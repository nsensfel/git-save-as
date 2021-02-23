#!/usr/bin/env python3
import argparse
import io
import os
import re
import subprocess
import fileinput

# TODO: test git 2.25 mini

args_parser = argparse.ArgumentParser(
   description = (
      "Saves a Git repository and its submodules (recursively) to another"
      " location."
   )
)

args_parser.add_argument(
   '--temporary-clone-folder',
   '-t',
   type = str,
   dest ='temporary_clone_folder',
   default = '/tmp/git_save_as',
   help = 'Folder in which to store temporary repositories.'
)

args_parser.add_argument(
   '--save-as-branch',
   '-b',
   type = str,
   dest ='save_as_branch',
   default = 'git-save-as',
   help = 'Branch to put the commits into.'
)

args_parser.add_argument(
   '--submodules-path-prefix',
   '-p',
   type = str,
   dest ='submodules_path_prefix',
   default = '/',
   help = 'Prefix to append to the relative path of cloned submodules.'
)

args_parser.add_argument(
   'source_repository',
   type = str,
   default = '',
   help = 'Source Git repository.'
)

args_parser.add_argument(
   'main_repository_creation_cmd',
   type = str,
   help = (
      "Running 'repository_creation_cmd repo_name' should  create a repository"
      " and echo its resulting Git URL."
   )
)

args_parser.add_argument(
   'submodule_repository_creation_cmd',
   type = str,
   default = None,
   help = (
      "Running 'repository_creation_cmd repo_name' should  create a repository"
      " and echo its resulting Git URL."
   )
)

args = args_parser.parse_args()

def ensure_directory_exists (dir_name):
   subprocess.Popen(['mkdir', '-p', dir_name]).wait()

   return

def get_repository_name (repository_url):
   repo_name = os.path.basename(repository_url)

   if repo_name.endswith(".git"):
      repo_name = repo_name[:-4]

   return repo_name

def read_gitmodules (repository_path):
   result = dict()

   module_name = None
   module_path = None
   module_url = None
   module_branch = None

   print("[D] Parsing " + repository_path + "/.gitmodules...")

   try:
      with open(repository_path + "/.gitmodules", 'r') as gitmodules:
         for line in gitmodules:
            search = re.findall(r'\s*\[submodule\s*"(.+)"\]', line)
            if search:
               if (module_path != None):
                  result[module_path] = (module_name, module_url)
               module_name = search[0]
            else:
               search = re.findall(r'\s*path\s*=\s*([^\s]+)', line)
               if search:
                  module_path = search[0]
               else:
                  search = re.findall(r'\s*url\s*=\s*([^\s]+)', line)
                  if search:
                     module_url = search[0]
   except FileNotFoundError:
      return dict()

   if (module_path != None):
      result[module_path] = (module_name, module_url)

   return result

def read_git_submodule_status (repository_path):
   result = dict()

   git_submodule_status = subprocess.Popen(
      ['git', 'submodule', 'status'],
      cwd = repository_path,
      stdout=subprocess.PIPE
   )

   for line in io.TextIOWrapper(git_submodule_status.stdout, encoding="utf-8"):
      search = re.findall(r'\s*[-+]?([^-+\s]+)\s*([^\s]+)', line)

      if (search):
         (commit, path) = search[0]
         result[path] = commit

   return result

def get_direct_submodules_list (repository_path):
   data_from_gitmodules = read_gitmodules(repository_path)
   data_from_git_submodule_status = read_git_submodule_status(repository_path)

   result = dict()

   for submodule_path in data_from_gitmodules:
      (submodule_name, submodule_url) = data_from_gitmodules[submodule_path]
      submodule_commit = data_from_git_submodule_status[submodule_path]
      result[submodule_path] = (submodule_name, submodule_url, submodule_commit)

   return result

def clone_repository (repo_source, repo_name, dest_parent_dir):
   print(
      "[D] Cloning "
      + repo_name
      + " ("
      + repo_source
      + ") into "
      + dest_parent_dir
   )
   ensure_directory_exists(dest_parent_dir)

   subprocess.Popen(
      ['git', 'clone', repo_source, repo_name],
      cwd = dest_parent_dir
   ).wait()

   return (dest_parent_dir + "/" + repo_name)

def switch_to_commit (repository_path, commit):
   print(
      "[D] Switching "
      + repository_path
      + " to commit "
      + commit 
   )
   subprocess.Popen(
      ['git', 'checkout', commit],
      cwd = repository_path
   ).wait()

   return

