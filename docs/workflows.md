# 📘 SeyoAWE Workflow DSL Guide

SeyoAWE workflows are written in **pure YAML** and define how automation tasks are triggered, executed, paused, and resumed — with full support for GitOps, human-in-the-loop approvals, and dynamic context handling.

This guide covers:

- All supported DSL keys
- Triggers, steps, context, and modules
- Examples of each concept
- Best practices and usage patterns

---

## 📂 Workflow File Structure

A typical workflow YAML looks like:

```yaml
  workflow:
    name: provision_environment

    trigger:
      type: api

    context_variables:
      github_token: "{{ secrets.gh_token }}"
      user: "{{ payload.user }}"

    context_modules:
      git:
        module: git_module.Git
        repo: "https://github.com/org/repo.git"
        branch: "feature/{{ context.user }}"

    steps:
    - id: create_file
        type: action
        action: context.git.add_file_from_template
        input:
          template: "main.tf.j2"
          destination: "envs/{{ context.user }}/main.tf"

    - id: approve_merge
        type: approval
        message: "Merge new infra for {{ context.user }}?"
        timeout_minutes: 60
        delivery_step:
          id: notify
          type: action
          action: slack_module.Slack.send_info_message
          input:
            channel: "#infra"
            message: "PR is ready. Approve to continue."

    - id: merge
        type: action
        action: context.git.merge_pr
````

---

## 🧩 Top-Level Keys

| Key                      | Description                                |
| ------------------------ | ------------------------------------------ |
| `name`                   | The workflow's name (required)             |
| `trigger`                | How the workflow is started                |
| `context_variables`      | Variables shared across all steps          |
| `context_modules`        | Modules initialized at the start, reusable |
| `global_failure_handler` | Optional handler for any uncaught failure  |
| `steps`                  | List of sequential or conditional steps    |

---

## ⏰ `trigger`

Determines how and when the workflow is activated.

### Types

| Type        | Description                                                   |
| ----------- | ------------------------------------------------------------- |
| `api`       | Triggered by HTTP POST to `POST /api/trigger/<workflow_name>` |
| `git`       | Triggered by repo changes (polling or webhook)                |
| `scheduled` | Cron-based execution (e.g., `"*/10 * * * *"`)                 |
| `ad-hoc`    | Manual trigger via CLI (`sawectl run`) or UI                  |

### Example

```yaml
trigger:
  type: api
  parsers:
    user: payload.user
  conditions:
    - key: payload.action
      equals: "provision"
```

> ✅ Use `parsers` to extract payload values into context variables.
> ✅ Use `conditions` to control which payloads start the workflow.

---

## 🔑 `context_variables`

Define variables accessible throughout the workflow.

```yaml
context_variables:
  user: "{{ payload.user }}"
  github_token: "{{ secrets.gh_token }}"
```

* Variables support Jinja2 templating
* Used in `input`, `context_modules`, steps, and templates
* Can be overridden by modules

---

## 🧠 `context_modules`

Persistent modules initialized once, then reused across steps.

```yaml
context_modules:
  git:
    module: git_module.Git
    repo: "https://github.com/org/repo.git"
    branch: "feature/{{ context.user }}"
```

> You call them in steps like `context.git.create_branch`.

---

## 🪜 `steps`

The main execution pipeline.
Each step has:

| Key               | Description                                     |
| ----------------- | ----------------------------------------------- |
| `id`              | Unique identifier                               |
| `type`            | Step type (`action`, `approval`, `conditional`) |
| `action`          | Method to call (for `action` steps)             |
| `input`           | Dict of input parameters passed to the method   |
| `approval`        | Boolean (for inline approvals)                  |
| `delivery_step`   | Step to run before approval waits               |
| `register_output` | Save output of step into context                |
| `on_failure`      | Optional failure handler for this step          |

---

## 🧾 Action Step

```yaml
- id: send_welcome
  type: action
  action: slack_module.Slack.send_info_message
  input:
    channel: "#general"
    message: "Hello {{ context.user }}!"
```

---

## ✅ Approval Step

```yaml
- id: approve
  type: approval
  message: "Do you approve environment creation for {{ context.user }}?"
  timeout_minutes: 45
  delivery_step:
    id: notify
    type: action
    action: slack_module.Slack.send_info_message
    input:
      channel: "#ops"
      message: "Approval required: {{ context.approval_link }}"
