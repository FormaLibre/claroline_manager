#!/usr/bin/env python
# -*- coding: utf-8 -*-

import yaml
import os
import sys
import argparse
import datetime

	
__FILE__ = os.path.realpath(__file__)
__DIR__ = os.path.dirname(__FILE__)

with open('install.yml') as stream:
    parameters = yaml.load(stream)

claro_admin_pwd = parameters['claro_admin_pwd']
mysql_root_pwd = parameters['mysql_root_pwd']
backup_directory = __DIR__ + '/backups'
platform_dir = __DIR__ + '/platforms'
operations_dir = __DIR__ + '/operations'
permissions_script = __DIR__ + '/permissions.sh'
webserver = parameters['webserver']

help_action = """
    This script should be used as root. Be carreful.

    init:         Initialize the temporary directories for this script
    param:        Create a new file containing a platform installation parameters. \n
    create:       Create the platform datatree. \n
    install:      Install a platform. \n
    backup:       Generates a backup. \n
    remove:		  Removes a platform. \n
    update:       Update a platform (warning: be carefull of symlinks if you use them). \n  
    update-light: Update a platform without claroline:update (warning: be carefull of symlinks if you use them). \n  
    restore:      Restore a platform - not implemented yet. \n
    perm:         Fire the permission script for a platform. \n
    emain:        Enable the maintenance mode. \n
    dmain:        Remove the maintenance mode. \n
    assets:       Dump the assets. \n
    warm:         Warm the cache.\n
"""

help_nom = """
    The platform name.
"""

help_symlink = """
    The platform name you want to symlink the vendor directory (only valid for the param action).
"""

