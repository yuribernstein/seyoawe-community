# 📘 Email Module Documentation

---

## 🧩 Overview

The `email_module` sends email notifications and approvals as part of a SeyoAWE workflow. It supports **HTML and plaintext** emails using Jinja2 templates and allows full control over recipients, subject lines, and message content.

Emails can be triggered as regular steps, used in approval flows (`delivery_step`), or chained into workflows alongside Slack messages, GitOps actions, or chatbot summaries.

---

## 🔧 Setup

### Configuration Options

The module requires SMTP credentials defined in `repos/modules/email_module/config.yaml`, for example:

```yaml
smtp_host: smtp.gmail.com
smtp_port: 587
smtp_user: yuri.bernstein@gmail.com
smtp_pass: your_app_password_here
from_addr: SeyoAWE Bot <yuri.bernstein@gmail.com>
```

Optionally, the `from_addr`, `smtp_host`, and others can be overridden from context variables (`context.smtp_host`, etc.).

---

## 🛠️ Supported Actions

| Action                               | Description |
|-------------------------------------|-------------|
| `email_module.Email.send_email`     | Sends an email using a Jinja2 `.j2` template or plaintext body |

---

## 🧾 Full Syntax Reference

### `send_email`

```yaml
- id: email_notification
  type: action
  action: email_module.Email.send_email
  input:
    to: "recipient@example.com"               # Required (comma-separated or list)
    subject: "Form Submitted"                # Required
    template: "form_confirmation.html.j2"    # Optional (HTML or plaintext, located in email_module/templates)
    body: "Thank you for your submission."   # Optional fallback if no template
    context_vars:                            # Optional — overrides or additional context
      username: "{{ context.user }}"
      approval: "{{ context.form_result.status.form_data.approval }}"
```

---

## ✨ Features

- Supports **HTML and plaintext** using `.j2` Jinja2 templates
- Full access to the current workflow context
- Context can be **augmented or overridden** via `context_vars`
- Can be used in `delivery_step` blocks for approval or webform actions

---

## 📂 Template Location

Templates must be placed in:

```
repos/modules/email_module/templates/
```

Example:

```bash
repos/modules/email_module/templates/form_confirmation.html.j2
```

---

## 🧠 Developer Notes

- Class: `Email`
- Location: `repos/modules/email_module/email.py`
- Uses `smtplib.SMTP()` for sending
- On init, the module loads SMTP config from:
  - `context` first (e.g., `context.smtp_user`)
  - Then falls back to `config.yaml`

### Templating

- Uses Jinja2 to render `template.j2`
- Context is injected from workflow + optional `context_vars`
- Example render:

```python
template.render(context=ctx)
```


# 📄 Full Workflow Reference: `email_module`

```yaml
workflow:
  name: email_module_full_test

  context_variables:
    - name: smtp_user
      default: "yuri.bernstein@gmail.com"
    - name: smtp_pass
      default: "app-password-here"
    - name: smtp_host
      default: "smtp.gmail.com"
    - name: smtp_port
      default: 587
    - name: from_addr
      default: "SeyoAWE Bot <yuri.bernstein@gmail.com>"
    - name: user
      default: "Yura"
    - name: user_email
      default: "user@example.com"

  steps:

    # ✅ Simple Info Email using template
    - id: send_info_email
      type: action
      action: email_module.Email.send_email
      input:
        to: "{{ context.user_email }}"
        subject: "✅ Workflow Completed"
        template: "confirmation_template.html.j2"
        context_vars:
          username: "{{ context.user }}"
          time: "{{ context.workflow_started_at }}"

    # ✅ Email with plain body (no template)
    - id: send_plaintext_email
      type: action
      action: email_module.Email.send_email
      input:
        to: "{{ context.user_email }}"
        subject: "👋 Hello"
        body: >
          Hi {{ context.user }},
          
          This is a plaintext email sent without a template.
          Regards,
          SeyoAWE

    # ✅ Approval Email via delivery_step
    - id: approval_email
      type: approval
      message: "Do you approve this workflow to continue?"
      timeout_minutes: 60
      delivery_step:
        id: send_email_with_link
        type: action
        action: email_module.Email.send_email
        input:
          to: "{{ context.user_email }}"
          subject: "🚨 Approval Required"
          template: "approval_link.html.j2"
          context_vars:
            username: "{{ context.user }}"
            link: "{{ context.approval_link }}"

    # ✅ Email summarizing a form submission
    - id: send_form_summary_email
      type: action
      action: email_module.Email.send_email
      input:
        to: "{{ context.user_email }}"
        subject: "📬 Form Submitted"
        template: "form_summary.html.j2"
        context_vars:
          username: "{{ context.user }}"
          data: "{{ context.form_result.status.form_data | tojson }}"
```

---

## 🧠 Template File Examples

### 📄 `confirmation_template.html.j2`
```html
<h2>🎉 Hello {{ username }}</h2>
<p>Your workflow finished at {{ time }}.</p>
<p>Thank you!</p>
```

---

### 📄 `approval_link.html.j2`
```html
<h2>Action Required</h2>
<p>Hello {{ username }},</p>
<p>Please review and approve the workflow using this link:</p>
<p><a href="{{ link }}">Click to Approve</a></p>
```

---

### 📄 `form_summary.html.j2`
```html
<h3>Form Submission Summary for {{ username }}</h3>
<pre>{{ data }}</pre>
```

---

This gives you full flexibility:

- Works with any email service that supports SMTP (via config or overrides)
- Great for audits, alerts, approvals, or internal tools
- Works with Slack in parallel for hybrid comms
