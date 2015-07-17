#!/usr/bin/python

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
		run_backup(sites[site])
	return 0

def run_backup(site):
	current_time = get_date_time()
	backup_root = "/var/backups"
	web_root = "/var/www"
	nightly_root = backup_root + '/' + site['directory']
	nightly_dir = nightly_root + '/' + current_time

	print nightly_dir
	os.system('mkdir -p "' + nightly_dir + '"')
	os.system('mkdir -p "' + nightly_dir + '/web"')
	os.system('mkdir -p "' + nightly_dir + '/db"')

	### Chmod. Only root can read or write.
	os.system('chmod -R 0700 "' + nightly_dir + '"')

	### Copy COM Production (entire WP directory. more reliable recovery, especially if WP is updated)
	os.system('cp -a "' + web_root + '/' + site['directory'] + '/." "' + nightly_dir + '/web/"')
	### Backup COM Production database
	# make sure there is no space between -p and the double quote
	os.system('mysqldump -u ' + site['user'] + ' -p"' + site['password'] + '" ' + site['db'] + ' > "' + nightly_dir + '/db/' + site['db'] + '"')

def prune(site):
	### Delete backup folders older than 90 days. Maxdepth - only look at the top folder structure. Mindepth - don't include the relative root (which is at depth 0) (which would delete all backups!).
	### mtime is number of days from today since the files were modified.
	os.system('find "$nightly_root" -mindepth 1 -maxdepth 1 -type d -mtime +90 | xargs rm -rf')
	# pipe into xargs because it is more efficient than using the find -exec command to rm

def get_date_time():
    date = datetime.datetime.today()
    return date.strftime("%Y-%m-%d_%s")


main() # run the script