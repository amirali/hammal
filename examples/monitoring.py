import json
import os
import random

from hammal import Hammal, RequestContext

MONITORING_API_KEY = os.getenv("MONITORING_API_KEY")

backend = {
    "db": {"cursor": lambda: random.random() < 0.5},
    "cache": {"ping": lambda: random.random() < 0.7},
}


def auth_middleware(context: RequestContext) -> bool:
    token = context.headers.get("Authorization")
    if not token == MONITORING_API_KEY:
        context.response.status = 401
        return False
    return True


def monitoring_handler(context: RequestContext) -> None:
    sanity_check = {
        "db": backend["db"]["cursor"](),
        "cache": backend["cache"]["ping"](),
    }

    if not all(sanity_check.values()):
        context.response.status = 500

    context.response.body = json.dumps(sanity_check)


router = Hammal()
router.use(auth_middleware)
router.get("/health", monitoring_handler)
router.start()
