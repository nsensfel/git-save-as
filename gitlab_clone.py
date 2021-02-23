#!/usr/bin/env python3
import gitlab
import argparse

args_parser = argparse.ArgumentParser(
   description = "Git-save-as interface to GitLab"
)

args_parser.add_argument(
   'repo_name',
   type = str,
   default = '',
   help = 'Name of the repo to create'
)

args_parser.add_argument(
   '--private-token',
   '-p',
   type = str,
   default = '',
   help = 'Private token for login'
)

args_parser.add_argument(
   '--server',
   '-s',
   type = str,
   default = '',
   help = 'GitLab server'
)

#args_parser.add_argument(
#   '--group',
#   '-g',
#   type = str,
#   default = '',
#   help = 'Group to add the repo to (not working)'
#)
#

args_parser.add_argument(
   '--group',
   '-g',
   type = int,
   default = 0,
   help = 'Group ID to add the repo to'
)

args = args_parser.parse_args()

gitlab_interface = gitlab.Gitlab(args.server, private_token = args.private_token)

gitlab_interface.auth()

#if (args.group == ''):
#   gitlab_interface.projects.create({'name': args.repo_name})
#else:
#   matching_groups = gitlab_interface.groups.list(search = args.group)
#
#   if (not matching_groups):
#      butchered_name = ''.join([c for c in args.group if c.isalpha()])
#      print("[D] Group did not exist. Creating " + butchered_name)
#      gitlab_interface.groups.create({'name': butchered_name, 'path': args.group}) 
#
#   group_id = matching_groups[0].id 
try:
   gitlab_interface.projects.create(
      {
         'name': args.repo_name,
         'namespace_id': args.group
      }
   )
except Exception as e:
   print(str(e))

project = gitlab_interface.projects.list(search=args.repo_name)[0]
print("New repo url: " + project.ssh_url_to_repo)
