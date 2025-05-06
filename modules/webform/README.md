# 📝 `webform_module` – Documentation

---

## 🧑 For Workflow Authors

### 🔍 What Is It?

The `webform_module` lets you **pause your workflow for human input**. It renders a clean, dynamic React-based form based on a config file, collects user input, and then continues the workflow using the submitted values.

---

### 🛠 How to Use It

You define a `webform` step in your workflow YAML:

```yaml
- id: collect_details
  type: webform
  module: webform
  config_file: wf_config.js
  css_file: custom.css
  timeout_minutes: 60
  delivery_step:
    id: notify_ops
    type: action
    action: slack_module.Slack.send_info_message
    input:
      channel: "#ops"
      message: "Please complete the form: <{{ context.approval_link }}|Open Form>"
  register_output: form_result
```

> ✅ The form appears as a link and blocks further execution until submitted or timed out.

---

### 🔗 Link Behavior

- The form link is **generated dynamically**:
  ```
  http://localhost:8080/webform/<workflow_uid>/<step_id>/t.webform.html?config_file=wf_config.js
  ```
- It is valid **only until submitted** or until the `timeout_minutes` is reached.
- After submission, the link is destroyed via Flask’s route cleanup.
- This ensures **secure, one-time-use approval** via link.

---

### 🔄 Creating Form Flows

The logic is defined in a `.js` file (e.g. `wf_config.js`) inside `repos/modules/webform/configs`.

Each step looks like this:

```js
{
  id: "email",
  type: "input",
  label: "Email Address",
  iconName: "Website",
  nextStep: "confirm"
}
```

The `nextStep` field determines which step comes next.

The form **automatically handles Back navigation** based on history — no need to define it.

---

### 🧱 Available Step Types

| Type | Description |
|------|-------------|
| `input` | Single-line text input |
| `textbox` | Multiline input |
| `dropdown` | Static options |
| `multiinput` | Repeating input fields |
| `searchable-dropdown` | Search from remote API |
| `junction` | Branching buttons |
| `checkbox` | Yes/No branching |
| `api-trigger` | Sends API call and branches on result |
| `info` | Static text with a "Next" button |
| `submit` | Final step that triggers form submission |

---

### ✅ What Happens After Submit?

When a user submits:

1. Data is posted to:
   ```
   POST /webform/<workflow_uid>/<step_id>/submit
   ```

2. Workflow engine resumes execution.

3. Submitted values are available in:
   ```yaml
   context.form_result.status.form_data
   ```

You can use this in later steps like:

```yaml
- id: gate
  type: action
  action: slack_module.Slack.send_info_message
  input:
    message: "User selected: {{ context.form_result.status.form_data.environment }}"
```

You can also use conditions to **branch logic**:

```yaml
conditions:
  - path: context.form_result.status.form_data.approval
    operator: equals
    value: "yes"
```

---

### 🧾 Full Workflow DSL Example

```yaml
workflow:
  name: gather_user_info

  context_variables:
    - name: channel
      default: "#intake"

  steps:
    - id: send_form
      type: webform
      module: webform
      config_file: wf_config.js
      css_file: custom.css
      timeout_minutes: 60
      delivery_step:
        id: alert
        type: action
        action: slack_module.Slack.send_info_message
        input:
          channel: "{{ context.channel }}"
          message: "Please fill out the form: <{{ context.approval_link }}|Open Form>"
      register_output: form_result

    - id: conditional_step
      type: action
      action: slack_module.Slack.send_info_message
      conditions:
        conditions:
          - path: context.form_result.status.form_data.need_ticket
            operator: equals
            value: "yes"
        condition_logic: always
      input:
        message: "A ticket is required."

    - id: finalize
      type: action
      action: slack_module.Slack.send_info_message
      input:
        message: "Thanks {{ context.form_result.status.form_data.name }} for your submission."
```

---

## 🧑‍💻 For Developers

---

### 📦 Folder Structure

```
webform/
├── build/            # Build system for frontend
├── configs/          # Declarative JS config for form flows
├── assets/           # Static icons
├── styles/           # CSS overrides
├── t.webform.html    # HTML template (injected with JS bundle)
├── webform.py        # Optional: module logic (currently unused)
```

---

### 🏗 Building the Form

1. Install dependencies:

```bash
cd repos/modules/webform
./setup.sh
```

2. Build the frontend:

```bash
./build/build_module.sh
```

This generates:
```
build/dist/
├── bundle.js         ✅ Webform renderer
├── configs/          ✅ JS configs copied over
├── icons/            ✅ Static icons
├── custom.css        ✅ CSS
```

---

### 🧬 Runtime Integration

- The URL:
  ```
  /webform/<uid>/<step_id>/t.webform.html?config_file=configs/your_config.js
  ```
  loads a React app that:
  - Parses the config file
  - Walks through steps
  - Posts data on submit to:
    ```
    POST /webform/<uid>/<step_id>/submit
    ```

- Flask handles it in `app.py`:
  ```python
  @app.route("/<module>/<uid>/<step_id>/submit", methods=["POST"])
  def handle_module_submit(...)
  ```

- The workflow engine is paused via `approval_manager.wait_for_approval(...)` and unblocked once data is received.

---

### 🔒 Security Notes

- Links are time-bound and one-time-use.
- The route is deregistered from the Flask app after:
  - Timeout
  - Submission
- Users cannot spoof or reuse previous links to affect new workflows.

---

### 💡 Advanced Usage

- Form logic can contain dynamic logic via `junction`, `api-trigger`, and `conditional paths`
- You can pull dynamic data via API using `searchable-dropdown`
- Form steps are composable and extensible — consider building reusable fragments
