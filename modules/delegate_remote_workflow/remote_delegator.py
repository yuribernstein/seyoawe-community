# remote_delegator.py

import os
import tempfile
import shutil
import yaml
from git import Repo
from engine.we import WorkflowEngine
from commons.logs import get_logger
from commons.get_config import get_config

logger = get_logger("delegate_remote_workflow")
global_config = get_config()


class RemoteDelegator:
    def __init__(self, context, **module_config):
        self.context = context
        self.config = module_config or {}

        logger.info(f"[DELEGATOR] Initialized with config: {self.config}")

    def run(self, repo, branch, path, token=None, run_conditions=None, condition_logic=None):
        # 1. Evaluate run conditions
        if run_conditions and not self._should_run(run_conditions, condition_logic):
            logger.info("[DELEGATOR] Run conditions not met, skipping execution")
            return {"status": "skipped", "reason": "run_conditions not met"}

        # 2. Clone the repo
        tmpdir = tempfile.mkdtemp()
        repo_url = self._auth_repo_url(repo, token or self.config.get("github_token"))

        try:
            logger.info(f"[DELEGATOR] Cloning repo {repo} into {tmpdir} (branch: {branch})")
            Repo.clone_from(repo_url, tmpdir, branch=branch, depth=1)

            wf_path = os.path.join(tmpdir, path)
            if not os.path.exists(wf_path):
                raise FileNotFoundError(f"Workflow not found: {wf_path}")

            with open(wf_path, "r") as f:
                workflow_dict = yaml.safe_load(f)

            # 3. Inject context and payload
            repo_base = self.context.get("repo_base_path") or global_config.get("repos_base_path", "")

            engine = WorkflowEngine(
                approval_manager=self.context["approval_manager"],
                workflow_dict={"workflow": workflow_dict["workflow"]},
                payload=self.context.get("payload", {}),
                repo_base_path=repo_base,
                skip_payload_parse=True,
                injected_context=self.context.get_all()
            )

            logger.info(f"[DELEGATOR] Executing remote workflow from {repo}@{branch}:{path}")
            engine.run()

            return {"status": "executed", "source": path}

        except Exception as e:
            logger.exception("[DELEGATOR] Failed to run delegated workflow")
            return {"status": "fail", "error": str(e)}

        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def _auth_repo_url(self, repo, token):
        if token:
            return repo.replace("https://", f"https://{token}:x-oauth-basic@")
        return repo

    def _should_run(self, conditions, logic):
        from engine.utils.match_engine import evaluate_operator

        condition_results = {}
        for i, cond in enumerate(conditions):
            actual = self.context.get(cond["path"])
            expected = cond.get("value")
            operator = cond.get("operator", "equals")
            result = evaluate_operator(operator, actual, expected)
            condition_results[str(i)] = result

        expr = logic or " and ".join(condition_results.keys())
        for cid, result in condition_results.items():
            expr = expr.replace(cid, str(result))

        try:
            return eval(expr)
        except Exception as e:
            logger.error(f"[DELEGATOR] Failed to eval condition logic: {e}")
            return False
