import git, os, sys, pathlib

repo_dir = pathlib.Path(os.path.abspath(__file__)).parent.parent
git_dir = repo_dir.joinpath('git','cmd','git.ext')

git.refresh(str(git_dir))
repo = git.Repo(str(repo_dir))

origin = repo.remotes.origin
pull_info = origin.pull()

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
from init import main
main()