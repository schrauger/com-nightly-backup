#!/usr/bin/env python

import datetime
import os
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


# Backup files and database, and prune older backups
def run_backup(site):
    
    # Use a date and timestamp to create unique folders
    current_time = get_date_time()
    
    # Get the root location where all backups are stored for all sites
    # backup_root = "/var/backups/nightly"
    backup_root = site['backup_root']
    
    # Get the parent of the root location that contains the files we want to back up. Generally, "/var/www"
    # web_root = "/var/www"
    web_root = site['web_root']
    
    # Within the backup_root folder, get the root folder that contains all the nightly backups for this specific site.
    # Create a new folder for this nightly backup, for both the web files and also the database dump
    nightly_root = backup_root + '/' + site['directory']
    nightly_dir = nightly_root + '/' + current_time
    os.system('sudo -u ' + site['linux_user'] + ' ' + 'mkdir -p "' + nightly_dir + '/web"')
    os.system('sudo -u ' + site['linux_user'] + ' ' + 'mkdir -p "' + nightly_dir + '/db"')
    
    # Create same setup of folders, but specifically for the tertiary server.
    # That server will pull in all files, but have a couple files specialized for their setup.
    nightly_root_specialized = backup_root + '/' + site['directory_specialized']
    nightly_dir_specialized = nightly_root_specialized + '/' + current_time
    os.system('sudo -u ' + site['linux_user'] + ' ' + 'mkdir -p "' + nightly_dir_specialized + '/web"')
    os.system('sudo -u ' + site['linux_user'] + ' ' + 'mkdir -p "' + nightly_dir_specialized + '/db"')
    
    # Previous versions of the script used a different directory structure for the external tertiary backups.
    # Since restructuring to fit some of their requirements, the location has changed, but the old location
    # is symlinked here so their ftp sync script can continue to work until their script is updated.
    # symlink the web and db folder for backwards compatibility
    os.system('sudo -u ' + site['linux_user'] + ' '
              + 'mkdir -p "' + nightly_dir + '/unprotected"')
    os.system('sudo -u ' + site['linux_user'] + ' '
              + 'ln -sfn "' + nightly_dir_specialized + '/web/' + '" "' + nightly_dir + '/unprotected/web"')
    os.system('sudo -u ' + site['linux_user'] + ' '
              + 'ln -sfn "' + nightly_dir_specialized + '/db/' + '" "' + nightly_dir + '/unprotected/db"')
    
    # Copy with hardlinks the most recent backup to a new folder, then sync the latest with the new folder.
    #   This will save tons on filespace for files that are unchanged, but changed, added, removed files
    #   are backed up. And if an old backup gets deleted, the hardlinked duplicates aren't deleted.
    excluded_files = ' --exclude=*.sync-conflict* '  # syncthing sometimes has conflicts. don't back those up
    excluded_files += ' --exclude=sb.log '  # this file is huge and doesn't need to be backed up
    excluded_files += ' --exclude=page-caching-log.php '  # cache file
    excluded_files += ' --exclude=wphb-cache '  # cache file
    excluded_files += ' --exclude=wp-content/cache/ '  # cache file
    
    # Get most recent nightly backup directory path, excluding the one we just created:
    #   find DIR -mindepth 1 -maxdepth 1 -type d -printf '%T@ %p\n' | sort -zk 1nr | head -1 | awk '{ print $2 }'
    previous_nightly_dir = os.popen(
        'sudo -u ' + site['linux_user'] + ' '
        'find "' + nightly_root + '/" -mindepth 1 -maxdepth 1 -type d'
        ' -not -path "' + nightly_dir + '" -printf "%T@ %p\n" '
        ' | sort -nr '
        ' | head -1 '
        ' | awk \'{ print $2 }\''
    ).read().strip()
    
    if (previous_nightly_dir):
        # sync the latest changes, but reference the previous backup for hardlinks.
        # any unchanged files get a hardlink to the previous backup so they don't take up any space.
        #		print('previous found. hardlinking. to ' + previous_nightly_dir + '/web/')
        os.system(
            'sudo -u ' + site['linux_user'] + ' '
            'rsync -a --delete '
            '--link-dest="' + previous_nightly_dir + '/web/" '  # hardlink to existing previous backup
            ' "' + web_root + '/' + site['directory'] + '/" '   # source files to backup
            ' "' + nightly_dir + '/web/" ' + excluded_files     # destination where backup files go
        )
    else:
        # Our very first backup for this site!
        # we need to create a full copy that is NOT hardlinked.
        # that way, files can later change on the website without affecting our backups
        #		print('no backups. creating from scratch.')
        os.system(
            'sudo -u ' + site['linux_user'] + ' '
            'cp -a '
            ' "' + web_root + '/' + site['directory'] + '/." '  # source files to backup
            ' "' + nightly_dir + '/web/"'                       # destination where backup files go
        )
    
    # Copy with hardlinks the regular backup files to the specialized backup folder
    os.system(
        'sudo -u ' + site['linux_user'] + ' '
        'rsync -a --delete '
        '--link-dest="' + nightly_dir + '/web/" '               # hardlink to our current/new backup folder
        ' "' + web_root + '/' + site['directory'] + '/" '       # source files to backup
        ' "' + nightly_dir_specialized + '/web/" ' + excluded_files  # destination where backup files go
    )
    # Chmod all directories to be readable and executable by the user. Also chmod all files to be readable.
    # FTP user must be able to read and navigate to pull files to the tertiary backup server.
    os.system(
        'sudo -u ' + site['linux_user'] + ' '
        'find "' + nightly_dir_specialized + '" -type d -exec chmod u+rx {} + '
    )
    os.system(
        'sudo -u ' + site['linux_user'] + ' '
        'chmod -R u+r "' + nightly_dir_specialized + '"'
    )
    
    # Overwrite any web files in the specialized backup folder using the specialized source directory.
    # These alternative files are necessary for the Windows tertiary server to host our site. Notably,
    # the wp-config.php file points to other database locations and has various changes to work with IIS.
    # Since the tertiary server copies all files and deletes any that are missing, we must maintain our copy
    # of these files on our server to give to the FTP user.
    #	print('overwriting specialized files')
    os.system(
        'sudo -u ' + site['linux_user'] + ' '
        'rsync -a '
        '"' + web_root + '/' + site['directory_specialized'] + '/" '
        '"' + nightly_dir_specialized + '/web/"'
    )
    
    # Backup Production database
    # make sure there is no space between -p and the double quote
    os.system(
        'sudo -u ' + site['linux_user'] + ' '
        'mysqldump -u ' + site['user'] + " -p'" + site['password'] + "' " + site['db'] +  # credentials
        ' > "' + nightly_dir + '/db/' + site['db'] + '.sql"'                              # db dump location
    )
    
    # Link the database dump into the specialized folder so that user can access it as well
    os.system(
        'sudo -u ' + site['linux_user'] + ' '
        'ln "' + nightly_dir + '/db/' + site['db'] + '.sql" "' + nightly_dir_specialized + '/db/' + site['db'] + '.sql"'
    )
    
    # For ease of use, create a symlink directory called 'latest',
    # and point it to the backup directory we just finished.
    os.system(
        'sudo -u ' + site['linux_user'] + ' '
        'ln -sfn "' + nightly_dir + '" "' + nightly_root + '/latest"'
    )
    os.system(
        'sudo -u ' + site['linux_user'] + ' '
        'ln -sfn "' + nightly_dir_specialized + '" "' + nightly_root_specialized + '/latest"'
    )
    
    # Delete old backups.
    if (site['backup_days']):
        prune(nightly_root, site['backup_days'])
        prune(nightly_root_specialized, site['backup_days'])
    else:
        prune(nightly_root, 90)
        prune(nightly_root_specialized, 90)


