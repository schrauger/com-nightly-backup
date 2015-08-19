sites = {}

sites['site_med_prd'] = {
	'directory': "med.ucf.edu/production", 
	'user': "DB_USER", 
	'password': "DB_PASSWORD",
	'db': "DB",
	'backup_days': "90"
}
sites['site_med_dev'] = {
	'directory': "med.ucf.edu/dev", 
	'user': "DB_DEV_USER",
	'password': "DB_DEV_PASSWORD",
	'db': "DB_DEV",
	'backup_days': "5"
}
