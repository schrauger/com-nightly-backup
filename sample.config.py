sendmail = '/usr/sbin/sendmail'
email_from = 'backups@SERVER.med.ucf.edu'
email_to = ['recipient@email.com']
server = 'SERVER.med.ucf.edu'
user_read_access = 'sshuserwithreadaccess'

sites = {}

#sites['site_med_prd'] = {
#	'linux_user': "root",			# user that can read the source and write to the destination
#	'backup_root': "/var/backups/nightly",	# backup destination root directory
#	'backup_root_db_incremental': "/var/backups/db-incremental", # backup destination root directory, for incremental database script
#	'web_root': "/var/www",			# web root that contains the 'directory'
						# (this portion of the path is not recreated)
#	'directory': "med.ucf.edu/production",	# the directory to be backed up
#	'directory_specialized': "med.ucf.edu/tertiary-production", # files that are used in place of the main files, when used on the tertiary server (generally, alternative wp-config.php files)
#						# NOTE: files in here should be owned by the linux_user, readable by it. wp-config.php is usually owned by root to prevent accidental viewing, but this has to be viewable by user defined.
#	'user': "DB_USER",			# database username that has SELECT privileges
#	'password': "DB_PASSWORD",		# database password
#	'db': "DB",				# database schema name
#	'backup_days': "90",			# number of individual days to keep before pruning.
						# Script uses hardlinks, so 10 backups do not take
						# up 10x the space of a single backup, unless the
						# entire set of files changes completely
#	'user_read_access': "sshuserwithreadaccess"	# this ssh user is must be able to read all the backup files. remove parameter if not needed.
#}
sites['site_med_prd'] = {
	'linux_user': "root",
	'backup_root': "/var/backups/nightly",
	'backup_root_db_incremental': "/var/backups/db-incremental",
	'web_root': "/var/www",
	'directory': "med.ucf.edu/production",
	'directory_specialized': "med.ucf.edu/tertiary-production",
	'user': "DB_USER",
	'password': "DB_PASSWORD",
	'db': "DB",
	'backup_days': "90",
	'user_read_access': "sshuserwithreadaccess"
}
sites['site_med_dev'] = {
	'linux_user': "root",
	'backup_root': "/var/backups/nightly",
	'backup_root_db_incremental': "/var/backups/db-incremental",
	'web_root': "/var/www",
	'directory': "med.ucf.edu/dev",
	'directory_specialized': "med.ucf.edu/tertiary-dev",
	'user': "DB_DEV_USER",
	'password': "DB_DEV_PASSWORD",
	'db': "DB_DEV",
	'backup_days': "5",
	'user_read_access': "sshuserwithreadaccess"
}
