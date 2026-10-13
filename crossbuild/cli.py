from pathlib import Path
import argparse
import subprocess
import json
import shlex


def get_repo_root(project_path):
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=project_path,
        capture_output=True,
        text=True,
        check=True
    )

    return Path(result.stdout.strip())


def get_relative_project_path(project_path):
    project_path = Path(project_path).resolve()
    repo_root = get_repo_root(project_path)

    return project_path.relative_to(repo_root)



def main():
	parser = argparse.ArgumentParser()

	parser.add_argument("path")

	parser.add_argument(
		"--platform",
		choices=["android", "ios","all"],
		required=True
	)

	args = parser.parse_args()

	with open('crossBuildConfig.json') as f:
		config = json.load(f)
		print(config)

	project_path = Path(args.path).resolve()

	if not project_path.exists():
		raise FileNotFoundError(
			f"Project directory does not exist: {project_path}"
		)

	
	def run_android(project_path):
		subprocess.run(["npm", "run", "android"],cwd=project_path,check=True)


	def run_ios(config,project_path):
		mac = config["workers"]["macos"]

		remote_login = mac["remote_login"]
		repo = config["repo"]

		repo_name = repo.rstrip("/").split("/")[-1]

		if repo_name.endswith(".git"):
			repo_name = repo_name[:-4]

		workspace = "$HOME/crossbuild-workspace"
		remote_project = f"{workspace}/{repo_name}"
		relative_path = relative_path = get_relative_project_path(project_path).as_posix()
		remote_app = f"{remote_project}/{relative_path}"
		remote_command = f"""
			mkdir -p {workspace} &&

			if [ ! -d {remote_project}/.git ]; then
				git clone {shlex.quote(repo)} {remote_project};
			else
				cd {remote_project} &&
				git pull;
			fi &&

			cd {remote_app} &&
			npm install &&
			npm run ios
		"""

		subprocess.run(
			[
				"ssh",
				remote_login,
				f"zsh -lc {shlex.quote(remote_command)}"
			],
			check=True
		)
		


	if args.platform == "android":
		run_android(project_path)

	elif args.platform == "ios":
		run_ios(config, project_path)

	elif args.platform == "all":
		run_android(project_path)
		run_ios(config, project_path)