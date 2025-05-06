import requests
from commons.logs import get_logger

logger = get_logger("chatbot_module")


class Chatbot:
    def __init__(self, context, **module_config):
        self.context = context
        self.config = module_config or {}

    def ask(self, provider=None, system_prompt=None, user_message=None,
            model=None, temperature=None, api_key=None):

        provider = (provider or self.config.get("provider", "")).lower()
        model = model or self.config.get("model")
        temperature = temperature if temperature is not None else self.config.get("temperature", 0.7)
        api_key = api_key or self.config.get("api_key")

        logger.info(f"[CHATBOT] Provider: {provider} | Model: {model}")
        if api_key:
            logger.info(f"[CHATBOT] Using API key starts with: {api_key[:10]}")
        else:
            logger.warning("[CHATBOT] No API key provided.")

        if not api_key and provider in ["openai", "anthropic", "mistral"]:
            return {
                "status": "fail",
                "message": f"Missing API key for provider '{provider}'",
                "data": None
            }

        try:
            if provider == "openai":
                return self._ask_openai(system_prompt, user_message, model or "gpt-4", temperature, api_key)
            elif provider == "anthropic":
                return self._ask_claude(system_prompt, user_message, model or "claude-3-opus-20240229", temperature, api_key)
            elif provider == "grok":
                return {
                    "status": "fail",
                    "message": "X/Twitter Grok API is not publicly available",
                    "data": None
                }
            elif provider == "mistral":
                return self._ask_mistral(system_prompt, user_message, model or "mistral-medium", temperature, api_key)
            else:
                return {
                    "status": "fail",
                    "message": f"Unsupported provider '{provider}'",
                    "data": None
                }
        except Exception as e:
            logger.error(f"[CHATBOT] Error during request: {e}")
            return {
                "status": "fail",
                "message": f"Exception occurred during Chatbot call: {str(e)}",
                "data": None
            }

    def _ask_openai(self, system_prompt, user_message, model, temperature, api_key):
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        }
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return {
            "status": "ok",
            "message": "OpenAI chat completed successfully",
            "data": {
                "reply": response.json()["choices"][0]["message"]["content"].strip()
            }
        }

    def _ask_claude(self, system_prompt, user_message, model, temperature, api_key):
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "temperature": temperature,
            "max_tokens": 1000,
            "messages": [
                {"role": "user", "content": f"{system_prompt}\n\n{user_message}"}
            ]
        }
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return {
            "status": "ok",
            "message": "Claude chat completed successfully",
            "data": {
                "reply": response.json()["content"][0]["text"].strip()
            }
        }

    def _ask_mistral(self, system_prompt, user_message, model, temperature, api_key):
        url = "https://api.mistral.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        }
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return {
            "status": "ok",
            "message": "Mistral chat completed successfully",
            "data": {
                "reply": response.json()["choices"][0]["message"]["content"].strip()
            }
        }
