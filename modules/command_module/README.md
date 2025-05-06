# 🧩 `command_module`

The `command_module` allows you to execute shell commands directly from your SeyoAWE workflows. It's useful for quick local operations, scripting, or interacting with tools not yet integrated via formal modules.

---

## ✅ Features

* Run any shell command (e.g. `ls`, `pwd`, `git status`)
* Choose shell: `bash`, `sh`, `zsh`, etc.
* Run as specific user (e.g. `nobody`, `deploy`)
* Set working directory
* Inject custom environment variables
* Captures `stdout`, `stderr`, and exit `code`

---

## 🧪 Example Usage

```yaml
- id: run_pwd
  type: action
  action: command_module.Command.run
  input:
    shell: "bash"
    command: "pwd"
    working_dir: "/tmp"
    run_as_user: "nobody"
    env:
      MY_VAR: "some_value"
  register_output: pwd_output
```

---

## 🎯 Input Parameters

| Name          | Type   | Required | Description                         |
| ------------- | ------ | -------- | ----------------------------------- |
| `shell`       | string | yes      | Shell to use (e.g., `bash`, `sh`)   |
| `command`     | string | yes      | The command line to execute         |
| `working_dir` | string | no       | Directory to `cd` into before exec  |
| `run_as_user` | string | no       | User to execute the command as      |
| `env`         | dict   | no       | Environment variables for the shell |

---

## 📤 Output Structure

On success (`status: ok`), the module returns:

```json
{
  "status": "ok",
  "message": "Command executed successfully",
  "data": {
    "stdout": "...",
    "stderr": "...",
    "code": 0
  }
}
```

On failure (`status: fail`), the `message` will explain the reason, and `code` will be non-zero.

---

## ⚠️ Notes

* Security: This module executes local shell commands. Avoid exposing it in untrusted workflows.
* Currently does not sandbox or isolate the process — future versions may support `nsjail`, `bwrap`, or `chroot`.