def commit_submodule_changes (repository_path, save_as_branch):
   # TODO: this won't do if 'save_as_branch' is already a branch.
   print("[D] Creating branch " + save_as_branch + " in " + repository_path)
   subprocess.Popen(
      ['git', 'checkout', '-b', save_as_branch],
      cwd = repository_path
   ).wait()

   print("[D] Adding changes in " + repository_path)
   subprocess.Popen(
      ['git', 'add', '-u'],
      cwd = repository_path
   ).wait()

   print("[D] Committing changes in " + repository_path)
   subprocess.Popen(
      ['git', 'commit', '-m', 'git-save-as submodule changes'],
      cwd = repository_path
   ).wait()

   git_rev_parse = subprocess.Popen(
      ['git', 'rev-parse', 'HEAD'],
      cwd = repository_path,
      stdout=subprocess.PIPE
   )

   result = ""
   for line in io.TextIOWrapper(git_rev_parse.stdout, encoding="utf-8"):
      search = re.findall(r'([a-z0-9]+)', line)

      if (search):
         print(
            "[D] Repository in "
            + repository_path
            + " is now at commit "
            + search[0]
         )
         return search[0]

   
   return result

def get_new_remote_url (repo_name, is_submodule_repo, args):
   repository_creator = None

   if (is_submodule_repo):
      repository_creator = subprocess.Popen(
               args.submodule_repository_creation_cmd + " " + repo_name,
               shell=True,
               stdout=subprocess.PIPE
            )
   else:
      repository_creator = subprocess.Popen(
               args.main_repository_creation_cmd + " " + repo_name,
               shell=True,
               stdout=subprocess.PIPE
         )

   result = None

   for line in io.TextIOWrapper(repository_creator.stdout, encoding="utf-8"):
      search = re.findall(r'\s*New repo url: (.+)', line)

      if (search):
         result = search[0]

         return result
   
   return ""
 
def send_to_new_host (repository_path, repo_name, is_submodule_repo, args):
   new_remote_url = get_new_remote_url(repo_name, is_submodule_repo, args)
   print(
      "[D] Adding new remote 'git-save-as' to "
      + repository_path
      + ": "
      + new_remote_url
   )
   subprocess.Popen(
      ['git', 'remote', 'add', 'git-save-as', new_remote_url],
      cwd = repository_path
   ).wait()

   print("[D] Pushing changes to new remote to " + new_remote_url)
   subprocess.Popen(
      ['git', 'push', 'git-save-as', '--all', '-u'],
      cwd = repository_path
   ).wait()

   return new_remote_url

def save_submodule_as (submodule_url, submodule_commit, args):
   module_name = get_repository_name(submodule_url)
   repository_path = clone_repository(
         submodule_url,
         module_name,
         (args.temporary_clone_folder + args.submodules_path_prefix)
      )
   switch_to_commit(repository_path, submodule_commit)
   save_submodules_as(repository_path, args)
   new_commit = commit_submodule_changes(repository_path, args.save_as_branch)
   new_url = send_to_new_host(
         repository_path,
         module_name,
         True,
         args
      )

   return (new_url, new_commit)

def rewrite_submodule_urls (repository_path, submodules, updated_submodules):
   print("[D] Rewriting submodule links in " + repository_path)

   for submodule_path in submodules:
      (submodule_name, submodule_url, submodule_commit) = submodules[submodule_path]
      (new_submodule_url, new_submodule_commit) = updated_submodules[submodule_path]

      print(
         "[D] Rewriting submodule links of "
         + repository_path
         + "/" + submodule_path
         + " to "
         + str(new_submodule_url)
      )

      print("git submodule set-url " + submodule_name + " " + new_submodule_url)
      subprocess.Popen(
         ['git', 'submodule', 'set-url', submodule_name, new_submodule_url],
         cwd = repository_path
      ).wait()

      subprocess.Popen(
         ['git', 'checkout', new_submodule_commit],
         cwd = repository_path + "/" + submodule_path
      ).wait()

   return

def save_submodules_as (repository_path, args):
   submodules = get_direct_submodules_list(repository_path)
   updated_submodules = dict()

   for submodule_path in submodules:
      (submodule_name, submodule_url, submodule_commit) = submodules[submodule_path]

      updated_submodules[submodule_path] = save_submodule_as(
            submodule_url,
            submodule_commit,
            args
         )

   rewrite_submodule_urls(repository_path, submodules, updated_submodules)

   return

main_repo_work_dir = (args.temporary_clone_folder + "/")
main_repo_name = get_repository_name(args.source_repository)
main_repository_path = main_repo_work_dir + main_repo_name
clone_repository(
   args.source_repository,
   main_repo_name,
   main_repo_work_dir
)

save_submodules_as(main_repository_path, args)
commit_submodule_changes(main_repository_path, args.save_as_branch)
send_to_new_host(main_repository_path, main_repo_name, False, args)
