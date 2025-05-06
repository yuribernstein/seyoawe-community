# repos/modules/webform/webform.py

from commons.logs import get_logger
from commons.get_config import get_config

logger = get_logger("webform_module")
global_config = get_config()

class Webform:
    def __init__(self, context, **module_config):
        self.context = context
        self.config = module_config or {}

        logger.info(f"[WEBFORM] Initialized with config: {self.config}")
        logger.debug(f"[WEBFORM] Workflow UID: {self.context.get('workflow_uid')}")

    def approval_form(self):
        # This method just returns the static form route or metadata.
        # Actual approval happens in the engine upon form submission.
        return {
            "status": "waiting_for_input",
            "form_url": f"/webform/{self.context.get('workflow_uid')}"
        }
