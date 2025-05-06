import requests
import time
from datetime import datetime, timedelta
from commons.logs import get_logger
from engine.utils.match_engine import extract_json_path, evaluate_operator

logger = get_logger("api_module")

class API:
    def __init__(self, context, **module_config):
        self.context = context
        self.config = module_config or {}

    def call(self, method, url, headers=None, params=None, json=None, data=None, timeout=None):
        timeout = timeout or self.config.get("timeout", 10)
        headers = headers or self.config.get("headers")

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json,
                data=data,
                timeout=timeout
            )
            if 200 <= response.status_code < 300:
                logger.info(f"[API] Request to {url} succeeded with status {response.status_code}")
                return {
                    "status": "ok",
                    "message": f"Request to {url} succeeded with status {response.status_code}",
                    "data": {
                        "status_code": response.status_code,
                        "body": response.text,
                        "url": response.url,
                    }
                }
            else:
                logger.error(f"[API] Request to {url} failed: Status {response.status_code}, Body: {response.text}")
                return {
                    "status": "fail",
                    "message": f"Request to {url} failed with status {response.status_code}",
                    "data": {
                        "status_code": response.status_code,
                        "body": response.text,
                        "url": response.url,
                    }
                }
        except Exception as e:
            logger.error(f"[API] Exception during API call: {e}")
            return {
                "status": "fail",
                "message": f"Exception occurred during API call: {e}",
                "data": None
            }

    def blocking_call(self, method, url, headers=None, params=None, body=None,
                      poll_interval_seconds=None, timeout_minutes=None,
                      polling_mode="status_code", expected_status_code=200, success_condition=None):
        
        poll_interval_seconds = poll_interval_seconds or self.config.get("poll_interval_seconds", 10)
        timeout_minutes = timeout_minutes or self.config.get("timeout_minutes", 5)
        headers = headers or self.config.get("headers")

        deadline = datetime.utcnow() + timedelta(minutes=timeout_minutes)

        while datetime.utcnow() < deadline:
            try:
                response = requests.request(method, url, headers=headers, params=params, json=body)

                if polling_mode == "status_code":
                    if response.status_code == expected_status_code:
                        return {"status": "success", "response": response.json() if response.content else {}}
                elif polling_mode == "response_body" and success_condition:
                    data = response.json()
                    actual_value = extract_json_path(data, success_condition["path"])
                    if evaluate_operator(success_condition["operator"], actual_value, success_condition["value"]):
                        return {"status": "success", "response": data}
            except Exception as e:
                logger.error(f"[API] Error during blocking call: {e}")

            time.sleep(poll_interval_seconds)

        return {"status": "timeout", "reason": f"Polling timed out after {timeout_minutes} minutes"}
