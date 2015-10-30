#!/usr/bin/env python
# -*- coding: utf-8 -*-

import yaml
import os
import sys
import argparse
import datetime

__FILE__   = os.path.realpath(__file__)
__DIR__    = os.path.dirname(__FILE__)
__DATE__   = str(datetime.datetime.now().strftime('%Y-%d-%m'))
__BACKUP__ = ['web', 'files', 'bin', 'app']

with open('claroline.yml') as stream:
    parameters = yaml.load(stream)

claro_admin_pwd    = parameters['claro_admin_pwd']
mysql_root_pwd     = parameters['mysql_root_pwd']
backup_directory   = __DIR__ + '/backups'
backup_tmp         = backup_directory + '/tmp'
platform_dir       = __DIR__ + '/platforms'
operations_dir     = __DIR__ + '/operations'
permissions_script = __DIR__ + '/permissions.sh'
webserver          = parameters['webserver']

help_action = """
    This script should be used as root. Be carreful.

    init:          Initialize the temporary directories for this script. \n
    param:         Create a new file containing a platform installation parameters (see the platforms directory). \n
    create:        Create the platform datatree (with symlink or runs composer). This will also add a new database, a new database user, a new user and a new vhost.\n
    install:       Install a platform. \n
    build          Fires the param, create and install method for a platform. \n
    backup:        Generates a backup. \n
    remove:	   Removes a platform. \n
    update:        Update a platform (warning: be carefull of symlinks if you use them). \n  
    update-light:  Update a platform without claroline:update (warning: be carefull of symlinks if you use them). \n  
    restore:       Restore platforms. \n
    migrate:       Migrate platforms. \n
    perm:          Fire the permission script for a platform. \n
    warm:          Warm the cache.\n
    console:       Runs a claroline console command.\n
"""

help_name = """
    The platform name.
"""

help_symlink = """
    The platform name you want to symlink the vendor directory [param][build][restore][migrate].
"""

help_restore = """
    The folder you want to restore in [restore][migrate].
"""

help_remove = """
    Remove before restoring [restore].
"""

help_console = """
    Fires a claroline console command [console].
"""