# Delete folders that are older than our expiration date
def prune(site_nightly_root, days, linux_user="root"):
    # Delete backup folders older than 90 days. Maxdepth - only look at the top folder structure.
    # Mindepth - don't include the relative root (which is at depth 0) (which would delete all backups!).
    # mtime is number of days from today since the files were modified.
    os.system(
        'sudo -u ' + linux_user + ' '
        'find "' + site_nightly_root + '" -mindepth 1 -maxdepth 1 -type d -mtime +' + days +
        ' | xargs rm -rf'
    )
    # pipe into xargs because it is more efficient than using the find -exec command to rm


# Generate a string for a folder name based on the date and time
def get_date_time():
    date = datetime.datetime.today()
    return date.strftime("%Y-%m-%d_%s")


# send log email saying backups were completed
def send_email():
    sendmail_binary = config.sendmail
    email_from = config.email_from
    email_to = config.email_to
    
    email_subject = "Nightly Backup - " + config.server
    email_content = "The nightly backup for " + get_date_time() + " on " + config.server + """ completed. \n\n\
Date: """ + get_date_time() + """\n\
Server: """ + config.server
    
    message = """\
From: %s
To: %s
Subject: %s

%s
	""" % (email_from, ", ".join(email_to), email_subject, email_content)
    p = os.popen("%s -t -i" % sendmail_binary, "w")
    p.write(message)
    status = p.close()
    if status:
        print("Sendmail exit status", status)


main()  # run the script
