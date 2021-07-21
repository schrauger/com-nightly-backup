#!/usr/bin/env python

import os
import datetime
import sys

def module_exists(module_name):
    try:
        __import__(module_name)
    except ImportError:
        return False
    else:
        return True

# load passwords and other configs (stored separately in a file not tracked by git)
if module_exists("config"):
    import config
else:
    print("Please set up the config.py file. Copy 'sample.config.py' to 'config.py' and set the database passwords.")
    sys.exit(2)

def main():
	sites = config.sites
	for site in sites:
		run_db_incremental_backup(sites[site])
#	send_email()
	return 0

def run_db_incremental_backup(site):

	current_time = get_date_time()
	backup_root_db_incremental = site['backup_root_db_incremental']
	site_root_db_incremental = backup_root_db_incremental + '/' + site['directory']
	os.system('sudo -u ' + site['linux_user'] + ' ' + 'mkdir -p "' + site_root_db_incremental + '"')

	### Backup Production database
	# make sure there is no space between -p and the double quote
	os.system('sudo -u ' + site['linux_user'] + ' ' + 'mysqldump -u ' + site['user'] + " -p'" + site['password'] + "' " + site['db'] + ' > "' + site_root_db_incremental + '/' + site['db'] + '.sql"')

	### Initialize the git repo if not already
	os.system('sudo -u ' + site['linux_user'] + ' ' + 'git -C "' + site_root_db_incremental + '" init')

	### Add the file to the repo if not already
	os.system('sudo -u ' + site['linux_user'] + ' ' + 'git -C "' + site_root_db_incremental + '" add .')

	### Commit the production database to the git repo
	os.system('sudo -u ' + site['linux_user'] + ' ' + 'git -C "' + site_root_db_incremental + '" commit -m "' + get_date_time() + ' db backup" ')

	### Re-pack the git repo - ie compress to only store deltas (git does this automatically when it deems it necessary; we tell it to do it each time)
	os.system('sudo -u ' + site['linux_user'] + ' ' + 'git -C "' + site_root_db_incremental + '" add .')



	### Delete old backups
#	if (site['backup_days']):
#		prune(site_root_db_incremental, site['backup_days'])
#		prune(site_root_db_incremental_specialized, site['backup_days'])
#	else:
#		prune(site_root_db_incremental, 90)
#		prune(site_root_db_incremental_specialized, 90)

#def prune(site_nightly_root, days, linux_user = "root"):
	### Delete backup folders older than 90 days. Maxdepth - only look at the top folder structure. Mindepth - don't include the relative root (which is at depth 0) (which would delete all backups!).
	### mtime is number of days from today since the files were modified.
#	os.system('sudo -u ' + linux_user + ' ' + 'find "' + site_nightly_root + '" -mindepth 1 -maxdepth 1 -type d -mtime +' + days + ' | xargs rm -rf')
	# pipe into xargs because it is more efficient than using the find -exec command to rm

main() # run the script
