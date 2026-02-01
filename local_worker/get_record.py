import os
import json
import urllib.request
from urllib.error import URLError, HTTPError

# API Configuration
API_BASE_URL = os.environ.get("MANAGER_BASE_URL", "http://192.168.1.110:31500")  # Get from container env var
GET_TASK_ENDPOINT = f"{API_BASE_URL}/api/queue/largest"


def get_largest_task():
    request = urllib.request.Request(GET_TASK_ENDPOINT, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            status_code = response.getcode()
            body = response.read().decode("utf-8")
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                data = body
            return status_code, data
    except HTTPError as exc:
        return exc.code, exc.read().decode("utf-8")
    except URLError as exc:
        return None, f"Connection error: {exc}"