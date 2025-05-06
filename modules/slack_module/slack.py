import requests
import ast
import json
from commons.logs import get_logger

logger = get_logger("slack_module")


class Slack:
    def __init__(self, context, **module_config):
        self.context = context
        self.config = module_config or {}
        logger.info(f"[SLACK] Initialized with config: {self.config}")

    def send_info_message(self, channel, title, message=None, keyed_message=None, flatten_form_result=False, color="info", webhook_url=None):
        webhook_url = (
            webhook_url or
            self.context.get("slack_webhook_url") or
            self.context.get("webhook_url") or
            self.config.get("webhook_url")
        )
        logger.info(f"[SLACK] Webhook URL: {webhook_url}")

        if not webhook_url:
            logger.error("[SLACK] Missing webhook URL")
            return {"status": "fail", "message": "Missing webhook URL", "data": None}

        fields = []

        if message:
            fields.append({
                "title": "Message",
                "value": str(message),
                "short": False
            })

        if isinstance(keyed_message, list):
            for raw_item in keyed_message:
                if isinstance(raw_item, dict):
                    key = raw_item.get("key")
                    value = raw_item.get("value")
                elif isinstance(raw_item, str):
                    try:
                        parsed = ast.literal_eval(raw_item)
                        key = parsed.get("key")
                        value = parsed.get("value")
                    except Exception as e:
                        logger.warning(f"[SLACK] Could not parse keyed_message item: {raw_item} → {e}")
                        continue
                else:
                    continue

                if key and value is not None:
                    fields.append({
                        "title": str(key),
                        "value": str(value),
                        "short": True
                    })

        if flatten_form_result:
            form_data = self.context.get("form_result", {}).get("status", {}).get("form_data", {})
            if isinstance(form_data, dict):
                for k, v in form_data.items():
                    fields.append({
                        "title": k.replace("_", " ").title(),
                        "value": str(v),
                        "short": True
                    })

        payload = {
            "channel": channel,
            "text": title,
            "attachments": [
                {
                    "color": self._get_color(color),
                    "fields": fields,
                }
            ]
        }

        try:
            response = requests.post(webhook_url, json=payload)
            response.raise_for_status()
            logger.info(f"[SLACK] Info message sent to {channel}")
            return {"status": "ok", "message": f"Message sent to {channel}", "data": {"channel": channel}}
        except Exception as e:
            logger.error(f"[SLACK] Failed to send info message: {e}")
            return {"status": "fail", "message": str(e), "data": None}

    def send_incident_message(self, channel, message, severity=None, oncall_user=None):
        webhook_url = (
            self.context.get("slack_webhook_url") or
            self.context.get("webhook_url") or
            self.config.get("webhook_url")
        )
        logger.info(f"[SLACK] Webhook URL for incident: {webhook_url}")

        if not webhook_url:
            logger.error("[SLACK] Missing webhook URL for incident")
            return {"status": "fail", "message": "Missing webhook URL", "data": None}

        payload = {
            "channel": channel,
            "text": message,
            "attachments": [
                {
                    "color": self._get_color(severity),
                    "fields": [
                        {"title": "Severity", "value": severity or "N/A", "short": True},
                        {"title": "On-call", "value": oncall_user or "N/A", "short": True},
                    ],
                }
            ],
        }

        try:
            response = requests.post(webhook_url, json=payload)
            response.raise_for_status()
            logger.info(f"[SLACK] Incident message sent to {channel}")
            return {"status": "ok", "message": f"Incident sent to {channel}", "data": {"channel": channel}}
        except Exception as e:
            logger.error(f"[SLACK] Failed to send incident message: {e}")
            return {"status": "fail", "message": str(e), "data": None}

    def _get_color(self, severity):
        return {
            "sev1": "#ff0000",
            "sev2": "#ffa500",
            "sev3": "#ffff00",
            "none": "#00ff00",
            "info": "#0000ff",
            "approved": "#00ff00",
            "rejected": "#ff0000",
            "pending": "#ffff00",
            "error": "#ff0000",
            "warning": "#ffa500",
            "good": "#00ff00",
            "bad": "#ff0000",
            "neutral": "#cccccc",
        }.get(str(severity).lower(), "#cccccc")
