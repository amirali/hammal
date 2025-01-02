import json

from hammal import Hammal, RequestContext


def logging_middleware(context: RequestContext) -> bool:
    print(f"{context.method} request for {context.path} with body: {context.body}")
    return True


def hello_handler(context: RequestContext) -> None:
    context.response.body = json.dumps({"message": "Hello, World!"})


def greet_handler(context: RequestContext) -> None:
    name = context.path_params.get("name", "Guest")
    context.response.body = json.dumps({"message": f"Hello, {name}!"})


def echo_handler(context: RequestContext) -> None:
    context.response.body = json.dumps({"received": context.body})


router = Hammal()
router.use(logging_middleware)
router.add("GET", "/", hello_handler)
router.get("/greet/:name", greet_handler)
router.add("POST", "/echo", echo_handler)

router.start()