```

You can also mark a **regular action step** with `approval: true`.

```yaml
- id: deploy
  type: action
  action: api_module.Api.call_endpoint
  approval: true
  delivery_step:
    ...
```

---

## 🧮 Conditional Step

```yaml
- id: check_status
  type: conditional
  condition:
    key: context.repo_status.is_dirty
    equals: false
  if_true:
    - id: notify_clean
      type: action
      action: slack_module.Slack.send_info_message
      input:
        channel: "#ops"
        message: "Repo is clean."
  if_false:
    - id: notify_dirty
      type: action
      action: slack_module.Slack.send_warning_message
      input:
        channel: "#ops"
        message: "Uncommitted changes exist!"
```

---

## 💥 Failure Handling

Each step may define:

```yaml
on_failure:
  id: notify_failure
  type: action
  action: slack_module.Slack.send_error_message
  input:
    channel: "#alerts"
    message: "Step {{ step.id }} failed"
```

Or you can set a global fallback:

```yaml
global_failure_handler:
  id: notify_global
  type: action
  action: email_module.Email.notify_admins
  input:
    subject: "Workflow failed"
    recipients: ["ops@example.com"]
```

---

## 📤 Output Capture

```yaml
- id: get_status
  type: action
  action: context.git.get_status
  register_output: repo_status

# Later use:
value: "{{ context.repo_status.is_dirty }}"
```

---

## 🧪 Workflow Example — Full

```yaml
workflow:
    name: terraform_workflow

    trigger:
      type: ad-hoc

    context_variables:
      github_token: "{{ secrets.github }}"
      user: "alice"

    context_modules:
      git:
        module: git_module.Git
        repo: "https://github.com/org/infrastructure.git"
        branch: "tf/{{ context.user }}"

    steps:
    - id: render_tf
        type: action
        action: context.git.add_file_from_template
        input:
          template: "terraform.tf.j2"
          destination: "envs/{{ context.user }}/main.tf"
          variables:
            region: "us-west-2"

    - id: pr
        type: action
        action: context.git.open_pr
        input:
          title: "Provision TF for {{ context.user }}"
          body: "Auto-generated from workflow"

    - id: approve
        type: approval
        message: "Approve Terraform changes for {{ context.user }}?"
        timeout_minutes: 60
        delivery_step:
        id: announce
        type: action
        action: slack_module.Slack.send_info_message
          input:
            channel: "#infra"
            message: "Approve here: {{ context.approval_link }}"

    - id: merge
        type: action
        action: context.git.merge_pr
```

---

## 🔄 Triggers Recap

| Type        | Payload | Parsers | Conditions | Notes                        |
| ----------- | ------- | ------- | ---------- | ---------------------------- |
| `api`       | ✅      | ✅      | ✅         | Ideal for webhooks, GitHub   |
| `git`       | ❌      | N/A     | ✅         | Polls files or waits webhook |
| `scheduled` | ❌      | N/A     | ✅         | Use cron expressions         |
| `ad-hoc`    | ❌      | N/A     | N/A        | Triggered manually           |

---

## 🧠 Context Summary

Context is the **shared memory** of the workflow:

* Accessible via `{{ context.* }}`
* Modified via `register_output`, module returns, or explicit updates
* Used in template rendering, input generation, and conditional logic

You can inspect it via:

```yaml
- id: dump
  type: action
  action: slack_module.Slack.send_info_message
  input:
    message: "{{ context | tojson }}"
```

---

## ✅ Best Practices

| Practice                         | Why it matters                                 |
| -------------------------------- | ---------------------------------------------- |
| Use `id` for every step          | Enables reuse, debugging, and context tracking |
| Prefer `context_modules`         | For Git, API, DB actions shared across steps   |
| Use `register_output`            | For storing values for future steps            |
| Use `approval` + `delivery_step` | Combines automation and human decision-making  |
| Store secrets in config          | Don't hardcode tokens in YAMLs                 |

---

## 🛠 Tools

```bash
sawectl workflow init my_workflow
sawectl validate-workflow workflows/my_workflow.yaml
sawectl run workflows/my_workflow.yaml
```

---

## 📬 Need Help?

* Ask questions: [yuri.bernstein@gmail.com](mailto:yuri.bernstein@gmail.com)
* Coming soon: [https://seyoawe.dev/docs](https://seyoawe.dev/docs)
* Community modules: [GitHub → modules-community](https://github.com/yuribernstein/seyoawe-community)

---
