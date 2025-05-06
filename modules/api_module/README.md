# 📘 API Module Documentation

---

## 🧩 Overview

The `api_module` allows SeyoAWE workflows to make outbound HTTP calls to third-party or internal APIs. It's fully declarative — you define method, URL, headers, body, query parameters, and optionally capture the result.

This module is perfect for:

- Triggering other systems (CI/CD, ticketing, SaaS)
- Validating inputs or conditions via API
- Fetching metadata to guide workflow logic

---

## 🔧 Setup

This module requires no special configuration. It’s used directly in `action` steps and does not need to be declared under `context_modules`.

---

## 🛠️ Supported Actions

| Action                          | Description |
|--------------------------------|-------------|
| `api_module.API.call`          | Sends an HTTP request with optional headers, body, params |

---

## 🔁 Input Fields

| Field         | Required | Description |
|---------------|----------|-------------|
| `method`      | ✅ Yes   | `"GET"`, `"POST"`, `"PUT"`, `"DELETE"`, etc. |
| `url`         | ✅ Yes   | Full URL or templated |
| `headers`     | No       | Dictionary of request headers |
| `params`      | No       | Dictionary of query string params |
| `body`        | No       | Dictionary or JSON-compatible object for body (for POST/PUT) |
| `timeout`     | No       | Timeout in seconds (default: 10) |

---

## 🔁 Response Behavior

- The response is parsed as JSON if possible
- The result is returned like this:
```json
{
  "status": 200,
  "headers": { ... },
  "body": { ... }  // or string if not JSON
}
```

---

# 📄 Full Workflow Reference: `api_module`

```yaml
workflow:
  name: api_module_full_test

  context_variables:
    - name: user
      default: "yura"
    - name: channel
      default: "#api-tests"
    - name: openai_key
      default: "sk-xxxx..."

  steps:

    # ✅ Basic GET request
    - id: get_example
      type: action
      action: api_module.API.call
      input:
        method: "GET"
        url: "https://httpbin.org/get"
        params:
          query: "{{ context.user }}"
      register_output: http_get_result

    # ✅ Slack notification with output
    - id: notify_get_result
      type: action
      action: slack_module.Slack.send_info_message
      input:
        channel: "{{ context.channel }}"
        title: "🔎 HTTP GET Result"
        keyed_message:
          - key: "Status Code"
            value: "{{ context.http_get_result.status }}"
          - key: "Query Echoed"
            value: "{{ context.http_get_result.body.args.query }}"
        color: "neutral"

    # ✅ POST request with JSON body and headers
    - id: post_example
      type: action
      action: api_module.API.call
      input:
        method: "POST"
        url: "https://httpbin.org/post"
        headers:
          Content-Type: "application/json"
          Authorization: "Bearer {{ context.openai_key }}"
        body:
          user: "{{ context.user }}"
          workflow: "{{ context.workflow.name }}"
      register_output: http_post_result

    # ✅ Slack output from POST response
    - id: notify_post_result
      type: action
      action: slack_module.Slack.send_info_message
      input:
        channel: "{{ context.channel }}"
        title: "📤 HTTP POST Sent"
        keyed_message:
          - key: "Posted User"
            value: "{{ context.http_post_result.body.json.user }}"
          - key: "Workflow"
            value: "{{ context.http_post_result.body.json.workflow }}"
```

---

## 🧠 Developer Notes

- Class: `API`
- Location: `repos/modules/api_module/api.py`
- Uses `requests` to send the HTTP call
- Automatically serializes `body` and parses JSON response (if available)
- Designed for testability and chaining with other workflow steps

---

## 🔥 Real-World Use Cases

- Triggering external Jenkins builds, GitHub workflows, or deployment APIs
- Sending updates to third-party APIs (e.g. creating tickets or Slack via webhooks)
- Validating conditions before executing sensitive steps (e.g. `GET /status`)
- Dynamic approval workflows — send to your own approval backend