parser = argparse.ArgumentParser("Allow you to manage claroline platforms.", formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("action", help=help_action)
parser.add_argument('-n', '--name', help=help_nom)
parser.add_argument('-s', '--symlink', help=help_symlink)
args = parser.parse_args()

#############
# FUNCTIONS #
#############

def get_installed_platforms():
    platforms = []

    for subdir, dirs, files in os.walk(platform_dir):
        for file in files:
            with open(platform_dir + '/' + file) as stream:
                platforms.append(yaml.load(stream))

    return platforms

def get_installed_platform(name):
    platforms = get_installed_platforms()
    for platform in platforms:
        if platform['name'] == name:
            return platform
           
def get_child_platforms(name):
    base = get_installed_platform(name)
    if (base['base_platform'] != None):
        print 'Please run the action ' + args.action + ' on the ' + base['base_platform'] + ' instead.'
        raise Exception('The platform ' + name + ' uses ' + base['base_platform'] + ' as base with symlink.')
    
	platforms = []
	platform = get_installed_platforms()
	for platform in platforms:
		if platform['base_platform'] != None and platform['base_platform'] == name:
			platforms.append(platform)
	
	return platforms

def claroline_console(name, command):
    command = 'php ' + platform['user_home'] + 'claroline/app/console ' + command
    print command
    os.system(command)

def backup_sources(platform):
    print 'Backing up sources...'
    name = platform['name']
    date = str(datetime.datetime.now().strftime('%Y-%d-%m'))
    zip_name = name + '@' + date + '.source.zip'
    command = 'zip -r ' + backup_directory + '/' + zip_name + ' ' + platform['user_home'] + 'claroline/vendor'
    print command
    os.system(command)

def backup_files(platform):
    print 'backing up the platform files...'
    directories = ['web', 'files', 'bin', 'app']
    name = platform['name']
    date = str(datetime.datetime.now().strftime('%Y-%d-%m'))
    zip_name = name + '@' + date + '.file.zip'
    command = 'zip -r '

    for directory in directories:
        command += platform['user_home'] + 'claroline/' + directory + ' '

    exclude = '-x ' + '"' + platform['user_home'] + 'claroline/app/logs/*" ' + '"' + platform['user_home'] + 'claroline/app/cache/*" '
    command += exclude
    command += '--out ' + backup_directory + '/' + zip_name
    print command
    os.system(command)

def backup_database(platform):
    name = platform['db_name']
    date = str(datetime.datetime.now().strftime('%Y-%d-%m'))
    print 'Backing up the database for ' + name + '...'
    sql_file = name + '@' + date + '.sql'
    backup_file = backup_directory + '/' + sql_file
    command = "mysqldump --opt --databases " + name + "_prod -u " + name + " --password='" + platform['db_pwd'] + "' > " + backup_file
    print command
    os.system(command)

def update_composer(platform):
    print 'Starting composer...'
    os.chdir(platform['claroline_root'])
    os.system('composer update --prefer-dist --no-dev')
    os.system('cp app/config/operations.xml ' + 

def update_claroline(platform):
    os.chdir(platform['user_home'] + 'claroline')
    print 'Updating platform ' + platform['name'] + '...'
    print 'php ' + platform['user_home'] + 'claroline/vendor/sensio/distribution-bundle/Sensio/Bundle/DistributionBundle/Resources/bin/build_bootstrap.php'
    #claroline_console(platform, 'cache:clear')
    command = 'rm -rf ' + platform['user_home'] + 'claroline/app/cache/*'
    print command
    os.system(command)
    #claroline_console(platform, 'cache:warm')
    claroline_console(platform, 'claroline:update')
    claroline_console(platform, 'assets:install')

def update_claroline_light(platform):
    os.chdir(platform['user_home'] + 'claroline')
    print 'Updating platform ' + platform['name'] + '...'
    print 'php ' + platform['user_home'] + 'claroline/vendor/sensio/distribution-bundle/Sensio/Bundle/DistributionBundle/Resources/bin/build_bootstrap.php'
    command = 'rm -rf ' + platform['user_home'] + 'claroline/app/cache/*'
    print command
    os.system(command)

################################
# THIS IS WHERE THE FUN BEGINS #
################################

if args.action == "init":
    os.system('mkdir -p ' + backup_directory)
    os.system('mkdir -p ' + platform_dir)
    os.system('mkdir ' + __DIR__ + '/tmp')
    os.system('mkdir -p ' + operations_dir)
    #touch
    open(__DIR__ + '/.init', 'a').close()
    print 'You may want to edit the base composer file in the /skel directory.'
    print 'You might want to run this script with the check-configs action (see --help)' 
    sys.exit()
    
### CHECKS IF THE SCRIPT WAS INITIALIZED

if (not os.path.exists(__DIR__ + '/.init')):
    print 'Please initialize this script [init].'

    sys.exit()

### THE NAME IS REQUIRED FOR EVERY ACTION

if (not args.name):
	raise Exception('The platform name is required.')

### PARAM

if args.action == "param":
    if (args.symlink and not get_installed_platform(args.symlink)):
		raise Exception('The base platform ' + args.symlink + ' doesn''t exists.')
	
    db_pwd_gen = os.popen("apg -a 1 -m 25 -n 1 -MCLN").read().rstrip()
    token_gen = os.popen("apg -a 1 -m 50 -n 1 -MCLN").read().rstrip()
    ecole_admin_pwd_gen = os.popen('apg -a 0 -m 12 -x 12 -n 1 -MCLN').read().rstrip()
    data = dict(
            name = args.name,
            user_home = '/home/' + args.name + '/',
            claroline_root = '/home/' + args.name + '/claroline/',
            db_name = args.name,
            db_pwd = db_pwd_gen,
            token = token_gen,
            ecole_admin_pwd = ecole_admin_pwd_gen,
            base_platform = args.symlink
        )

    data_yaml = yaml.dump(data, explicit_start = True, default_flow_style=False)
    paramFile = open(platform_dir + "/" + args.name + ".yml", 'w+')
    paramFile.write(data_yaml)
    
    if (not args.symlink):
        print 'No symlink for ' + args.name + '.'
    else:
        print 'Symlinked to ' + args.symlink
        

### CREATE

elif args.action == "create":
    
    platform = get_installed_platform(args.name)
    # Create user and user home from skel
    cmd = "useradd --system --create-home --skel " + __DIR__ + "/skel/ " + platform["name"]
    os.system(cmd)

	# Set the web server
    if (webserver == 'apache'):
		print 'Create the apache vhost'
		input  = open(__DIR__ + "/files/vhost.conf", 'r')
		output = open("/etc/apache2/sites-available/" + platform["name"] + ".conf", 'w')
		clean  = input.read().replace("NEWUSER", platform["name"])
		output.write(clean)
		os.system("a2ensite " + platform["name"])
		
    elif args.webserver == 'nginx':
		print 'nginx is not supported yet. Please create your vhost manually or make a pr at https://github.com/FormaLibre/claroline_manager to handle this webserver.'
    else:
		print 'The webserver ' + args.webserver + ' is unknwown.'
		
    # Config DB parameters in app/config
    parameters_dist = platform["claroline_root"] + "app/config/parameters.yml.dist"
    parameters = platform["claroline_root"] + "app/config/parameters.yml"

    input  = open(parameters_dist, 'r')
    output = open(parameters, 'w')
    clean  = input.read().replace("claroline", platform["db_name"]).replace("CHANGEME", platform["db_pwd"]).replace("ThisTokenIsNotSoSecretChangeIt", platform["token"]).replace("root", platform["db_name"])
    output.write(clean)

    # Create database
    input  = open(__DIR__ + "/files/create-db.sql", 'r')
    output = open(__DIR__ + "/tmp/" + platform["name"] + ".sql", 'w')
    clean  = input.read().replace("NEWUSER", platform["db_name"]).replace("PASSWD", platform["db_pwd"])
    output.write(clean)
    mysql_cmd = "mysql -u root "
    if (mysql_root_pwd != None):
        mysql_cmd += "-p'" + mysql_root_pwd + " "
    mysql_cmd += ' -e "' + clean + '"'
    os.system(mysql_cmd)

    if (platform['base_platform'] != None):
        base = get_installed_platform(platform['base_platform'])
        os.system("ln -s " + base['claroline_root'] + "vendor " + platform["claroline_root"] + "vendor")
        os.system('cp ' + base['claroline_root'] + 'app/config/bundles.ini ' + platform["claroline_root"] + 'app/config/bundles.ini')
    else:
        print 'firing composer...'
        os.chdir(platform['claroline_root'])
        cmd = 'composer update --prefer-dist --no-dev'
        print os.system(cmd)
    
    print platform["name"] + " created !"

### INSTALL

elif args.action == "install":
    platform = get_installed_platform(args.name)
    print 'cd ' + platform['claroline_root']
    os.chdir(platform['claroline_root'])
    claroline_console(platform, "claroline:install")
    claroline_console(platform, "assets:install --symlink")
    claroline_console(platform, "assetic:dump")
    claroline_console(platform,  "claroline:user:create -a Admin Claroline clacoAdmin " + claro_admin_pwd + ' some_email')
    claroline_console(platform,  "claroline:user:create -a Admin " + platform["name"] + " " + platform["name"] + "Admin " + platform["ecole_admin_pwd"] + ' some_other_email')
    #uncomment the following line if you want to fire the permission script
    #os.system("bash " + __DIR__ + "/permissions.sh " + platform["claroline_root"]")

### BACKUP

elif args.action == 'backup':
    platforms = get_child_platforms(args.name)
    
    for platform in platforms:
        backup_files(platform)
        backup_database(platform)

    backup_sources(get_installed_platform(args.name))
    date = str(datetime.datetime.now().strftime('%Y-%d-%m'))
    os.system('mkdir -p ' + backup_directory + '/tmp/' + date)
    os.system('mv ' + backup_directory + '/tmp/*' + backup_directory + '/tmp/' + date + '/')

### UPDATE

elif args.action == 'update':
    platforms = get_child_platforms(args.name)
    base = get_installed_platform(args.name)
    
    for platform in platforms:
        claroline_console(platform, 'claroline:maintenance:enable')

    update_composer(base)

    #print 'Copying operations.xml and bundles.ini...'
    for platform in platforms:
        os.system('cp ' + base['claroline_root'] + 'app/config/operations.xml ' + platform['claroline_root'] + 'app/config/operations.xml')
        os.system('cp ' + base['user_home'] + 'app/config/bundles.ini ' + platform['claroline_root'] + 'app/config/bundles.ini')

    for platform in platforms:
        update_claroline(platform)

### UPDATE_LIGHT

elif args.action == 'update-light':
    platforms = get_child_platforms(args.name)
    base = get_installed_platform(args.name)

    for platform in platforms:
        claroline_console(platform, 'claroline:maintenance:enable')

    update_composer(base)

    #print 'Copying operations.xml and bundles.ini...'

    for platform in platforms:
        os.system('cp ' + base['claroline_root'] + 'app/config/operations.xml ' + __DIR__ + '/tmp/')
        os.system('cp ' + base['claroline_root'] + 'app/config/bundles.ini ' + platform['claroline_root'] + 'app/config/bundles.ini')

    for platform in platforms:
        update_claroline_light(platform)

### PERM

elif args.action == 'perm':
    platforms = get_child_platforms(args.name)

    for platform in platforms:
        command = 'sh ' + permissions_script + ' ' + platform['claroline_root']
        print command
        os.system(command)

### DMAIN

elif args.action == 'dmain':
    platforms = get_child_platforms(args.name)
    platforms = get_installed_platforms()

    for platform in platforms:
        claroline_console(platform, 'claroline:maintenance:disable')

### EMAIN

elif args.action == 'emain':
    platforms = get_child_platforms(args.name)
    platforms = get_installed_platforms()

    for platform in platforms:
        claroline_console(platform, 'claroline:maintenance:enable')

### ASSETS

elif args.action == 'assets':
    platforms = get_child_platforms(args.name)
    platforms = get_installed_platforms()

    for platform in platforms:
        os.chdir(platform['claroline_root'])
        claroline_console(platform, 'assets:install')  

### WARM

elif args.action == 'warm':
    platforms = get_child_platforms(args.name)
    platforms = get_installed_platforms()

    for platform in platforms:
        os.chdir(platform['claroline_root'])
        claroline_console(platform, 'cache:warm --env=prod')
        os.system('chown -R www-data:www-data app/cache')
        os.system('chmod -R 0777 app/cache')

### REMOVE

elif args.action == 'remove':
    os.system('userdel -r ' + args.name)
    #remove the database
    cmd = "mysql -u root "
    if (mysql_root_pwd != None):
        cmd += "-p'" + mysql_root_pwd + " "
    cmd += "-e 'drop database " + args.name + "_prod;drop user '" + args.name + "'@'localhost';'"
    #print 'You probably want to execute the following command manually - this script does not fire it for some reason'
    print cmd
    os.system(cmd)
    #remove the vhost
    if (webserver == 'apache'):
        if os.path.exists("/etc/apache2/sites-available/" + args.name + ".conf"):
            os.remove("/etc/apache2/sites-available/" + args.name + ".conf")
        if os.path.exists("/etc/apache2/sites-enabled/" + args.name + ".conf"): 
            os.remove("/etc/apache2/sites-enabled/" + args.name + ".conf")
    else:
        print('The server ' + args.webserver + ' is not supported yet.')
        
    #remove the platform
    if os.path.exists(platform_dir + '/' + args.name + '.yml'):
        os.remove(platform_dir + '/' + args.name + '.yml')

### RESTORE

elif args.action == 'restore':
    print 'not implemented yet'
    
### CHECK_CONFIGS

elif args.action == 'check-configs':
    base_platform = args.name
    platforms = get_installed_platforms()
    
    for platform in platforms:
        if (not 'claroline_root' in platform):
            platform['claroline_root'] = platform['user_home'] + '/claroline'
        if (not 'base_platform' in platform):
            platform['base_platform'] = args.name 
        
    data_yaml = yaml.dump(data, explicit_start = True, default_flow_style=False)
    paramFile = open(platform_dir + "/" + args.name + ".yml", 'w+')
    paramFile.write(data_yaml)

### CUSTOM

elif args.action == 'custom':
    if args.name == 'ecoles-base':
        platforms = get_installed_platforms()

        for platform in platforms:
            os.chdir(platform['claroline_root'])
            claroline_console(platform, 'DO W/E YOU WANT HERE')

else:
    print "INVALID PARAMETERS"


