import subprocess
import os
import pwd
from commons.logs import get_logger

logger = get_logger("command_module")

class Command:
    def __init__(self, context, **module_config):
        self.context = context
        self.module_config = module_config

    def run(self, command, shell="/bin/bash", cwd=None, user=None, env=None):
        try:
            logger.info(f"[COMMAND] Preparing to run: {command}")

            # Set environment
            run_env = os.environ.copy()
            if env:
                run_env.update(env)

            # If user is specified, get uid/gid
            preexec_fn = None
            if user:
                pw_record = pwd.getpwnam(user)
                uid = pw_record.pw_uid
                gid = pw_record.pw_gid
                def change_user():
                    os.setgid(gid)
                    os.setuid(uid)
                preexec_fn = change_user

            result = subprocess.run(
                command,
                shell=True,
                executable=shell,
                cwd=cwd,
                env=run_env,
                preexec_fn=preexec_fn,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            logger.info(f"[COMMAND] Completed with return code {result.returncode}")

            if result.returncode != 0:
                return {
                    "status": "fail",
                    "message": f"Command failed: {result.stderr.strip()}",
                    "data": {
                        "stdout": result.stdout.strip(),
                        "stderr": result.stderr.strip(),
                        "exit_code": result.returncode
                    }
                }

            return {
                "status": "ok",
                "message": "Command executed successfully",
                "data": {
                    "stdout": result.stdout.strip(),
                    "exit_code": result.returncode
                }
            }

        except Exception as e:
            logger.exception("[COMMAND] Unexpected error")
            return {
                "status": "fail",
                "message": f"Unhandled exception: {str(e)}",
                "data": {}
            }
