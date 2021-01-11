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
	#backup_root = "/var/backups/nightly"
	backup_root = site['backup_root']
	#web_root = "/var/www"
	web_root = site['web_root']
	nightly_root = backup_root + '/' + site['directory']
	nightly_dir = nightly_root + '/' + current_time
	os.system('sudo -u ' + site['linux_user'] + ' ' + 'mkdir -p "' + nightly_dir + '/web"')
	os.system('sudo -u ' + site['linux_user'] + ' ' + 'mkdir -p "' + nightly_dir + '/db"')
	os.system('sudo -u ' + site['linux_user'] + ' ' + 'ln -sfn "' + nightly_dir + '" "' + nightly_root + '/latest"')

	### Chmod. Only root can read or write. However, the execute bit is set to others can traverse the path if they know the location.
	### This is used by the user_read_access user with ACL read access for all backups.
	os.system('sudo -u ' + site['linux_user'] + ' ' + 'chmod -R 0711 "' + nightly_dir + '"')
	try:
		site['user_read_access']
		os.system('sudo -u ' + site['linux_user'] + ' ' + 'setfacl -R -m user:' + site['user_read_access'] + ':rX ' + nightly_dir) # set permission for folder
		os.system('sudo -u ' + site['linux_user'] + ' ' + 'setfacl -R -d -m user:' + site['user_read_access'] + ':rX ' + nightly_dir) # set default for new files and subfolders
	except KeyError:
		print "No user configured for read access. Continuing with backup."

	### Copy with hardlinks the most recent backup to a new folder, then sync the latest with the new folder.
	###   This will save tons on filespace for files that are unchanged, but changed, added, removed files
	###   are backed up. And if an old backup gets deleted, the hardlinked duplicates aren't deleted.
	# Get most recent directory path: find DIR -mindepth 1 -maxdepth 1 -type d -printf '%T@ %p\n' | sort -zk 1nr | head -1 | awk '{ print $2 }'
	previous_nightly_dir = os.popen('sudo -u ' + site['linux_user'] + ' ' + 'find "' + nightly_root + '/" -mindepth 1 -maxdepth 1 -type d -not -path "' + nightly_dir + '" -printf "%T@ %p\n" | sort -nr | head -1 | awk \'{ print $2 }\'').read().strip()
	if (previous_nightly_dir):
		os.system('sudo -u ' + site['linux_user'] + ' ' + 'rsync -a --delete --link-dest="' + previous_nightly_dir + '/web" "' + web_root + '/' + site['directory'] + '/" "' + nightly_dir + '/web/"')
	else:
		os.system('sudo -u ' + site['linux_user'] + ' ' + 'cp -a "' + web_root + '/' + site['directory'] + '/." "' + nightly_dir + '/web/"')

	### Move protected files into their own folder. Mainly because the COMIT script crashes if it tries to read these files (it can't skip files that it sees but lacks permission to read)
	for protected_file in site['protected_files']:
		# get the relative path of the file based on the string
		protected_path = os.path.dirname(protected_file)
		protected_path_full_origin = nightly_dir + '/web/' + protected_path
		protected_path_full_destination = nightly_dir + '/protected/' + protected_path
		print(protected_path_full_origin + protected_file)
		print(protected_path_full_destination + protected_file)
		os.system('sudo -u ' + site['linux_user'] + ' ' + 'mkdir -p "' + protected_path_full_destination + '"')
		os.system('sudo -u ' + site['linux_user'] + ' ' + 'mv -f "' + protected_path_origin + protected_file + '" "' + protected_path_destination + protected_file + '"')

	### Backup COM Production database
	# make sure there is no space between -p and the double quote
	os.system('sudo -u ' + site['linux_user'] + ' ' + 'mysqldump -u ' + site['user'] + " -p'" + site['password'] + "' " + site['db'] + ' > "' + nightly_dir + '/db/' + site['db'] + '.sql"')

	### Delete old backups
	if (site['backup_days']):
		prune(nightly_root, site['backup_days'])
	else:
		prune(nightly_root, 90)

def prune(site_nightly_root, days, linux_user = "root"):
	### Delete backup folders older than 90 days. Maxdepth - only look at the top folder structure. Mindepth - don't include the relative root (which is at depth 0) (which would delete all backups!).
	### mtime is number of days from today since the files were modified.
	os.system('sudo -u ' + linux_user + ' ' + 'find "' + site_nightly_root + '" -mindepth 1 -maxdepth 1 -type d -mtime +' + days + ' | xargs rm -rf')
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
