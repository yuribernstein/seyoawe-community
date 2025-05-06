# 🤝 Contributing to SeyoAWE Community Edition

Thanks for your interest in contributing to **SeyoAWE** — a GitOps-native, human-in-the-loop automation engine.

We welcome pull requests for:

- ✅ New modules (in `modules/`)
- ✅ Improvements to existing modules
- ✅ New workflows and templates
- ✅ Documentation updates and corrections
- ✅ Enhancements to `sawectl` CLI or testing tools

---

## 📦 Repository Structure

```bash
modules/                # Core & community modules
  your_module/
    your_module.py
    module.yaml
    usage_reference.yaml
    templates/

workflows/              # Example and production-ready workflows
configuration/          # YAML-based engine configs
sawectl/                # CLI tool for validation and execution
docs/                   # Markdown-based documentation
````

---

## 🧩 How to Contribute a New Module

1. **Create a new folder** inside `modules/your_module_name`

2. Include:

   * `your_module.py` — Python logic class (can expose multiple methods)
   * `module.yaml` — metadata for methods and inputs
   * `usage_reference.yaml` — real examples for the CLI and docs
   * `templates/` — if needed for file rendering

3. Follow this return format in all methods:

```python
return {
  "status": "ok",  # or "fail", "warn"
  "message": "What happened",
  "data": {...}    # Optional: any output to use later
}
```

4. Validate your module using:

```bash
sawectl validate-module modules-community/your_module
```

---

## 🛠 Workflow Contributions

* Place new workflows in `workflows/community/`
* Use the full DSL: `trigger`, `steps`, `context_variables`, etc.
* Add an inline comment or short doc block explaining the use case

Validate with:

```bash
sawectl validate-workflow workflows/community/my_workflow.yaml
```

---

## 📝 Documentation Contributions

* Add or edit Markdown files in `/docs`
* Follow existing tone: practical, clear, developer-friendly
* Prefer examples and real-world use over theoretical explanations

---

## 📥 Pull Request Process

1. Fork the repo and create a new branch
2. Make your changes with clear commit messages
3. Run tests and validations
4. Submit a PR with a short summary and what it adds/fixes

We’ll review and respond quickly!

---

## 🚦 Contribution Standards

| Aspect     | Rule                                                       |
| ---------- | ---------------------------------------------------------- |
| Code style | Follow existing formatting; keep it clean and readable     |
| Logging    | Use `commons.logs.get_logger()` with descriptive messages  |
| Comments   | Use only when necessary — code should be mostly self-clear |
| Secrets    | Never commit credentials, tokens, or real keys             |
| Testing    | Manual runs are fine; validate workflows with `sawectl`    |

---

## 📢 Code of Conduct

I expect all contributors to be respectful, collaborative, and constructive. Discrimination or harassment of any kind is not tolerated.

---

## 🙋‍♂️ Need Help?

* Have questions? [Email me](mailto:yuri.bernstein@gmail.com)
* See something unclear? [Open an issue](https://github.com/yuribernstein/seyoawe-community/issues)

Thanks again for making SeyoAWE better. Let’s build powerful, transparent automation together.

—
**Yuri Bernstein**
