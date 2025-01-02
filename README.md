# Hammal
[![PyPI - Version](https://img.shields.io/pypi/v/hammal?logo=pypi&logoColor=%23df8e1d&label=PyPI&color=%23df8e1d)](https://pypi.org/project/hammal/)

Hammal is a fast, minimalist Python web framework inspired by [Echo](https://github.com/labstack/echo). It is designed to be simple and easy to embed within other applications, providing the bare minimum router functionality.

## Installation

Install Hammal using pip:

```bash
pip install hammal
```

## Quick Start
Here's how you can get started with Hammal:

### Example: Hello World
```python
import json
from hammal import Hammal, RequestContext

def hello_handler(context: RequestContext) -> None:
    context.response.body = json.dumps({"message": "Hello, World!"})

router = Hammal()
router.get("/", hello_handler)
router.start()
```
Run the script and visit http://localhost:8000 in your browser to see "Hello, World!".

### Example: Handling Parameters
```python
def greet_handler(context: RequestContext) -> None:
    name = context.path_params.get("name", "Guest")
    context.response.body = json.dumps({"message": f"Hello, {name}!"})

router.get("/greet/:name", greet_handler)
```
Accessing http://localhost:8080/greet/Pikachu will return "Hello, Pikachu!".

### Example: Middleware
```python
import logging

def logging_middleware(context: RequestContext) -> bool:
    logging.info(f"{context.method} request for {context.path} with body: {context.body}")
    return True

def auth_middleware(context: RequestContext) -> bool:
    token = context.headers.get("Authorization")
    if not token == MONITORING_API_KEY:
        context.response.status = 401
        return False
    return True

router.use(logging_middleware)
router.use(auth_middleware)
```

### Example: Extensibility

Hammal is designed to be extensible, allowing you to integrate it into other applications seamlessly. Here's an example of extending Hammal:
```python
from hammal import Hammal

class BotWithHammal(Hammal):
    def __init__(self, bot, *args, **kwargs):
        self.bot = bot
        super().__init__(*args, **kwargs)

    def start_async(self, *args, **kwargs):
        super().start_async(*args, **kwargs)
        self.bot.polling(none_stop=True, timeout=60)

app = BotWithHammal(bot)
# add routes and middlewares
app.start_async()
```

### More Examples
The [examples](https://github.com/amirali/hammal/tree/main/examples) directory.

## Contributing

Contributions are welcome! Feel free to fork the project and submit a pull request.

## License

Hammal is open-source software licensed under the [MIT License](https://opensource.org/license/MIT).
