sendmail = '/usr/sbin/sendmail'
email_from = 'backups@SERVER.med.ucf.edu'
email_to = ['recipient@email.com']
server = 'SERVER.med.ucf.edu'
user_read_access = 'sshuserwithreadaccess'

sites = {}

#sites['site_med_prd'] = {
#	'backup_root': "/var/backups/nightly",	# backup destination root directory
#	'web_root': "/var/www",			# web root that contains the 'directory'
						# (this portion of the path is not recreated)
#	'directory': "med.ucf.edu/production",	# the directory to be backed up
#	'user': "DB_USER",			# database username that has SELECT privileges
#	'password': "DB_PASSWORD",		# database password
#	'db': "DB",				# database schema name
#	'backup_days': "90"			# number of individual days to keep before pruning.
						# Script uses hardlinks, so 10 backups do not take
						# up 10x the space of a single backup, unless the
						# entire set of files changes completely
#}
sites['site_med_prd'] = {
	'backup_root': "/var/backups/nightly",
	'web_root': "/var/www",
	'directory': "med.ucf.edu/production",
	'user': "DB_USER",
	'password': "DB_PASSWORD",
	'db': "DB",
	'backup_days': "90"
}
sites['site_med_dev'] = {
	'backup_root': "/var/backups/nightly",
	'web_root': "/var/www",
	'directory': "med.ucf.edu/dev",
	'user': "DB_DEV_USER",
	'password': "DB_DEV_PASSWORD",
	'db': "DB_DEV",
	'backup_days': "5"
}