parser = argparse.ArgumentParser("Allow you to manage claroline platforms.", formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("action", help=help_action)
parser.add_argument('-n', '--name', help=help_name)
parser.add_argument('-s', '--symlink', help=help_symlink)
parser.add_argument('-r', '--restore', help=help_restore)
parser.add_argument('-rm', '--remove', help=help_remove, action='store_true')
parser.add_argument('-c', '--console', help=help_console)
parser.add_argument('-nc', '--noconfirm', action='store_true')
args = parser.parse_args()

#############
# FUNCTIONS #
#############

def confirm(prompt=None, resp=False):  
    if (args.noconfirm):
        return True
      
    if prompt is None:
        prompt = 'Confirm'

    if resp:
        prompt = '%s [%s]|%s: ' % (prompt, 'y', 'n')
    else:
        prompt = '%s [%s]|%s: ' % (prompt, 'n', 'y')
        
    while True:
        ans = raw_input(prompt)
        if not ans:
            return resp
        if ans not in ['y', 'Y', 'n', 'N']:
            print 'please enter y or n.'
            continue
        if ans == 'y' or ans == 'Y':
            return True
        if ans == 'n' or ans == 'N':
            return False

def run_sql(instructions, plainText = True):
    mysql_cmd = "mysql -u root "
    if (mysql_root_pwd != None):
        mysql_cmd += "-p'" + mysql_root_pwd + "' "
    
    if plainText:
        mysql_cmd += '-e "' + instructions + '"'
    else:
        mysql_cmd += instructions
        
    print(mysql_cmd)
    os.system(mysql_cmd)

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
        print 'Please run the action ' + args.action + ' on the ' + base['base_platform'] + ' platform instead.'
        raise Exception('The platform ' + name + ' uses ' + base['base_platform'] + ' as base with symlink.')

    platforms = []
    names = []
    installed = get_installed_platforms()
    
    print 'The action ' + args.action + ' will be executed on:'
    print name

    for platform in installed:
        if platform['base_platform'] != None and platform['base_platform'] == name:
            platforms.append(platform)
            print platform['name']

    platforms.append(base)
    conf = confirm()
    
    if not conf:
        sys.exit()
    
    return platforms

def claroline_console(platform, command):
    command = 'php ' + platform['claroline_root'] + 'app/console ' + command
    print command
    os.system(command)

def backup_sources(platform):
    name = platform['name']
    os.chdir(platform['claroline_root'])
    print 'Backing up sources for ' + name +'...'
    zip_name = name + '@' + __DATE__ + '.source.zip'
    command = 'zip -r -q ' + backup_directory + '/' + __DATE__ + '/' + zip_name + ' vendor'
    print command
    os.system(command)

def backup_files(platform):
    name = platform['name']
    os.chdir(platform['claroline_root'])
    print 'backing up the platform files for ' + name + '...'
    zip_name = name + '@' + __DATE__ + '.file.zip'
    command = 'zip -r -q '
    command += backup_directory + '/' + __DATE__ + '/' + zip_name + ' '

    for directory in __BACKUP__:
        command += directory + ' '

    exclude = '-x app/logs app/cache'
    command += exclude
    print command
    os.system(command)

def backup_database(platform):
    name = platform['name']
    print 'Backing up the database for ' + name + '...'
    sql_file = name + '@' + __DATE__ + '.sql'
    backup_file = backup_directory + '/' + __DATE__ + '/' + sql_file
    command = "mysqldump --opt --databases " + platform['db_name'] + " -u " + name + " --password='" + platform['db_pwd'] + "' > " + backup_file
    print command
    os.system(command)

def base_update(name):
    platforms = get_child_platforms(name)
    base = get_installed_platform(name)
    
    for platform in platforms:
        claroline_console(platform, 'claroline:maintenance:enable')

    update_composer(base)

    #print 'Copying operations.xml and bundles.ini...'
    for platform in platforms:
        os.system('cp ' + base['claroline_root'] + 'app/config/operations.xml ' + platform['claroline_root'] + 'app/config/operations.xml')
        os.system('cp ' + base['claroline_root'] + 'app/config/bundles.ini ' + platform['claroline_root'] + 'app/config/bundles.ini')
        
    return platforms

def update_composer(platform):
    print 'Starting composer...'
    os.chdir(platform['claroline_root'])
    os.system('composer update --prefer-dist --no-dev')
    os.system('cp app/config/operations.xml ' + operations_dir + '/operations-' + args.name + '-' + __DATE__ + '.yml')

def update_claroline(platform):
    update_claroline_light(platform)
    #claroline_console(platform, 'cache:warm')
    claroline_console(platform, 'claroline:update')
    claroline_console(platform, 'assets:install')

def update_claroline_light(platform):
    os.chdir(platform['claroline_root'])
    print 'Updating platform ' + platform['name'] + '...'
    print 'php ' + platform['claroline_root'] + 'vendor/sensio/distribution-bundle/Sensio/Bundle/DistributionBundle/Resources/bin/build_bootstrap.php'
    command = 'rm -rf ' + platform['claroline_root'] + 'app/cache/*'
    print command
    os.system(command)
    
def make_user(platform):
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
        os.system("service apache2 reload")
		
    elif webserver == 'nginx':
		print 'nginx is not supported yet. Please create your vhost manually or make a pr at https://github.com/FormaLibre/claroline_manager to handle this webserver.'
    else:
		print 'The webserver ' + args.webserver + ' is unknwown.'
        
def make_database(platform):
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
    run_sql(clean)
    
def check_restore(folder, symlink):
    restoreFolder = backup_directory + '/' + folder

    if (not os.path.isdir(restoreFolder)):
        raise Exception(restoreFolder + ' is not a directory.')
        
    items = os.listdir(restoreFolder)
    platforms = []
    
    print 'Proceed to the restoration for ?'
    
    for item in items:
        platform = item.partition("@")[0]
        if not platform in platforms:
            platforms.append(platform)
            
    print platforms
    conf = confirm()
    
    if (not conf):
        print 'Restoration cancelled.'
        sys.exit()
    else:
        print 'Restoration started.'
        
    return platforms
    
def restore_platform(platform, folder, symlink):
    print 'Restoring the database...'
    sql = platform['name'] + '@' + folder + '.sql'
    sqlPath = backup_directory + '/' + folder + '/' + sql
    
    if (not os.path.exists(sqlPath)):
        raise Exception(sqlPath + ' does not exists.')
        
    run_sql('< ' + sqlPath, False)
    os.chdir(platform['claroline_root'])
    baseFolder = backup_directory + '/' + folder
      
    if (symlink == None or platform['name'] == symlink):
        print 'Extracting the vendor directory...'
        vendor = platform['name'] + '@' + folder + '.source.zip'
        vendorPath =  baseFolder + '/' + vendor
        os.system('unzip -q ' + vendorPath)
    else:
        print 'Symlinking the vendor directory...'
        base = get_installed_platform(symlink)
        os.system("ln -s " + base['claroline_root'] + "vendor " + platform["claroline_root"] + "vendor")
        os.system('cp ' + base['claroline_root'] + 'app/config/bundles.ini ' + platform["claroline_root"] + 'app/config/bundles.ini')
        
    print 'Extracting the saved files...'
    files = platform['name'] + '@' + folder + '.file.zip'
    filesPath = baseFolder + '/' + files
    
    os.chdir(platform['claroline_root'])
    
    #if (platform['claroline_root'] == '/' or platform == None):
    #    Raise Exception("we're doing rm -rf so it better be a existing directory...")
    
    #for directory in __BACKUP__:
    #    os.system('rm -rf ' + directory')
    
    os.system('unzip -o ' + filesPath)
    
    print 'Adding the correct database identifiers in parameters.yml...' 
    parametersPath = platform['claroline_root'] + 'app/config/parameters.yml'

    with open(parametersPath, 'r') as stream:
        parameters = yaml.load(stream)
        
    parameters['parameters']['database_password'] = platform['db_pwd']
    data_yaml = yaml.dump(parameters, explicit_start = True, default_flow_style=False)
    paramFile = open(parametersPath, 'w+')
    paramFile.write(data_yaml)
        
    print 'Clearing cache and other stuff...'
    paramFile = open(parametersPath + ".yml", 'w')
    paramFile.write(data_yaml)
    
def migrate_platform(name, folder, symlink):
    platform = param(name, symlink)
    make_user(platform)
    make_database(platform)
    restore_platform(platform, folder, symlink)

def remove(name):
    os.system('userdel -r ' + name)
    #remove the database
    cmd = "mysql -u root"
    if (mysql_root_pwd != None):
        cmd += " -p'" + mysql_root_pwd + "'"
    cmd += " -e 'drop database " + name + "_prod;drop user '" + name + "'@'localhost';'"
    #print 'You probably want to execute the following command manually - this script does not fire it for some reason'
    print cmd
    os.system(cmd)
    #remove the vhost
    if (webserver == 'apache'):
        if os.path.exists("/etc/apache2/sites-available/" + name + ".conf"):
            os.remove("/etc/apache2/sites-available/" + name + ".conf")
        os.system("a2dissite " + name)
    else:
        print('The server ' + webserver + ' is not supported yet.')
        
    #remove the platform
    if os.path.exists(platform_dir + '/' + name + '.yml'):
        os.remove(platform_dir + '/' + name + '.yml')

def param(name, symlink):
    if (symlink and not get_installed_platform(symlink)):
        raise Exception('The base platform ' + symlink + ' doesn''t exists.')
	
    db_pwd_gen = os.popen("apg -a 1 -m 25 -n 1 -MCLN").read().rstrip()
    token_gen = os.popen("apg -a 1 -m 50 -n 1 -MCLN").read().rstrip()
    ecole_admin_pwd_gen = os.popen('apg -a 0 -m 12 -x 12 -n 1 -MCLN').read().rstrip()
    data = dict(
            name = name,
            user_home = '/home/' + name + '/',
            claroline_root = '/home/' + name + '/claroline/',
            db_name = name + '_prod',
            db_pwd = db_pwd_gen,
            token = token_gen,
            ecole_admin_pwd = ecole_admin_pwd_gen,
            base_platform = symlink
        )

    data_yaml = yaml.dump(data, explicit_start = True, default_flow_style=False)
    paramFile = open(platform_dir + "/" + name + ".yml", 'w+')
    paramFile.write(data_yaml)
    
    if (not args.symlink):
        print 'No symlink for ' + name + '.'
    else:
        print 'Symlinked to ' + symlink + '.'
        
    return data
    
def create(name):
    platform = get_installed_platform(name)
    make_user(platform)
    make_database(platform)

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
    
def install(name):
    platform = get_installed_platform(name)
    print 'cd ' + platform['claroline_root']
    os.chdir(platform['claroline_root'])
    claroline_console(platform, "claroline:install")
    claroline_console(platform, "assets:install --symlink")
    claroline_console(platform, "assetic:dump")
    claroline_console(platform,  "claroline:user:create -a Admin Claroline clacoAdmin " + claro_admin_pwd + ' some_email')
    claroline_console(platform,  "claroline:user:create -a Admin " + platform["name"] + " " + platform["name"] + "Admin " + platform["ecole_admin_pwd"] + ' some_other_email')
    #uncomment the following line if you want to fire the permission script
    #os.system("bash " + __DIR__ + "/permissions.sh " + platform["claroline_root"]")
    operationsPath = platform['claroline_root'] + 'app/config/operations.xml'
    
    if os.path.exists(operationsPath):
        os.remove(operationsPath)
        
def restore(folder, symlink):
    names = check_restore(folder, symlink)
    
    if (args.remove):
        print 'This will remove the following platforms:'
        print names
        conf = confirm()
        
        if (not conf):
            sys.exit()
        
        if (symlink):
            remove(symlink)
            migrate_platform(symlink, folder, symlink)
            names.remove(symlink)
        
        for name in names:
            remove(name)
            migrate_platform(name, folder, symlink)
            
        sys.exit()
                
    if (symlink):
        platform = get_installed_platform(symlink)
        restore_platform(platform, folder, symlink)
        names.remove(name)
    
    for name in names:
        platform = get_installed_platform(name)
        restore_platform(platform, folder, symlink)
        
def migrate (folder, symlink):
    names = check_restore(folder, symlink)
    
    if (symlink):
        migrate_platform(symlink, folder, symlink)
        names.remove(symlink)
    
    for name in names:
        migrate_platform(name, folder, symlink)
    
######################################################
# THIS IS WHERE THE FUN BEGINS: HERE ARE THE ACTIONS #
######################################################

if args.action == "init":
    os.system('mkdir -p ' + backup_directory)
    os.system('mkdir -p ' + platform_dir)
    os.system('mkdir ' + __DIR__ + '/tmp')
    os.system('mkdir -p ' + operations_dir)
    os.system('cp ' + __DIR__ + '/platform_options.yml.dist ' + __DIR__ + '/skel/claroline/app/config/platform_options.yml')
    os.system('cp ' + __DIR__ + '/masters.yml.dist ' + __DIR__ + '/skel/claroline/app/config/masters.yml')
    os.system('cp ' + __DIR__ + '/vhost.conf.dist ' + __DIR__ + '/files/vhost.conf')
    #touch
    open(__DIR__ + '/.init', 'a').close()
    print 'You may want to edit the base composer file in the /skel directory.'
    print 'You might want to run this script with the check-configs action (see --help)' 
    print 'You might need to set up a github authentication token during the install or update operations the first time'
    sys.exit()
    
### CHECKS IF THE SCRIPT WAS INITIALIZED

if (not os.path.exists(__DIR__ + '/.init')):
    print 'Please initialize this script [init].'
    sys.exit()
    
elif args.action == 'restore':
    if (not args.restore):
        raise Exception('The restoration folder is required (--restore=RESTORE_FOLDER).')
    restore(args.restore, args.symlink)
    
elif args.action == 'migrate':
    if (not args.restore):
        raise Exception('The restoration folder is required (--restore=RESTORE_FOLDER).')
    migrate(args.restore, args.symlink)
    sys.exit()
    
### THE NAME IS REQUIRED FOR EVERY OTHER ACTION

if (not args.name):
	raise Exception('The platform name is required.')

if args.action == "param":
    param(args.name, args.symlink)
    
elif args.action == "create":
    create(args.name)

elif args.action == "install":
    install(args.name)
    
elif args.action == 'remove':
    platforms = get_child_platforms(args.name)
    
    for platform in platforms:
        remove(args.name)
    
elif args.action == 'backup':
    platforms = get_child_platforms(args.name)
    os.system('mkdir -p ' + backup_directory + '/' + __DATE__)
    
    for platform in platforms:
        backup_files(platform)
        backup_database(platform)

    backup_sources(get_installed_platform(args.name))

elif args.action == 'update':
    platforms = base_update(args.name)

    for platform in platforms:
        update_claroline(platform)

elif args.action == 'update-light':
    platforms = base_update(args.name)

    for platform in platforms:
        update_claroline_light(platform)

elif args.action == 'perm':
    platforms = get_child_platforms(args.name)

    for platform in platforms:
        command = 'sh ' + permissions_script + ' ' + platform['claroline_root']
        print command
        os.system(command)

elif args.action == 'console':
    platforms = get_child_platforms(args.name)

    for platform in platforms:
        os.chdir(platform['claroline_root'])
        claroline_console(platform, args.console)

elif args.action == 'warm':
    platforms = get_child_platforms(args.name)

    for platform in platforms:
        os.chdir(platform['claroline_root'])
        claroline_console(platform, 'cache:warm --env=prod')
        os.system('chown -R www-data:www-data app/cache')
        os.system('chmod -R 0777 app/cache')

elif args.action == 'build':
    param(args.name, args.symlink)
    create(args.name)
    install(args.name)
    
elif args.action == 'check-configs':
    base_platform = args.name
    platforms = get_installed_platforms()
    
    for platform in platforms:
        if (not 'claroline_root' in platform):
            platform['claroline_root'] = platform['user_home'] + 'claroline/'
        if (not 'base_platform' in platform):
            if (platform['name'] == args.name):
                platform['base_platform'] = None
            else:
                platform['base_platform'] = args.name 
        
        data_yaml = yaml.dump(platform, explicit_start = True, default_flow_style=False)
        paramFile = open(platform_dir + "/" + platform['name'] + ".yml", 'w')
        paramFile.write(data_yaml)

else:
    print "INVALID PARAMETERS"


