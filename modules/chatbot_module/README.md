# 🤖 `chatbot_module` – Documentation

---

## 🧑 For Workflow Authors

### 🔍 What Is It?

The `chatbot_module` lets you **ask questions to an LLM (AI chatbot)** during a workflow.

It’s useful for:
- Summarizing user input from a form
- Auto-generating Slack messages or responses
- Translating or rephrasing content
- Making AI-based decisions mid-execution

---

### 📦 Basic Usage (DSL)

```yaml
- id: summarize_form
  type: action
  action: chatbot_module.Chatbot.ask
  input:
    provider: "openai"
    model: "gpt-4"
    system_prompt: >
      You are a helpful assistant that summarizes form input.
      Remove technical boilerplate, highlight only useful context.
    user_message: >
      Here's the user-submitted form:
      {{ context.form_result | tojson }}
    temperature: 0.6
    api_key: "{{ context.openai_key }}"
  register_output: chatbot_response
```

---

### 📥 Required Input Fields

| Field | Description |
|-------|-------------|
| `provider` | One of: `openai`, `anthropic`, `mistral` |
| `model` | Optional – e.g. `gpt-4`, `claude-3-opus`, `mistral-medium` |
| `system_prompt` | AI’s role definition (sets behavior) |
| `user_message` | Your actual message (user input) |
| `temperature` | Creativity control: `0.0` = conservative, `1.0` = imaginative |
| `api_key` | API key – usually passed from context (required for hosted models) |

---

### ✅ Example Use Case

After a form step:

```yaml
- id: ask_chatbot
  type: action
  action: chatbot_module.Chatbot.ask
  input:
    provider: "openai"
    system_prompt: >
      Summarize the following in plain language:
    user_message: >
      {{ context.form_result | tojson }}
    api_key: "{{ context.openai_key }}"
  register_output: chatbot_reply
```

Then you can use:

```yaml
- id: send_summary
  type: action
  action: slack_module.Slack.send_info_message
  input:
    channel: "#intake"
    title: "🤖 AI Summary"
    message: "{{ context.chatbot_reply.reply }}"
```

---

## 🧑‍💻 For Developers

---

### 🗂 Supported Providers

| Provider | Endpoint | Notes |
|----------|----------|-------|
| `openai` | `https://api.openai.com/v1/chat/completions` | Requires API key |
| `anthropic` | `https://api.anthropic.com/v1/messages` | Claude 3, requires API key |
| `mistral` | `https://api.mistral.ai/v1/chat/completions` | Hosted Mistral access |
| `grok` | Not supported yet | Placeholder |

---

### 🔐 API Key Handling

The module does **not** persist or hardcode API keys. Keys are passed via the workflow context and rendered using templating:

```yaml
api_key: "{{ context.openai_key }}"
```

The engine will inject the value at runtime.

---

### 🧪 Internal Call Flow

```python
def ask(self, provider, system_prompt, user_message, model, temperature, api_key)
```

Dispatches to one of:

- `_ask_openai(...)`
- `_ask_claude(...)`
- `_ask_mistral(...)`

Each uses standard `requests.post` with a JSON payload like:

```json
{
  "model": "gpt-4",
  "temperature": 0.7,
  "messages": [
    { "role": "system", "content": "..." },
    { "role": "user", "content": "..." }
  ]
}
```

Then parses response:

```json
{
  "status": "ok",
  "reply": "final text"
}
```

On error:

```json
{
  "status": "error",
  "error": "Invalid token or provider"
}
```

---

### 🧰 Logging + Safety

- Logs selected provider + model
- Catches all network errors and wraps them cleanly
