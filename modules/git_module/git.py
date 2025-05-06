import os
import shutil
import subprocess
import re
import json
import requests
from git import Repo
from jinja2 import Environment, FileSystemLoader
from commons.logs import get_logger
from commons.get_config import get_config

config = get_config()
MODULES_BASE = config["directories"]["modules"]

logger = get_logger("git_module")

class Git:
    def __init__(self, context, **module_config):
        self.context = context
        self.config = module_config

        self.repo_url = self.config["repo"]
        self.branch = self.config["branch"]
        self.base_branch = self.config.get("base_branch", "main")
        self.work_dir = os.path.abspath(self.config.get("work_dir", "/tmp/gitops"))
        self.repo_dir = os.path.join(self.work_dir, "repo")
        self.ssh_key = self.config.get("ssh_key")
        self.handle_existing_branch = self.config.get("handle_existing_branch", "fail")
        self.github_token = self.config.get("github_token") or context.get("github_token")
        
        if not self.github_token:
            logger.warning("[GIT] GitHub token not found in config or context – PR actions may fail.")

        self.env = Environment(
            loader=FileSystemLoader(os.path.join(MODULES_BASE, "git_module", "templates")),
            autoescape=False
        )

        self._setup_git_env()
        self._clone_repo()

    def _setup_git_env(self):
        if self.ssh_key:
            os.environ["GIT_SSH_COMMAND"] = f"ssh -i {self.ssh_key} -o StrictHostKeyChecking=no"
        if os.path.exists(self.repo_dir):
            shutil.rmtree(self.repo_dir)

    def _clone_repo(self):
        logger.info(f"[GIT] Cloning {self.repo_url} into {self.repo_dir}")
        clone_url = self.repo_url
        if self.github_token:
            clone_url = clone_url.replace("https://", f"https://{self.github_token}:x-oauth-basic@")

        self.repo = Repo.clone_from(clone_url, self.repo_dir)
        self.repo.git.checkout(self.base_branch)

        if self.github_token:
            new_origin = self.repo_url.replace("https://", f"https://{self.github_token}:x-oauth-basic@")
            self.repo.git.remote("set-url", "origin", new_origin)

        self.repo.remote().fetch()
        remote_branches = [ref.name for ref in self.repo.remote().refs]
        remote_branch = f"origin/{self.branch}"

        if remote_branch in remote_branches:
            if self.handle_existing_branch == "pull":
                self.repo.git.checkout(self.branch)
                self.repo.git.pull("origin", self.branch)
            elif self.handle_existing_branch == "fail":
                raise Exception(f"Remote branch '{self.branch}' already exists and policy is 'fail'")
            else:
                raise Exception(f"Unknown handle_existing_branch value: {self.handle_existing_branch}")
        else:
            self.repo.git.checkout("-b", self.branch)
    def create_branch(self):
        self.repo.git.checkout("-b", self.branch)
        return {
            "status": "ok",
            "message": f"Branch '{self.branch}' created successfully",
            "data": {"branch": self.branch}
        }

    def add_file_from_template(self, template, destination, variables=None, commit_message="Add generated file"):
        ctx = self.context.get_all()
        if variables:
            ctx.update(variables)

        template_obj = self.env.get_template(template)
        rendered = template_obj.render(context=ctx)

        dest_path = os.path.join(self.repo_dir, destination)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

        with open(dest_path, "w") as f:
            f.write(rendered)

        self.repo.git.add(dest_path)
        self.repo.index.commit(commit_message)

        logger.info(f"[GIT] Added file: {destination}")
        return {
            "status": "ok",
            "message": f"File '{destination}' added successfully",
            "data": {"file": destination}
        }

    def open_pr(self, title="Auto-generated PR", body="This PR was created by SeyoAWE."):
        if not self.github_token:
            raise ValueError("Missing GitHub token in context as 'github_token'.")

        logger.info(f"[GIT] Pushing branch {self.branch} to origin before PR")
        self.repo.git.push("--set-upstream", "origin", self.branch)

        match = re.search(r"github\.com[:/](.+?)/(.+?)(\.git)?$", self.repo_url)
        if not match:
            raise ValueError(f"Invalid GitHub repo URL: {self.repo_url}")

        owner, repo = match.group(1), match.group(2)
        api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"

        payload = {
            "title": title,
            "head": self.branch,
            "base": self.base_branch,
            "body": body
        }

        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github+json"
        }

        response = requests.post(api_url, headers=headers, json=payload)
        if response.status_code not in [200, 201]:
            logger.error(f"[GIT] Failed to create PR: {response.status_code} {response.text}")
            return {"status": "fail", "message": response.text, "data": None}

        data = response.json()
        logger.info(f"[GIT] PR created: #{data['number']} - {data['html_url']}")
        return {
            "status": "ok",
            "message": "Pull Request created successfully",
            "data": {
                "pr_number": data["number"],
                "url": data["html_url"]
            }
        }

    def merge_pr(self):
        if not self.github_token:
            raise ValueError("Missing GitHub token")

        match = re.search(r"github\.com[:/](.+?)/(.+?)(\.git)?$", self.repo_url)
        if not match:
            raise ValueError(f"Invalid GitHub repo URL: {self.repo_url}")

        owner, repo = match.group(1), match.group(2)
        api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"

        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github+json"
        }

        r = requests.get(api_url, headers=headers)
        r.raise_for_status()
        prs = r.json()

        for pr in prs:
            if pr["head"]["ref"] == self.branch and pr["state"] == "open":
                pr_number = pr["number"]
                merge_url = f"{api_url}/{pr_number}/merge"
                merge = requests.put(merge_url, headers=headers, json={"merge_method": "squash"})
                if merge.status_code not in [200, 201]:
                    logger.error(f"[GIT] Merge failed: {merge.text}")
                    return {"status": "fail", "message": merge.text, "data": None}
                return {
                    "status": "ok",
                    "message": f"PR #{pr_number} merged successfully",
                    "data": {"pr_number": pr_number}
                }

        return {"status": "fail", "message": "PR not found for merging", "data": None}

    def close_pr(self):
        if not self.github_token:
            raise ValueError("Missing GitHub token")

        match = re.search(r"github\.com[:/](.+?)/(.+?)(\.git)?$", self.repo_url)
        if not match:
            raise ValueError(f"Invalid GitHub repo URL: {self.repo_url}")

        owner, repo = match.group(1), match.group(2)
        api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"

        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github+json"
        }

        r = requests.get(api_url, headers=headers)
        r.raise_for_status()
        prs = r.json()

        for pr in prs:
            if pr["head"]["ref"] == self.branch and pr["state"] == "open":
                pr_number = pr["number"]
                close_url = f"{api_url}/{pr_number}"
                close = requests.patch(close_url, headers=headers, json={"state": "closed"})
                if close.status_code not in [200, 201]:
                    logger.error(f"[GIT] Failed to close PR: {close.text}")
                    return {"status": "fail", "message": close.text, "data": None}
                return {
                    "status": "ok",
                    "message": f"PR #{pr_number} closed successfully",
                    "data": {"pr_number": pr_number}
                }

        return {"status": "fail", "message": "No open PR found to close", "data": None}

    def get_status(self):
        return {
            "status": "ok",
            "message": "Repository status retrieved successfully",
            "data": {
                "current_branch": self.repo.active_branch.name,
                "is_dirty": self.repo.is_dirty(),
                "untracked_files": self.repo.untracked_files,
            }
        }

    def add_files_from_templates(self, files, commit_message="Add multiple files"):
        ctx = self.context.get_all()
        logger.info(f"[GIT] Adding files: {files}")
        for item in files:
            if not isinstance(item, dict):
                try:
                    item = json.loads(item)
                except Exception as e:
                    logger.error(f"[GIT] Failed to parse item: {item} → {e}")
                    continue
            
            logger.info(f"[GIT] Adding file from template: {item['template']} to {item['destination']}")
            template = self.env.get_template(item["template"])
            rendered = template.render(context=ctx)
            dest_path = os.path.join(self.repo_dir, item["destination"])
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            with open(dest_path, "w") as f:
                f.write(rendered)
            self.repo.git.add(dest_path)
            logger.info(f"[GIT] Staged file: {item['destination']}")

        self.repo.index.commit(commit_message)
        return {
            "status": "ok",
            "message": "Files added and committed successfully",
            "data": {"files": files}
        }

    def cleanup(self):
        if os.path.exists(self.repo_dir):
            shutil.rmtree(self.repo_dir)
            logger.info(f"[GIT] Repo directory cleaned up: {self.repo_dir}")
        return {
            "status": "ok",
            "message": "Repository directory cleaned up",
            "data": None
        }
