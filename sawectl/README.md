# 🛠️ sawectl — SeyoAWE CLI Tool

`sawectl` is the official CLI for managing workflows and modules in the **SeyoAWE** automation system.

It supports authoring, validating, and running YAML-defined workflows. It also enables module scaffolding, schema validation, and CLI-first automation — all backed by strict JSON Schema and best practices.

---

## 🚀 Key Features

- 🧱 **Workflow scaffolding**: Generate full or minimal workflow files from module usage
- ⚙️ **Module generation**: Bootstrap new modules with Python stubs, manifest, and usage reference
- ✅ **Deep validation**: Schema-level validation of workflows and module manifests
- 🧪 **Ad-hoc execution**: Run workflows directly against a running SeyoAWE server
- 🔒 **Schema-driven**: Uses strict Schema validation for both workflows and modules

---

## 🔧 Commands

### 🔹 `init module <name>`

Scaffold a new module inside `modules/`.

```bash
sawectl init module slack_module
```

Creates:

```
modules/slack_module/
  ├─ slack_module.py               # Python class with a stub method
  ├─ module.yaml                   # Manifest (schema-compliant)
  └─ usage_reference.yaml         # Step examples for this module
```

---

### 🔹 `init workflow <name>`

Generate a new workflow file.

#### Minimal template (default):

```bash
sawectl init workflow hello
```

#### Full template with modules and trigger:

```bash
sawectl init workflow my_flow --full --modules slack,email --trigger api
```

Options:

| Option             | Description                                      |
| ------------------ | ------------------------------------------------ |
| `--full`           | Include steps from module usage references       |
| `--modules`        | Comma-separated module list                      |
| `--modules-path`   | Path to modules directory (default: `./modules`) |
| `--workflows-path` | Output dir for workflow (default: `./workflows`) |
| `--trigger`        | `api`, `git`, `scheduled`, `ad-hoc`              |

---

### 🔹 `validate-workflow`

Validate a workflow YAML against schema, steps, and modules.

```bash
sawectl validate-workflow --workflow workflows/my_flow.yaml --verbose
```

Checks:

* JSON Schema compliance
* Valid step types and IDs
* Valid action and input fields for each module method
* Context modules are resolvable
* `on_success`, `on_failure`, `global_failure_handler` blocks

---

### 🔹 `validate-modules`

Validate all `module.yaml` manifests.

```bash
sawectl validate-modules
```

Checks:

* Schema compliance
* Required fields: `name`, `class`, `methods`, etc.
* Method args structure and required keys

---

### 🔹 `run`

Trigger a workflow against a SeyoAWE server.

```bash
sawectl run --workflow workflows/demo.yaml --server localhost:8080
```

Triggers a run of a workflow (can also be triggered with `curl -X POST`)

---

## 🧪 Example Workflow

```bash
sawectl init module logger
sawectl init workflow hello_logger --full --modules logger
sawectl validate-workflow --workflow workflows/hello_logger.yaml
sawectl run --workflow workflows/hello_logger.yaml --server localhost:8080
```

---

## 🧠 Roadmap Ideas

* [ ] Validate `usage_reference.yaml` structure and types
* [ ] Add `--strict` mode (e.g., enforce version format, require `returns`)
* [ ] CLI-based documentation generator per module
* [ ] Lint workflows (e.g., unused outputs, unreachable steps)
* [ ] Auto-generate example runs from usage references

---

## 📚 Documentation

See the full platform docs at:

👉 [https://seyoawe.dev/docs](https://seyoawe.dev/docs)
👉 DSL Reference: [https://seyoawe.dev/docs/dsl](https://seyoawe.dev/docs/dsl)
👉 Modules Reference: [https://seyoawe.dev/docs/modules](https://seyoawe.dev/docs/modules)

---

## 🧑‍💻 Author

**Yuri Bernstein**
Creator of SeyoAWE
yuri.bernstein@gmail.com

---

