#!/usr/bin/env python3

VERSION = "0.0.1"
# SeyoAWE CLI Tool

import os
import sys
import argparse
import requests
import yaml
import json
from pathlib import Path
from jsonschema import validate as jsonschema_validate, Draft202012Validator
from jsonschema.exceptions import ValidationError

# === UTILS ===
def load_yaml(path):
    try:
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
            if data is None:
                raise ValueError("YAML file is empty")
            return data
    except yaml.YAMLError as ye:
        print(f"[ERROR] Invalid YAML format in {path}: {ye}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Failed to load YAML from {path}: {e}")
        sys.exit(1)

def load_json_schema(schema_path):
    try:
        with open(schema_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load schema from {schema_path}: {e}")
        sys.exit(1)

def validate_against_schema(yaml_data, schema_path):
    schema = load_json_schema(schema_path)
    try:
        Draft202012Validator(schema).validate(yaml_data)
    except ValidationError as e:
        print(f"[SCHEMA FAIL] {e.message} at {list(e.path)}")
        sys.exit(1)
    except Exception as e:
        print(f"[SCHEMA ERROR] {e}")
        sys.exit(1)

def load_module_manifest(modules_dir, module_name):
    module_path = Path(modules_dir) / module_name / "module.yaml"
    if not module_path.exists():
        return None
    try:
        with open(module_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"[ERROR] Failed to read module.yaml for '{module_name}': {e}")
        return None

def extract_module_and_method(action_str, context_modules):
    parts = action_str.split('.')
    if parts[0] == 'context' and len(parts) >= 3:
        cm_id = parts[1]
        method = parts[2]
        module_ref = context_modules.get(cm_id, {}).get('module')
        if not module_ref:
            return None, None
        module_name = module_ref.split('.')[0]
        return module_name, method
    elif len(parts) >= 3:
        return parts[0], parts[2]
    elif len(parts) == 2:
        return parts[0], parts[1]
    return None, None

def validate_step(step, modules_dir, context_modules):
    if 'id' not in step or 'type' not in step:
        return False, f"Step missing 'id' or 'type': {step}"

    action_str = step.get('action') or step.get('config', {}).get('action')
    if not action_str:
        return True, f"Step '{step['id']}' is valid (no action to validate)"

    module_name, method_name = extract_module_and_method(action_str, context_modules)
    if not module_name or not method_name:
        return False, f"Cannot resolve module or method in action: {action_str}"

    manifest = load_module_manifest(modules_dir, module_name)
    if manifest is None:
        return False, f"Module '{module_name}' not found or has no manifest"

    matching_method = next((m for m in manifest.get('methods', []) if m['name'] == method_name), None)
    if not matching_method:
        return False, f"""
        Method '{method_name}' not found in module '{module_name}' manifest.
        Available methods: [ {', '.join(m['name'] for m in manifest.get('methods', []))} ]
        """

    expected_args = {arg['name'] for arg in matching_method.get('arguments', []) if arg.get('required')}
    provided_args = set(step.get('input', {}).keys() if 'input' in step else step.get('config', {}).keys())

    missing = expected_args - provided_args
    if missing:
        return False, f"""
        Missing required input(s) {missing} in step '{step['id']}'
        """

    return True, f"Step '{step['id']}' validated successfully"

def validate_workflow_deep(args):
    raw = load_yaml(args.workflow)
    schema_path = os.path.join(os.path.dirname(__file__), "dsl.schema.json")
    validate_against_schema(raw, schema_path)

    workflow = raw.get('workflow', raw)
    modules_dir = args.modules or "modules"

    context_modules_raw = workflow.get('context_modules', {})
    context_modules = context_modules_raw if isinstance(context_modules_raw, dict) else {}

    if 'name' not in workflow or 'steps' not in workflow:
        print("[FAIL] Workflow must contain 'name' and 'steps'")
        sys.exit(1)

    step_ids = set()
    for step in workflow['steps']:
        if step['id'] in step_ids:
            print(f"[FAIL] Duplicate step ID: {step['id']}")
            sys.exit(1)
        step_ids.add(step['id'])

        ok, msg = validate_step(step, modules_dir, context_modules)
        if not ok:
            print(f"[FAIL] {msg}")
            sys.exit(1)
        elif args.verbose:
            print(f"[OK] {msg}")

    for cm_id, cm_conf in context_modules.items():
        ref = cm_conf.get('module')
        if not ref:
            print(f"[FAIL] Context module '{cm_id}' missing 'module'")
            sys.exit(1)
        module_name = ref.split('.')[0]
        manifest = load_module_manifest(modules_dir, module_name)
        if manifest is None:
            print(f"[FAIL] Context module type '{module_name}' not found")
            sys.exit(1)
        elif args.verbose:
            print(f"[OK] Context module '{cm_id}' valid")

    if 'global_failure_handler' in workflow:
        ok, msg = validate_step(workflow['global_failure_handler'], modules_dir, context_modules)
        if not ok:
            print(f"[FAIL] global_failure_handler: {msg}")
            sys.exit(1)
        elif args.verbose:
            print(f"[OK] global_failure_handler validated")

    if 'on_failure' in workflow:
        for step in workflow['on_failure'].get('steps', []):
            ok, msg = validate_step(step, modules_dir, context_modules)
            if not ok:
                print(f"[FAIL] on_failure step: {msg}")
                sys.exit(1)
            elif args.verbose:
                print(f"[OK] on_failure step '{step['id']}' validated")

    if 'on_success' in workflow:
        for step in workflow['on_success'].get('steps', []):
            ok, msg = validate_step(step, modules_dir, context_modules)
            if not ok:
                print(f"[FAIL] on_success step: {msg}")
                sys.exit(1)
            elif args.verbose:
                print(f"[OK] on_success step '{step['id']}' validated")

    print("[VALIDATION PASSED] Workflow is fully valid.")


# === HELPERS ===
def validate_module_manifest(path_to_manifest, schema_path):
    try:
        manifest = load_yaml(path_to_manifest)
        schema = load_json_schema(schema_path)
        Draft202012Validator(schema).validate(manifest)
        print(f"[OK] {path_to_manifest} is valid ✅")
        return True
    except ValidationError as e:
        print(f"[FAIL] {path_to_manifest}: {e.message} at {list(e.path)}")
        return False
    except Exception as e:
        print(f"[ERROR] {path_to_manifest}: {e}")
        return False

def validate_all_modules(args):
    modules_dir = Path(args.modules or "modules")
    schema_path = os.path.join(os.path.dirname(__file__), "module.schema.json")
    if not modules_dir.exists():
        print(f"[ERROR] Modules path '{modules_dir}' does not exist.")
        sys.exit(1)

    any_fail = False
    for mod in sorted(modules_dir.iterdir()):
        if not mod.is_dir():
            continue
        manifest_path = mod / "module.yaml"
        if not manifest_path.exists():
            print(f"[WARN] Skipping {mod.name}: No module.yaml found")
            continue
        ok = validate_module_manifest(manifest_path, schema_path)
        if not ok:
            any_fail = True

    if any_fail:
        print("[RESULT] ❌ One or more modules failed validation")
        sys.exit(1)
    else:
        print("[RESULT] ✅ All module manifests passed validation")


def load_all_usage_examples(modules_path, selected=None):
    steps = []
    context_modules = {}

    for module_path in Path(modules_path).iterdir():
        if not module_path.is_dir():
            continue
        modname = module_path.name
        if selected and modname not in selected:
            continue
        usage_file = module_path / "usage_reference.yaml"
        if not usage_file.exists():
            continue
        try:
            with open(usage_file, "r") as f:
                docs = list(yaml.safe_load_all(f))
            for doc in docs:
                step = {
                    "id": f"{modname}_{doc['method']}",
                    "type": "action",
                    "action": f"{modname}.{doc['method']}",
                    "input": doc.get("example_input", {})
                }
                steps.append(step)
            context_modules[f"ctx_{modname}"] = {
                "module": f"{modname}.{modname.capitalize()}"
            }
        except Exception as e:
            print(f"[WARN] Failed to read usage_reference.yaml in {modname}: {e}")
    return context_modules, steps


def generate_full_workflow_from_schema_and_modules(schema_path, modules_dir="modules", selected_modules=None):
    schema = load_json_schema(schema_path)
    defs = schema.get("$defs", {})
    workflow_schema = schema["properties"]["workflow"]

    def resolve_ref(ref):
        key = ref.split("/")[-1]
        return defs.get(key, {})

    def build_example(prop):
        if "$ref" in prop:
            return build_structure(resolve_ref(prop["$ref"]))
        if "enum" in prop:
            return prop["enum"][0]
        typ = prop.get("type")
        if typ == "string":
            return "example_string"
        if typ == "integer":
            return 42
        if typ == "boolean":
            return True
        if typ == "array":
            return [build_example(prop.get("items", {}))]
        if typ == "object":
            return build_structure(prop)
        return "example_value"

    def build_structure(schema_node):
        result = {}
        for key, val in schema_node.get("properties", {}).items():
            if key == "steps":
                continue  # inject real steps later
            result[key] = build_example(val)
        return result

    # === START BUILDING WF STRUCTURE ===
    wf = build_structure(workflow_schema)
    wf["steps"] = []
    context_modules, steps = load_all_usage_examples(modules_dir, selected=selected_modules)

    # Sort for consistency
    wf["steps"] = sorted(steps, key=lambda x: x["id"])
    # wf["context_modules"] = context_modules
    return {"workflow": wf}




# === COMMANDS ===
def init_module_from_schema(args):
    schema_path = os.path.join(os.path.dirname(__file__), "module.schema.json")
    schema = load_json_schema(schema_path)

    module_name = args.name
    class_name = module_name.capitalize()
    module_dir = Path(args.modules or "modules") / module_name
    module_dir.mkdir(parents=True, exist_ok=True)

    # 1. Generate manifest
    manifest = {
        "name": module_name,
        "class": class_name,
        "version": "1.0",
        "author": "Your Name",
        "methods": [
            {
                "name": "run",
                "description": "Example method that echoes input.",
                "arguments": [
                    {"name": "param1", "type": "string", "required": True},
                    {"name": "param2", "type": "int", "required": False}
                ],
                "returns": {
                    "type": "object",
                    "structure": {
                        "status": "one_of(['ok', 'fail'])",
                        "message": "string",
                        "data": "object"
                    }
                }
            }
        ]
    }

    # 2. Save manifest
    with open(module_dir / "module.yaml", "w") as f:
        yaml.dump(manifest, f, sort_keys=False)

    # 3. Generate Python class
    class_code = f"""class {class_name}:
    def __init__(self, context, **module_config):
        self.context = context
        self.config = module_config or {{}}

    def run(self, param1, param2=None):
        return {{
            "status": "ok",
            "message": "Echoing input",
            "data": {{"param1": param1, "param2": param2}}
        }}
"""
    with open(module_dir / f"{module_name}.py", "w") as f:
        f.write(class_code)

    # 4. usage_reference.yaml
    usage_ref = [
        {
            "method": "run",
            "example_input": {
                "param1": "hello",
                "param2": 123
            }
        }
    ]
    with open(module_dir / "usage_reference.yaml", "w") as f:
        yaml.dump_all(usage_ref, f)

    print(f"[INIT] Module skeleton created at: {module_dir}")


def run_workflow(args):
    workflow = load_yaml(args.workflow)
    try:
        res = requests.post(
            f"http://{args.server}/api/adhoc",
            json={"workflow": workflow},
            timeout=10
        )
        res.raise_for_status()
        print(f"[SUCCESS] Workflow triggered. Response: {res.json()}")
    except Exception as e:
        print(f"[ERROR] Failed to trigger workflow: {e}")
        sys.exit(1)


def init_module(args):
    module_dir = Path(f"modules/{args.name}")
    module_dir.mkdir(parents=True, exist_ok=True)

    with open(module_dir / "module.yaml", "w") as f:
        f.write("""name: {name}
class: {class_name}
version: 1.0
author: Your Name

methods:
  - name: run
    description: Basic run method
    arguments:
      - name: param1
        type: string
        required: true
      - name: param2
        type: int
        required: false
""".format(name=args.name, class_name=args.name.capitalize()))

    with open(module_dir / f"{args.name}.py", "w") as f:
        f.write(f"""class {args.name.capitalize()}:
    def __init__(self, context, **module_config):
        self.context = context

    def run(self, param1, param2=None):
        return {{"status": "ok", "message": "Success", "data": {{"param1": param1, "param2": param2}} }}
""")
    print(f"[INIT] Module skeleton created at {module_dir}")

def extract_enum_from_schema(schema, path):
    """
    Extracts an enum list from a schema given a dotted path like 'workflow.trigger.type'
    """
    parts = path.split(".")
    node = schema
    for part in parts:
        if "properties" in node:
            node = node["properties"].get(part, {})
        else:
            return []
        if "$ref" in node:
            ref_key = node["$ref"].split("/")[-1]
            node = schema.get("$defs", {}).get(ref_key, {})
    return node.get("enum", [])


def init_workflow(args):
    workflows_dir = Path(args.workflows_path or "workflows")
    workflows_dir.mkdir(parents=True, exist_ok=True)
    path = workflows_dir / f"{args.name}.yaml"

    if args.full:
        schema_path = os.path.join(os.path.dirname(__file__), "dsl.schema.json")
        schema = load_json_schema(schema_path)
        valid_triggers = extract_enum_from_schema(schema, "workflow.trigger.type")
        if args.trigger not in valid_triggers:
            print(f"[ERROR] Invalid trigger type '{args.trigger}'. Allowed: {', '.join(valid_triggers)}")
            sys.exit(1)
        
        selected = [m.strip() for m in args.modules.split(",")] if args.modules else None
        wf = generate_full_workflow_from_schema_and_modules(schema_path, args.modules_path or "modules", selected_modules=selected)
        wf["workflow"]["name"] = args.name
        wf["workflow"]["trigger"] = {
            "type": args.trigger
        }
        valid_triggers = {"api", "git", "scheduled", "ad-hoc"}
        if args.trigger not in valid_triggers:
            print(f"[ERROR] Unsupported trigger type '{args.trigger}'. Must be one of: {', '.join(valid_triggers)}")
            sys.exit(1)
        # Filter context modules to only those actually used in steps
        used_module_names = set(
            step["action"].split(".")[0]
            for step in wf["workflow"]["steps"]
            if "action" in step and isinstance(step["action"], str)
        )
        wf["workflow"]["context_modules"] = {
            k: v for k, v in wf["workflow"]["context_modules"].items()
            if v.get("module", "").split(".")[0] in used_module_names
        }


    else:
        wf = {
            "workflow": {
                "name": args.name,
                "steps": [
                    {
                        "id": "step1",
                        "type": "action",
                        "action": "logger.run",
                        "input": {"message": "Hello, world!"}
                    }
                ]
            }
        }

    header_comment = f"""
        # =============================================
        # SeyoAWE Full Workflow Example
        # Generated via `sawectl init workflow --full`
        # 
        # 🔗 DSL Reference: https://seyoawe.dev/docs/dsl
        # 🔗 Modules Reference: https://seyoawe.dev/docs/modules
        # 
        # Modify this file to suit your use case.
        # =============================================
        """

    for k in ["global_failure_handler", "on_failure", "on_success"]:
        if k in wf["workflow"] and not wf["workflow"][k]:
            del wf["workflow"][k]

    with open(path, 'w') as f:
        f.write(header_comment + "\n")


        dumped = yaml.dump(wf, sort_keys=False, width=120)


        def add_spacing_to_blocks(text, key):
            lines = text.splitlines()
            result = []
            inside_block = False
            for i, line in enumerate(lines):
                if line.strip().startswith(f"- id:"):
                    if inside_block:
                        result.append("") 
                    inside_block = True
                result.append(line)
            return "\n".join(result)

        dumped = add_spacing_to_blocks(dumped, key="steps")
        f.write(dumped)


    print(f"[INIT] Workflow created at {path}")




# === CLI SETUP ===
def main():
    parser = argparse.ArgumentParser(
        prog="sawectl",
        description="SeyoAWE CLI Tool",
        add_help=False  # disables auto -h/--help
    )
    parser.add_argument('-h', '--help', action='store_true', help="Show this help message and exit")
    parser.add_argument('-v', '--version', action='version', version=VERSION, help="Show version and exit")
    subparsers = parser.add_subparsers(dest="command")

    # run
    p_run = subparsers.add_parser("run", help="Run a workflow ad-hoc")
    p_run.add_argument("--workflow", required=True)
    p_run.add_argument("--server", required=True)
    p_run.set_defaults(func=run_workflow)

    # validate-workflow (deep)
    p_val = subparsers.add_parser("validate-workflow", help="Validate a workflow file deeply")
    p_val.add_argument("--workflow", required=True)
    p_val.add_argument("--modules", help="Path to modules dir", default="modules")
    p_val.add_argument("--verbose", action="store_true")
    p_val.set_defaults(func=validate_workflow_deep)

    # init module/workflow
    p_init = subparsers.add_parser("init", help="Initialize modules or workflows")
    sub_init = p_init.add_subparsers(dest="type")
    p_mod = sub_init.add_parser("module", help="Create a new module")
    p_mod.add_argument("name")
    p_mod.add_argument("--modules", help="Path to modules dir", default="modules")
    p_mod.set_defaults(func=init_module_from_schema)

    # validate-modules
    p_valmod = subparsers.add_parser("validate-modules", help="Validate all module manifests")
    p_valmod.add_argument("--modules", help="Path to modules dir", default="modules")
    p_valmod.set_defaults(func=validate_all_modules)

    # init workflow
    p_wf = sub_init.add_parser("workflow", help="Create a new workflow")
    p_wf.add_argument("name")
    p_wf.add_argument("--minimal", action="store_true")
    p_wf.add_argument("--full", action="store_true")
    p_wf.add_argument("--modules", help="Comma-separated list of modules to include (default: all)")
    p_wf.add_argument("--modules-path", help="Path to modules dir", default="modules")
    p_wf.add_argument("--workflows-path", help="Path to workflows dir", default="workflows")
    p_wf.add_argument("--trigger", help="Trigger type (api, git, scheduled, etc)", default="api")
    p_wf.set_defaults(func=init_workflow)


    args = parser.parse_args()

    if getattr(args, 'help', False) or not hasattr(args, 'func'):
        print("""
        Usage: sawectl <command> [options]

        SeyoAWE CLI Tool — Workflow Automation for Humans.

        Available commands:

        init workflow         Create a new workflow (minimal or full template)
        init module           Scaffold a new module with manifest, code, and usage reference
        run                   Trigger an ad-hoc workflow against a running SeyoAWE engine
        validate-workflow     Deep-validate a workflow against schema and module manifests
        validate-modules      Validate all module.yaml manifests in the modules directory

        Options for `init workflow`:
        --full                        Generate a full workflow based on module usage and schema
        --minimal                     Generate a minimal stub workflow (default)
        --modules <csv>              Comma-separated list of module names to include (default: all)
        --modules-path <dir>         Path to modules directory (default: ./modules)
        --workflows-path <dir>       Output path for workflow files (default: ./workflows)
        --trigger <type>             Trigger type (api | git | scheduled | ad-hoc)

        Options for `run`:
        --workflow <file>            Path to a workflow YAML file
        --server <host:port>         Address of the SeyoAWE server (e.g., localhost:8080)

        Options for `validate-workflow`:
        --workflow <file>            Workflow file to validate
        --modules <dir>              Path to modules directory (default: ./modules)
        --verbose                    Print detailed validation output

        Options for `validate-modules`:
        --modules <dir>              Path to modules directory (default: ./modules)

        Examples:

        sawectl init module slack_module
        sawectl init workflow my_workflow --full --modules slack_module,email_module
        sawectl run --workflow workflows/my_workflow.yaml --server localhost:8080
        sawectl validate-workflow --workflow workflows/my_workflow.yaml --verbose
        sawectl validate-modules

        Documentation → https://seyoawe.dev/docs
        """)
        sys.exit(0)
    args.func(args)


if __name__ == "__main__":
    main()