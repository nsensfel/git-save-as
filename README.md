# git-save-as
You need `git >= 2.25` to run this, as it makes use of the
`git submodule set-url` command.

## How to use
First of all, a big warning: **THIS SCRIPT WAS RUSHED TOGETHER, TEST THINGS OUT
BEFORE USING IT ON YOUR ACTUAL REPOS**.

Let's say you want to keep your own copy
of https://github.com/ArduPilot/ardupilot.git and its submodules.

Start by making sure this quickly hacked together script doesn't break when it
handles your case:

```
$ ./git_save_as.py -b my_git_save_as_branch -t /tmp/my_git_save_as_temp_dir https://github.com/ArduPilot/ardupilot.git "./local_clone.sh ~/git_repos/main_projects/ " "./local_clone.sh ~/git_repos/submodules/ "
```
This should create an interconnected set of repositories in your `~/git_repos/`
folder, with your copy of the ardupilot's repo being in
`~/git_repos/main_projects/` and its submodules being in
`~/git_repos/submodules/`.

If nothing exploded, you can push your luck and try with GitLab:
```
./git_save_as.py https://github.com/ArduPilot/ardupilot.git -b my_git_save_as_branch -t /tmp/my_other_git_save_as_temp_dir "./gitlab_clone.py -p MyPr1v4TeT0k3n -s https://my_great_gitlab.server.com/ -g my_main_group_id " "./gitlab_clone.py -p MyPr1v4TeT0k3n -s https://my_great_gitlab.server.com/ -g my_submodule_group_id "
```
Ardupilot will be added to that first group, and its submodules (recursively)
to the other. In every repository, the my_git_save_as_branch will link the
submodules to repositories hosted at https://my_great_gitlab.server.com/.

## Adding support for another platform
This *totally* safe script is very easy to extend to other hosting solutions.
Indeed, it'll just call whatever commands are passed as its last two parameters
(that second one really should be optional, but oh well...) with the name of
a repository and expect these commands to print a line like:
```
New repo url: URL_TO_REPO
```
It'll then consider URL_TO_REPO to be where the content of the repository should
be pushed.
