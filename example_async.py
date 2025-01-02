import json
import time

from hammal import Hammal, RequestContext


def status_handler(context: RequestContext) -> None:
    context.response.body = json.dumps({"message": "Server is still running"})


router = Hammal()
router.get("/", status_handler)

router.start_async()

for i in range(6):
    print(f"timestamp={time.time()}: Server is still running")
    time.sleep(10)

router.stop_async()
