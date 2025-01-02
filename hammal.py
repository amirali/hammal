import json
import socket
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, Tuple
from urllib.parse import parse_qs

RequestContext = Dict[str, Any]
Middleware = Callable[[RequestContext], bool]
RouteHandler = Callable[[RequestContext], None]

Headers = Dict[str, str]
Body = Optional[str]


@dataclass
class ResponseContext:
    status: int = 200
    headers: Headers = field(default_factory=dict)
    body: Body = None


@dataclass
class RequestContext:
    method: str
    path: str
    headers: Headers = field(default_factory=dict)
    body: Body = None
    path_params: Optional[Dict[str, str]] = None
    response: ResponseContext = field(default_factory=ResponseContext)


http_status_codes = {
    # 1xx Informational
    100: "Continue",
    101: "Switching Protocols",
    102: "Processing (WebDAV)",
    103: "Early Hints",
    # 2xx Success
    200: "OK",
    201: "Created",
    202: "Accepted",
    203: "Non-Authoritative Information",
    204: "No Content",
    205: "Reset Content",
    206: "Partial Content",
    207: "Multi-Status (WebDAV)",
    208: "Already Reported (WebDAV)",
    226: "IM Used (HTTP Delta encoding)",
    # 3xx Redirection
    300: "Multiple Choices",
    301: "Moved Permanently",
    302: "Found",
    303: "See Other",
    304: "Not Modified",
    305: "Use Proxy",
    306: "Switch Proxy (No Longer Used)",
    307: "Temporary Redirect",
    308: "Permanent Redirect",
    # 4xx Client Errors
    400: "Bad Request",
    401: "Unauthorized",
    402: "Payment Required",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    406: "Not Acceptable",
    407: "Proxy Authentication Required",
    408: "Request Timeout",
    409: "Conflict",
    410: "Gone",
    411: "Length Required",
    412: "Precondition Failed",
    413: "Payload Too Large",
    414: "URI Too Long",
    415: "Unsupported Media Type",
    416: "Range Not Satisfiable",
    417: "Expectation Failed",
    418: "I'm a Teapot",
    421: "Misdirected Request",
    422: "Unprocessable Entity (WebDAV)",
    423: "Locked (WebDAV)",
    424: "Failed Dependency (WebDAV)",
    425: "Too Early",
    426: "Upgrade Required",
    428: "Precondition Required",
    429: "Too Many Requests",
    431: "Request Header Fields Too Large",
    451: "Unavailable For Legal Reasons",
    # 5xx Server Errors
    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
    505: "HTTP Version Not Supported",
    506: "Variant Also Negotiates",
    507: "Insufficient Storage (WebDAV)",
    508: "Loop Detected (WebDAV)",
    510: "Not Extended",
    511: "Network Authentication Required",
}


class Hammal(object):
    def __init__(self, host: str = "127.0.0.1", port: int = 8000) -> "Hammal":
        self.host = host
        self.port = port
        self.routes: Dict[str, Dict[str, RouteHandler]] = {}
        self.middlewares: list[Middleware] = []
        self.thread: Optional[threading.Thread] = None
        self.thread_stop_event: Optional[threading.Event] = None

    def add(self, method: str, path: str, handler: RouteHandler) -> None:
        method = method.upper()
        if method not in self.routes:
            self.routes[method] = {}
        self.routes[method][path] = handler

    def get(self, path: str, handler: RouteHandler) -> None:
        self.add("get", path, handler)

    def post(self, path: str, handler: RouteHandler) -> None:
        self.add("post", path, handler)

    def put(self, path: str, handler: RouteHandler) -> None:
        self.add("put", path, handler)

    def patch(self, path: str, handler: RouteHandler) -> None:
        self.add("patch", path, handler)

    def delete(self, path: str, handler: RouteHandler) -> None:
        self.add("delete", path, handler)

    def use(self, middleware: Middleware) -> None:
        self.middlewares.append(middleware)

    def match_route(
        self, method: str, path: str
    ) -> Tuple[Optional[str], Dict[str, str]]:
        for route_template in self.routes.get(method, {}):
            route_parts = route_template.strip("/").split("/")
            path_parts = path.strip("/").split("/")
            if len(path_parts) != len(route_parts):
                continue

            path_params: Dict[str, str] = {}
            matched = True
            for route_part, path_part in zip(route_parts, path_parts):
                if route_part.startswith(":"):
                    param_name = route_part[1:]
                    path_params[param_name] = path_part
                elif route_part != path_part:
                    matched = False
                    break

            if matched:
                return route_template, path_params

        return None, {}

    @staticmethod
    def parse_request(request_data: str) -> Tuple[str, str, Headers, Body]:
        lines = request_data.split("\r\n")
        request_line = lines[0]
        method, path, _ = request_line.split(" ")
        headers: Headers = {}

        i = 1
        while i < len(lines) and lines[i]:
            key, value = lines[i].split(":", 1)
            headers[key.strip()] = value.strip()
            i += 1

        body = "\r\n".join(lines[i + 1 :]) if i + 1 < len(lines) else ""
        return method, path, headers, body

    @staticmethod
    def build_response(response: ResponseContext) -> bytes:
        status: int = response.status
        body: str = response.body
        headers: Headers = response.headers
        reason: str = http_status_codes.get(status, "Internal Server Error")

        if not headers.get("Content-Type".lower()):
            headers["Content-Type"] = "application/json"

        response_text = f"HTTP/1.1 {status} {reason}\r\n"
        for header_name, header_value in headers.items():
            response_text += f"{header_name}: {header_value}\r\n"
        response_text += f"Content-Length: {len(body)}\r\n\r\n"
        response_text += body
        return response_text.encode("utf-8")

    def handle_request(self, request_data: str) -> bytes:
        method, path, headers, body = self.parse_request(request_data)

        path_template, path_params = self.match_route(method, path)
        context: RequestContext = RequestContext(
            method, path, headers, body, path_params
        )

        for middleware in self.middlewares:
            if not middleware(context):
                return self.build_response(context.response)

        if path_template:
            handler = self.routes[method][path_template]
            handler(context)
        else:
            context.response.status = 404
            context.response.body = json.dumps({"error": "Not Found"})

        return self.build_response(context.response)

    def start(self, host: str = None, port: int = None) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((host or self.host, port or self.port))
            server_socket.listen(5)

            loop_condition = lambda: (
                not self.thread_stop_event.is_set()
                if self.thread_stop_event
                else lambda: True
            )
            while loop_condition():
                client_socket, client_address = server_socket.accept()
                with client_socket:
                    request_data = client_socket.recv(1024).decode("utf-8")
                    if not request_data:
                        continue

                    response = self.handle_request(request_data)
                    client_socket.sendall(response)

    def start_async(self, host: str = None, port: int = None) -> None:
        self.thread = threading.Thread(target=(self.start), args=(host, port))
        self.thread_stop_event = threading.Event()
        self.thread.start()

    def stop_async(self):
        # FIXME: Fix the last request call to end the process
        # while loop_condition():
        #    client_socket, client_address = server_socket.accept() <-----
        #    with client_socket:
        self.thread_stop_event.set()
        self.thread.join()
