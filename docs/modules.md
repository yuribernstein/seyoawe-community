# 🧩 SeyoAWE Modules — Developer Guide

Modules are the core building blocks of **SeyoAWE workflows**.  
Each module encapsulates automation logic — from making an API call to managing Git, sending Slack messages, or collecting human input.

---

## 📦 What Is a Module?

A **module** is a Python class with callable methods, accompanied by:

- A `module.yaml` manifest  
- An optional `usage_reference.yaml` with real examples

These are auto-loaded by both the engine and the CLI (`sawectl`), making modules self-documenting and discoverable.

---

## 🔧 Module Anatomy

Each module has:

```bash
configuration/
  config.yaml               # global configuration file
    ...
        modules:
            your_module:
                settings:   # Optional: your module external configurations
modules/
  your_module/
    module.yaml             # Required: describes the module to the engine
    usage_reference.yaml    # Optional: input examples per method
    your_module.py          # Required: contains the logic class
    templates/              # Optional: Jinja2 templates used by the module

````

---

## 🧠 Key Concepts

### 🔹 Module Class

Your main class can have **multiple public methods** (not just `execute`):

```python
class MyModule:
    def say_hello(self, name):
        return {
            "status": "ok",
            "message": f"Hello, {name}!"
        }

    def add(self, a, b):
        return {
            "status": "ok",
            "result": a + b
        }
```

The class is instantiated **once per workflow run** (or per step if not used as a context module).

---

### 🔹 `module.yaml` Manifest

```yaml
name: git_module
class: Git
version: 1.0
author: Yura Bernstein

methods:
  - name: create_branch
    description: Creates a new Git branch locally.
    arguments: []

  - name: add_file_from_template
    description: Renders a Jinja2 template and commits it.
    arguments:
      - name: template
        type: string
        required: true
      - name: destination
        type: string
        required: true
      - name: variables
        type: dict
        required: false
      - name: commit_message
        type: string
        required: false
        default: "Add generated file"
```

This manifest is parsed by the engine and `sawectl`, enabling:

* Input validation
* Method discovery
* CLI autocompletion
* UI hints

---

### 🔹 `usage_reference.yaml` (Optional)

Provides per-method usage samples and helps the CLI/UI generate code snippets.

```yaml
method: add_file_from_template
example_input:
  template: "main.tf.j2"
  destination: "envs/dev/main.tf"
  variables:
    region: "us-west-2"
```

---

## 📘 Module Lifecycle

SeyoAWE modules:

1. Are loaded at runtime by the engine
2. Receive `context` and `**module_config` in `__init__`
3. Methods are called dynamically based on workflow step
4. Return structured dictionaries with `status`, `message`, and optional `data`

---

### Example Method Response

```python
return {
    "status": "ok",
    "message": "Template rendered",
    "data": {
        "file": "envs/dev/config.yaml"
    }
}
```

| Field     | Type   | Description                                       |
| --------- | ------ | ------------------------------------------------- |
| `status`  | string | One of: `ok`, `fail`, `warn`                      |
| `message` | string | Human-readable status                             |
| `data`    | dict   | Optional: any output to store in workflow context |

---

## 🧰 Context Modules vs Step Modules

| Type               | Behavior                                                           |
| ------------------ | ------------------------------------------------------------------ |
| **Step module**    | Called once during a specific step (e.g. `module: slack`)          |
| **Context module** | Instantiated at start of workflow and reused across multiple steps |

Context modules are defined in `context_modules` like so:

```yaml
context_modules:
  git:
    module: git_module.Git
    repo: "https://github.com/org/repo.git"
    branch: "feature/{{ context.user }}"
```

Then used as:

```yaml
action: context.git.add_file_from_template
```

---

## 🧪 Testing a Module

You can test methods like:

```python
from modules.git_module.git_module import Git

ctx = {"user": "alice", "github_token": "..."}
mod = Git(ctx, repo="...", branch="dev")

result = mod.add_file_from_template("main.tf.j2", "envs/dev/main.tf", {"region": "us-west-2"})
print(result)
```

Or use:

```bash
sawectl run workflows/example.yaml
```

---

## 📋 Best Practices

| Practice                       | Why it matters                                 |
| ------------------------------ | ---------------------------------------------- |
| Use `module.yaml`              | Enables CLI validation and module discovery    |
| Include `usage_reference.yaml` | Helps with documentation and sample generation |
| Avoid global state             | Modules may be run concurrently or restarted   |
| Return structured results      | Enables context passing and error handling     |
| Log clearly and concisely      | Helps trace module behavior in logs            |

---

## 🔐 Commercial Modules

Modules may be distributed:

* As open-source (as part of the community edition)
* Bundled with the commercial binary (closed source - requires commercial license)

If you’re building commercial or internal modules:

* Store sensitive logic securely
* Use external APIs with robust error handling
* Avoid relying on engine internals — keep logic modular

---

## 📤 Publishing Your Module

Want to contribute?

1. Fork the repo
2. Add your module under `modules-community/`
3. Include `module.yaml` and `usage_reference.yaml`
4. Submit a pull request!

You can also publish proprietary modules in private repos using the **module loader config**.

---

## 🛠 CLI Integration (`sawectl`)

`sawectl` automatically picks up:

* Module names
* Methods
* Input schemas
* Usage examples

Try:

```bash
sawectl list-modules
sawectl validate-workflow workflows/infra.yaml
```

---

## 💬 Need Help?

* Submit GitHub issues
* Reach out to [yuri.bernstein@gmail.com](mailto:yuri.bernstein@gmail.com)
* Stay tuned for [seyoawe.dev/docs/modules](https://seyoawe.dev/docs/modules) *(Coming Soon)*
