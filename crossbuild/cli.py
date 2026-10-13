from pathlib import Path
import argparse
import subprocess
import json
import shlex


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


	def run_ios(config):
		mac = config["workers"]["macos"]

		remote_login = mac["remote_login"]
		workspace = mac["workspace"]
		repo = config["repo"]

		project_name = Path(repo).stem

		remote_project_path = f"{workspace}/{project_name}"

		remote_command = f"""
			mkdir -p {shlex.quote(workspace)} &&
			if [ ! -d {shlex.quote(remote_project_path)}/.git ]; then
				git clone {shlex.quote(repo)} {shlex.quote(remote_project_path)};
			else
				cd {shlex.quote(remote_project_path)} &&
				git pull;
			fi &&
			cd {shlex.quote(remote_project_path)} &&
			npm install &&
			npm run ios
		"""

		subprocess.run(["ssh",remote_login,remote_command],check=True)


	if args.platform == "android":
		run_android(project_path)

	elif args.platform == "ios":
		run_ios(config)

	elif args.platform == "all":
		run_android(project_path)
		run_ios(config)