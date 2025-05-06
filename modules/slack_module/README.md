# 📘 Slack Module Documentation

---

## 🧩 Overview

The `slack_module` provides flexible, structured notifications to Slack channels. It supports both informational messages and incident-style alerts using Slack's webhook-based integration. This module is used as a **direct action step** — it is not a context module.

You can dynamically control:

- Which **channel** to post to
- The **webhook URL**, either globally or per workflow
- The structure of the message: plain, keyed fields, or form result flattening

---

## 🔧 Setup

### Slack Webhook Configuration Options

You can provide the Slack webhook URL in **three ways** (priority order):

1. **Step input** (`webhook_url`)
2. **Context variable** (`context.slack_webhook_url` or `context.webhook_url`)
3. **Static config** from `repos/modules/slack_module/config.yaml`

---

## 🛠️ Supported Actions

| Action                                      | Description |
|--------------------------------------------|-------------|
| `slack_module.Slack.send_info_message`     | Sends an informational Slack message (with optional formatting) |
| `slack_module.Slack.send_incident_message` | Sends a severity-based incident alert |

---

## 🧾 Full Syntax Reference

### `send_info_message`

```yaml
- id: slack_notify
  type: action
  action: slack_module.Slack.send_info_message
  input:
    channel: "#alerts"                  # Required
    title: "🚀 Deployment Complete"     # Required
    message: "Version 2.0 deployed"     # Optional (shown as 'Message' field)
    keyed_message:                      # Optional list of key-value pairs
      - key: "Service"
        value: "user-api"
      - key: "Deployed By"
        value: "{{ context.user }}"
    flatten_form_result: true          # Optional (default: false)
    color: "good"                      # Optional (default: 'info')
    webhook_url: "{{ context.slack_webhook_url }}"  # Optional override
```

#### `flatten_form_result: true`
When set, this flattens fields from `context.form_result.status.form_data` and adds them as individual fields in Slack.

---

### `send_incident_message`

```yaml
- id: alert_sev1
  type: action
  action: slack_module.Slack.send_incident_message
  input:
    channel: "#incident-response"
    message: "🔥 Service is down"
    severity: "sev1"         # Optional: sev1, sev2, sev3, warning, info, etc.
    oncall_user: "pagerduty-user"
    webhook_url: "{{ context.webhook_url }}"  # Optional override
```

---

## 🎨 Supported Colors

You can set the color in `color:` or `severity:` fields.

| Label     | Color      |
|-----------|------------|
| `sev1`    | 🔴 `#ff0000` |
| `sev2`    | 🟠 `#ffa500` |
| `info`    | 🔵 `#0000ff` |
| `good`    | 🟢 `#00ff00` |
| `warning` | 🟠 `#ffa500` |
| `neutral` | ⚪ `#cccccc` |
| `error`   | 🔴 `#ff0000` |
| `rejected`| 🔴 `#ff0000` |
| `approved`| 🟢 `#00ff00` |


# 📄 Full Workflow Reference: `slack_module`

```yaml
workflow:
  name: slack_module_full_test

  context_variables:
    - name: user
      default: "Yura"
    - name: channel
      default: "#gitops-alerts"
    - name: slack_webhook_url
      default: "https://hooks.slack.com/services/XXX/YYY/ZZZ"

  steps:

    # ✅ Simple Slack message with title and body
    - id: notify_simple
      type: action
      action: slack_module.Slack.send_info_message
      input:
        channel: "{{ context.channel }}"
        title: "🚀 Workflow Started"
        message: "This is a simple Slack message sent from SeyoAWE."

    # ✅ Keyed Slack fields
    - id: notify_keyed
      type: action
      action: slack_module.Slack.send_info_message
      input:
        channel: "{{ context.channel }}"
        title: "📦 Build Info"
        keyed_message:
          - key: "Environment"
            value: "Staging"
          - key: "Triggered By"
            value: "{{ context.user }}"
          - key: "Version"
            value: "v2.0.4"
        color: "info"

    # ✅ Flattened form data
    - id: flatten_form_result
      type: action
      action: slack_module.Slack.send_info_message
      input:
        channel: "{{ context.channel }}"
        title: "📝 Form Submission"
        flatten_form_result: true
        color: "good"

    # ✅ Slack message in approval flow (with approval link)
    - id: approval_step
      type: approval
      message: "Do you approve proceeding?"
      timeout_minutes: 60
      delivery_step:
        id: send_approval_notice
        type: action
        action: slack_module.Slack.send_info_message
        input:
          channel: "{{ context.channel }}"
          title: "🔔 Approval Needed"
          message: "Please approve using: <{{ context.approval_link }}|Click Here>"
          color: "warning"

    # ✅ Incident-style alert with severity and on-call
    - id: incident_alert
      type: action
      action: slack_module.Slack.send_incident_message
      input:
        channel: "#incident-response"
        message: "🔥 Service is down"
        severity: "sev1"
        oncall_user: "yuri@team.com"

    # ✅ Using context-defined webhook
    - id: notify_custom_hook
      type: action
      action: slack_module.Slack.send_info_message
      input:
        channel: "#custom-alerts"
        title: "📣 Custom Webhook Notification"
        message: "This message uses the webhook defined in context.slack_webhook_url"
        webhook_url: "{{ context.slack_webhook_url }}"
```

---


## 🧠 Behavior Summary

- Supports both `message` and `keyed_message` (or both together)
- `flatten_form_result: true` pulls fields from:
  ```python
  context.form_result.status.form_data
  ```
- Supports `webhook_url` as:
  - Step input
  - `context.slack_webhook_url` or `context.webhook_url`
  - Fallback to config in `slack_module/config.yaml`
- Fully compatible with delivery steps (e.g. for approval or webform links)

