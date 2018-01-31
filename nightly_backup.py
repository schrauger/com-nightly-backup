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
	send_email()
	return 0

def run_backup(site):
	current_time = get_date_time()
	backup_root = "/var/backups/nightly"
	web_root = "/var/www"
	nightly_root = backup_root + '/' + site['directory']
	nightly_dir = nightly_root + '/' + current_time

	os.system('mkdir -p "' + nightly_dir + '"')
	os.system('mkdir -p "' + nightly_dir + '/web"')
	os.system('mkdir -p "' + nightly_dir + '/db"')
	os.system('ln -sf "' + nightly_dir + '" "' + nightly_root + '/latest"')

	### Chmod. Only root can read or write.
	os.system('chmod -R 0700 "' + nightly_dir + '"')

	### Copy with hardlinks the most recent backup to a new folder, then sync the latest with the new folder.
	###   This will save tons on filespace for files that are unchanged, but changed, added, removed files
	###   are backed up. And if an old backup gets deleted, the hardlinked duplicates aren't deleted.
	# Get most recent directory path: find DIR -mindepth 1 -maxdepth 1 -type d -printf '%T@ %p\n' | sort -zk 1nr | head -1 | awk '{ print $2 }'
	previous_nightly_dir = os.popen('find "' + nightly_root + '/" -mindepth 1 -maxdepth 1 -type d -not -path "' + nightly_dir + '" -printf "%T@ %p\n" | sort -nr | head -1 | awk \'{ print $2 }\'').read().strip()
	if (previous_nightly_dir):
		os.system('rsync -a --delete --link-dest="' + previous_nightly_dir + '/web" "' + web_root + '/' + site['directory'] + '/" "' + nightly_dir + '/web/"')
	else:
		os.system('cp -a "' + web_root + '/' + site['directory'] + '/." "' + nightly_dir + '/web/"')
	
	### Backup COM Production database
	# make sure there is no space between -p and the double quote
	os.system('mysqldump -u ' + site['user'] + ' -p"' + site['password'] + '" ' + site['db'] + ' > "' + nightly_dir + '/db/' + site['db'] + '.sql"')

	### Delete old backups
	if (site['backup_days']):
		prune(nightly_root, site['backup_days'])
	else:
		prune(nightly_root, 90)
	
def prune(site_nightly_root, days):
	### Delete backup folders older than 90 days. Maxdepth - only look at the top folder structure. Mindepth - don't include the relative root (which is at depth 0) (which would delete all backups!).
	### mtime is number of days from today since the files were modified.
	os.system('find "' + site_nightly_root + '" -mindepth 1 -maxdepth 1 -type d -mtime +' + days + ' | xargs rm -rf')
	# pipe into xargs because it is more efficient than using the find -exec command to rm

def get_date_time():
    date = datetime.datetime.today()
    return date.strftime("%Y-%m-%d_%s")

# send log email saying backups were completed
def send_email():
	SENDMAIL = config.sendmail
	FROM = config.email_from
	TO = config.email_to

	SUBJECT = "Nightly Backup - " + config.server
	TEXT = "The nightly backup for " + get_date_time() + " on " + config.server + """ completed. \n\n\
Date: """ + get_date_time() + """\n\
Server: """ + config.server

	message = """\
From: %s
To: %s
Subject: %s

%s
	""" % (FROM, ", ".join(TO), SUBJECT, TEXT)
	p = os.popen("%s -t -i" %SENDMAIL, "w")
	p.write(message)
	status = p.close()
	if status:
		print "Sendmail exit status", status

main() # run the script
