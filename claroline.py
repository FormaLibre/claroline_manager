#!/usr/bin/env python
# -*- coding: utf-8 -*-

import yaml
import os
import sys
import argparse
import datetime
import pwd

__FILE__   = os.path.realpath(__file__)
__DIR__    = os.path.dirname(__FILE__)
__DATE__   = str(datetime.datetime.now().strftime('%Y-%d-%m'))
__BACKUP__ = ['web', 'files', 'bin', 'app', 'composer.json']

with open('claroline.yml') as stream:
    parameters = yaml.load(stream)

claro_admin_pwd    = parameters['claro_admin_pwd']
claro_admin_email  = parameters['claro_admin_email']
mysql_root_pwd     = parameters['mysql_root_pwd']
backup_directory   = parameters['backup_directory']
backup_tmp         = backup_directory + '/tmp'
platform_dir       = __DIR__ + '/platforms'
operations_dir     = __DIR__ + '/operations'
permissions_script = __DIR__ + '/permissions.sh'
webserver          = parameters['webserver']
claroline_src      = parameters['claroline_src']

help_action = """
    This script should be used as root. Be carreful.

    init:          Initialize the temporary directories for this script and commit the changes of the .dist files.
    param:         Create a new file containing a platform installation parameters (see the platforms directory).
    create:        Create the platform datatree (with symlink or runs composer). This will also add a new database, a new database user, a new user and a new vhost.
    install:       Install a platform.
    build          Fires the param, create and install method for a platform.
    backup:        Generates a backup.
    remove:        Removes a platform.
    update:        Update a platform.
    update-light:  Update a platform without claroline:update.
    restore:       Restore platforms.
    migrate:       Migrate platforms.
    dist-migrate:  Migrate from a remote server.
    perm:          Fire the permission script for a platform.
    warm:          Warm the cache.
    console:       Runs a claroline console command.
    param-migrate  Build the parameters files for a migration.
    symlink        Set the symlinks for platforms file sharing.
    refresh        Refresh assets and fire assetic:dump.
    set-git-root   Ty 7.x branch -_-
"""

help_name = """
    The platform name. [all]
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

help_dismiss = """
    Doesn't do the action on the child platforms. [all]
"""

help_server = """
    A remote server. [param-migrate]
"""

help_force = """
    Force the action even if a platform is symlinked. [all]
"""

help_confirm = """
    Doesn't prompt any confirmation.
"""

help_composer = """
    Specify a composer file.
"""

parser = argparse.ArgumentParser("Allow you to manage claroline platforms.", formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("action", help=help_action)
parser.add_argument('-n', '--name', help=help_name)
parser.add_argument('-s', '--symlink', help=help_symlink)
parser.add_argument('-r', '--restore', help=help_restore)
parser.add_argument('-rm', '--remove', help=help_remove, action='store_true')
parser.add_argument('-c', '--console', help=help_console)
parser.add_argument('-nc', '--noconfirm', action='store_true', help=help_confirm)
parser.add_argument('-f', '--force', action='store_true', help=help_force)
parser.add_argument('-srv', '--srv', help=help_server)
parser.add_argument('-d', '--dismisschild', action='store_true', help=help_dismiss)
parser.add_argument('-idb', '--ignoredatabase', action='store_true')
parser.add_argument('-C', '--composer', action='store_true', help=help_composer)
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

def set_git_root(platform):
    cmd = 'mv ' + platform['user_home'] + 'claroline ' +  platform['user_home'] + 'moved'
    print (cmd)
    os.system(cmd)
    os.chdir(platform['user_home'])
    cmd = 'git clone https://github.com/claroline/Claroline.git'
    print (cmd)
    os.system(cmd)
    cmd = 'mv ' + platform['user_home'] + 'Claroline ' +  platform['claroline_root']
    os.system(cmd)
    os.chdir(platform['claroline_root'])
    cmd = 'git checkout 7.x'
    print (cmd)
    os.system(cmd)
    os.system('git checkout .')
    os.system('git config core.fileMode false')

    targets = ['vendor', 'app/config', 'web', 'files', 'app/bootstrap.php.cache']

    for target in targets:
        cmd = 'rm -rf ' + platform['claroline_root'] + target
	print(cmd)
        conf = confirm()
        if not conf:
            sys.exit()
        os.system(cmd)
        cmd = 'cp -r ' + platform['user_home'] + 'moved/' + target + ' ' + platform['claroline_root'] + target
        print(cmd)
        os.system(cmd)

def get_base_platforms(platforms):
    base = []

    for platform in platforms:
        if (platform['base_platform'] == platform['name'] or platform['base_platform'] == None):
            base.append(platform)

    return base 

def get_installed_platforms():
    platforms = []

    for subdir, dirs, files in os.walk(platform_dir):
        for file in files:
            with open(platform_dir + '/' + file) as stream:
                platform = yaml.load(stream)
                if platform:
                    platforms.append(platform)

    return platforms

def get_installed_platform(name):
    platforms = get_installed_platforms()
    for platform in platforms:
        if platform['name'] == name:
            return platform
           
def get_queried_platforms(name):
    if name == 'all':
        platforms = get_installed_platforms()
    else:
        names = name.split(",") 
        baseList  = []

        for name in names:
            base = get_installed_platform(name)
            if base:
                baseList.append(base)

        for base in baseList:
            if (base and base['base_platform'] != None and not args.force):
                print 'Please run the action ' + args.action + ' on the ' + base['base_platform'] + ' platform instead.'
                raise Exception('The platform ' + name + ' uses ' + base['base_platform'] + ' as base with symlink.')

        platforms = []
        installed = get_installed_platforms()

        if not args.dismisschild:           
            for platform in installed:
                for base in baseList:
                    if platform['base_platform'] != None and platform['base_platform'] == base['name']:
                        platforms.append(platform)

        for base in baseList:
            if not base in platforms:
                platforms.append(base)

    print 'The action ' + args.action + ' will be executed on:'    

    for platform in platforms:
        print platform['name']

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
    command = 'zip -r ' + backup_tmp + '/' + zip_name + ' vendor'
    os.system(command)

def backup_files(platform):
    name = platform['name']
    os.chdir(platform['claroline_root'])
    print 'backing up the platform files for ' + name + '...'
    zip_name = name + '@' + __DATE__ + '.file.zip'
    command = 'zip -r '
    command += backup_tmp + '/' + zip_name + ' '

    for directory in __BACKUP__:
        command += directory + ' '

    exclude = '-x ' + '"' + platform['claroline_root'] + 'app/logs" ' + '"' + platform['claroline_root'] + 'app/cache" '
    command += exclude
    os.system(command)

def backup_database(platform):
    dbName = platform['db_name']
    name = platform['name']
    print 'Backing up the database for ' + name + '...'
    sql_file = name + '@' + __DATE__ + '.sql'
    backup_file = backup_tmp + '/' + sql_file
    command = "mysqldump --no-create-db --opt " + dbName + " -u " + name + " --password='" + platform['db_pwd'] + "' > " + backup_file
    print command
    os.system(command)

def base_update(name):
    platforms = get_queried_platforms(name)
    base = get_installed_platform(name)
    
    for platform in platforms:
        claroline_console(platform, 'claroline:maintenance:enable')

    update_composer(base)

    #print 'Copying operations.xml and bundles.ini...'
    for platform in platforms:
        os.system('cp ' + base['claroline_root'] + 'app/config/previous-installed.json ' + platform['claroline_root'] + 'app/config/previous-installed.json')
        os.system('cp ' + base['claroline_root'] + 'app/config/bundles.ini ' + platform['claroline_root'] + 'app/config/bundles.ini')
        set_permissions(platform)
        
    return platforms

def update_composer(platform):
    print 'Starting composer...'
    os.chdir(platform['claroline_root'])
    os.system('COMPOSER_DISCARD_CHANGE=true composer update --prefer-source')
    os.system('npm install')
    os.system('npm run bower')
    os.system('composer build')
    os.system('rm *.gzip')

def update_claroline(platform):
    claroline_console(platform, 'assets:install')
    update_claroline_light(platform)

def update_claroline_light(platform):
    os.chdir(platform['claroline_root'])
    os.system('rm -rf app/cache/*')
    print 'Updating platform ' + platform['name'] + '...'
    print 'php ' + platform['claroline_root'] + 'vendor/sensio/distribution-bundle/Sensio/Bundle/DistributionBundle/Resources/bin/build_bootstrap.php'
    command = 'rm -rf ' + platform['claroline_root'] + 'app/cache/*'
    print command
    os.system(command)
    claroline_console(platform, 'claroline:update -vvv')
    
def make_user(platform, download = True):

    if platform['name'] in [x[0] for x in pwd.getpwall()]:
        print platform['name'] + ' user already exists'
        return

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
        #os.system("service apache2 reload")
		
    elif webserver == 'nginx':
		print 'nginx is not supported yet. Please create your vhost manually or make a pr at https://github.com/FormaLibre/claroline_manager to handle this webserver.'
    else:
		print 'The webserver ' + args.webserver + ' is unknwown.'

    if download:
        download_base(platform)
        
def download_base(platform):
    os.chdir(platform['user_home'])
    cmd = 'wget http://packages.claroline.net/releases/' + claroline_src + '/claroline-' + claroline_src + '.tar.gz'
    print cmd
    os.system(cmd)
    cmd = 'tar -xvf claroline-' + claroline_src + '.tar.gz'
    os.system(cmd)
    print cmd
    cmd = 'mv claroline-' + claroline_src + ' claroline'
    os.system(cmd)
    print cmd
	
def make_database(platform):
    # Create database
    input  = open(__DIR__ + "/files/create-db.sql", 'r')
    output = open(__DIR__ + "/tmp/" + platform["name"] + ".sql", 'w')
    clean  = input.read().replace("NEWUSER", platform["name"]).replace("PASSWD", platform["db_pwd"]).replace('NEW_DATABASE', platform['db_name'])
    output.write(clean)
    run_sql(clean)
    
def set_parameters(platform):
    cmd = 'cp ' + platform['claroline_root'] + 'app/config/parameters.yml.dist ' + platform['claroline_root'] + 'app/config/parameters.yml'
    os.system(cmd)
    parametersPath = platform['claroline_root'] + 'app/config/parameters.yml'

    with open(parametersPath, 'r') as stream:
        parameters = yaml.load(stream)
        
    #rangeKeys = yaml.load(parameters['parameters']['chosenRangeKeys'])
    parameters['parameters']['database_password'] = platform['db_pwd']
    parameters['parameters']['database_name'] = platform['db_name']
    parameters['parameters']['database_user'] = platform['name']
    parameters['parameters']['chosenRangeKeys'] = []
    data_yaml = yaml.dump(parameters, default_flow_style=False)
    paramFile = open(parametersPath, 'w')
    paramFile.write(data_yaml)
        
def set_permissions(platform):
    command = 'sh ' + permissions_script + ' ' + platform['claroline_root']
    print command
    os.system(command)

def set_symlink(platform):
    print 'Set the symlink...'
    base = get_installed_platform(platform['base_platform'])
    if not base:
        print 'Platform ' + platform['name'] + ' has no symlink defined.'
        return
    if (base['name'] == platform['name']):
        print 'Platform ' + base['name'] + ' cannot symlink itself.'
        return

    directories = ['vendor', 'web/packages', 'web/dist', 'web/themes', 'node_modules']
    os.chdir(platform['claroline_root'])

    for directory in directories:
        cmd = 'rm -rf ' + platform['claroline_root'] + directory
        print cmd
        os.system(cmd)
        cmd = 'ln -s ' + base['claroline_root'] + directory + ' ' + directory
        print cmd
        os.system(cmd)

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
    
def restore_platform(platform, folder):
    print 'Restoring the database...'
    sql = platform['name'] + '@' + folder + '.sql'
    sqlPath = backup_directory + '/' + folder + '/' + sql
    
    if (not os.path.exists(sqlPath)):
        raise Exception(sqlPath + ' does not exists.')
        
    run_sql(platform['db_name'] + ' < ' + sqlPath, False)
    os.chdir(platform['claroline_root'])
    baseFolder = backup_directory + '/' + folder
      
    if (not platform['base_platform']):
        print 'Extracting the vendor directory...'
        vendor = platform['name'] + '@' + folder + '.source.zip'
        vendorPath =  baseFolder + '/' + vendor
        os.system('unzip -q ' + vendorPath)
    else:
        set_symlink(platform)
        
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
    set_parameters(platform)
    remove_cache(platform)
    
def migrate_platform(name, folder, symlink):
    platform = param(name, symlink)
    make_user(platform)
    make_database(platform)
    restore_platform(platform, folder)

def remove_cache(platform):
    os.chdir(platform['claroline_root'])
    cachePath = 'app/cache/'
    cmd = 'rm -rf ' + cachePath + '*'
    print 'Do you want to execute ' + cmd + ' ?'
    conf = confirm()

    if conf:
        os.system(cmd)
    else:
        print 'Cache was not removed.'

def npm_build(platform):
    os.chdir(platform['claroline_root'])
    os.system('npm install')
    os.system('npm run bower')
    os.system('npm run themes')
    os.system('npm run webpack')

def remove(name):
    platform = get_installed_platform(name)
    os.system('userdel -r ' + name)
    #remove the database
    cmd = "mysql -u root"
    if (mysql_root_pwd != None):
        cmd += " -p'" + mysql_root_pwd + "'"
    cmd += " -e \"drop database \`" + platform['db_name'] + "\`;drop user '" + name + "'@'localhost';\""
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
    print 'Building param file...'
    if (symlink and not get_installed_platform(symlink)):
        raise Exception('The base platform ' + symlink + ' doesn''t exists.')
	
    db_pwd_gen = os.popen("apg -a 1 -m 25 -n 1 -MCLN").read().rstrip()
    token_gen = os.popen("apg -a 1 -m 50 -n 1 -MCLN").read().rstrip()
    ecole_admin_pwd_gen = os.popen('apg -a 0 -m 12 -x 12 -n 1 -MCLN').read().rstrip()
    data = dict(
            name = name,
            user_home = '/home/' + name + '/',
            claroline_root = '/home/' + name + '/claroline/',
            db_name = name,
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
    make_user(platform, True)
    make_database(platform)
    set_parameters(platform)

    if (platform['base_platform'] != None):
        set_symlink(platform)
        os.chdir(platform['claroline_root'])
        os.system('composer fast-install')
        refresh(platform)
    else:
        os.chdir(platform['claroline_root'])
        print os.getcwd()
        cmd = 'composer run fast-install -vvv'
	print cmd
	os.system(cmd)

    claroline_console(platform,  "claroline:user:create -a Admin Claroline clacoAdmin " + claro_admin_pwd + ' ' + claro_admin_email)
    claroline_console(platform,  "claroline:user:create -a Admin " + platform["name"] + " " + platform["name"] + "Admin " + platform["ecole_admin_pwd"] + ' some_other_email')
    set_permissions(platform)

    print platform["name"] + " created !"
    
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
        restore_platform(platform, folder)
        names.remove(name)
    
    for name in names:
        platform = get_installed_platform(name)
        restore_platform(platform, folder)
        
def migrate (folder, symlink):
    names = check_restore(folder, symlink)
    
    if (symlink):
        migrate_platform(symlink, folder, symlink)
        names.remove(symlink)
    
    for name in names:
        migrate_platform(name, folder, symlink)

def refresh(platform):
    print 'cd ' + platform['claroline_root']
    os.chdir(platform['claroline_root'])
    claroline_console(platform, "assets:install")
    claroline_console(platform, "assetic:dump")
    npm_build(platform)
    os.system("bash " + __DIR__ + "/permissions.sh " + platform["claroline_root"])

def remote_database_dump(platform):
    command = "mysqldump --verbose --opt " + platform['db_dist_name'] + " -u " + platform['name'] + " --password='" + platform['db_dist_pwd'] + "' > " + platform['name'] + '.sql'
    sshCmd = 'ssh ' + platform['remote_srv'] + ' ' + command
    print sshCmd
    os.system(sshCmd)

######################################################
# THIS IS WHERE THE FUN BEGINS: HERE ARE THE ACTIONS #
######################################################

if args.action == "init":
    os.system('mkdir -p ' + backup_directory)
    os.system('mkdir -p ' + platform_dir)
    os.system('mkdir ' + __DIR__ + '/tmp')
    os.system('mkdir -p ' + operations_dir)
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

elif args.action == 'dist-migrate':
    platforms = get_queried_platforms(args.name)

    for platform in platforms:
        make_user(platform, False)
        platformPath = __DIR__ + '/platforms/' + platform['name'] + '.yml'

        with open(platformPath, 'r') as stream:
            platform = yaml.load(stream)
        
        platform['user_home'] = '/home/' + platform['name'] + '/'
        platform['claroline_root'] = platform['user_home'] + 'claroline/'
        platform['db_name'] = platform['db_dist_name']
        platform['token'] = os.popen("apg -a 1 -m 50 -n 1 -MCLN").read().rstrip()
        data_yaml = yaml.dump(platform, default_flow_style=False)
        paramFile = open(platformPath, 'w')
        paramFile.write(data_yaml)

        dist_location = platform['remote_srv'] + ':' + platform['remote_loc']
        rsyncCmd = 'rsync --progress -e ssh -az ' + dist_location + '* ' + platform['claroline_root']
        print rsyncCmd
        os.system(rsyncCmd)
        os.system('rm ' + platform['user_home'] + 'sqldump.sql') #you may want to comment this line
        command = "mysqldump --verbose --opt " + platform['db_dist_name'] + " -u " + platform['name'] + " --password='" + platform['db_dist_pwd'] + "' > " + platform['user_home'] + 'sqldump.sql'
        sshCmd = 'ssh ' + platform['remote_srv'] + ' ' + command
        print sshCmd
        os.system(sshCmd)

        #Drop the database if it exists
        print 'Drop the database if it exists...'
        cmd = "mysql -u root"
        if (mysql_root_pwd != None):
            cmd += " -p'" + mysql_root_pwd + "'"
        cmd += " -e 'drop database if exists " + platform['db_name'] + ";drop user '" + platform['name'] + "'@'localhost';'"
        #print 'You probably want to execute the following command manually - this script does not fire it for some reason'
        print cmd
        os.system(cmd)

        #Import the database
        print 'Restoring the database...'
        make_database(platform)
        if not args.ignoredatabase:
            sqlPath = platform['user_home'] + 'sqldump.sql'
        
            if (not os.path.exists(sqlPath)):
                raise Exception(sqlPath + ' does not exists.')
            
            run_sql(platform['db_name'] + ' < ' + sqlPath, False)
        remove_cache(platform)
        set_permissions(platform)
        print 'Changes your dns to apply changes...'
        print 'Check the permissions were correct...'

    #link the vendor directory
    #for platform in platforms:
    #    if platform['base_platform']:
    #        set_symlink(platform)


### THE NAME IS REQUIRED FOR EVERY OTHER ACTION

if (not args.name):
	raise Exception('The platform name is required.')

if args.action == "param":
    param(args.name, args.symlink)

elif args.action == "create":
    create(args.name)

elif args.action == 'remove':
    platforms = get_queried_platforms(args.name)
    
    for platform in platforms:
        remove(platform['name'])
    
elif args.action == 'backup':
    platforms = get_queried_platforms(args.name)
    
    for platform in platforms:
        backup_files(platform)
        backup_database(platform)

    basePlatforms = get_base_platforms(platforms)

    for basePlatform in basePlatforms:
        backup_sources(basePlatform)

    os.system('mkdir -p ' + backup_directory + '/' + __DATE__)
    os.system('mv ' + backup_tmp + '/* ' + backup_directory + '/' + __DATE__ + '/')

elif args.action == 'update':
    platforms = base_update(args.name)

    for platform in platforms:
        update_claroline(platform)

elif args.action == 'update-light':
    platforms = base_update(args.name)

    for platform in platforms:
        update_claroline_light(platform)

elif args.action == 'perm':
    platforms = get_queried_platforms(args.name)

    for platform in platforms:
        set_permissions(platform)

elif args.action == 'set-git-root':
    platforms = get_queried_platforms(args.name)

    for platform in platforms:
        set_git_root(platform)

elif args.action == 'console':
    platforms = get_queried_platforms(args.name)

    for platform in platforms:
        os.chdir(platform['claroline_root'])
        claroline_console(platform, args.console)

elif args.action == 'warm':
    platforms = get_queried_platforms(args.name)

    for platform in platforms:
        os.chdir(platform['claroline_root'])
        claroline_console(platform, 'cache:warm --env=prod')
        os.system('chown -R www-data:www-data app/cache')
        os.system('chmod -R 0777 app/cache')

elif args.action == 'build':
    param(args.name, args.symlink)
    create(args.name)
    
elif args.action == 'param-migrate':
    print "Something may be wrong on this method. Please check the db_dist_name & pw."
    base_platform = args.name
    platforms = get_queried_platforms(args.name)
    
    for platform in platforms:
        platform['remote_loc']   = platform['claroline_root']
        platform['remote_srv']   = args.srv
        platform['db_dist_name'] = platform['db_name']
        platform['db_dist_pwd']  = platform['db_pwd']

        data_yaml = yaml.dump(platform, explicit_start = True, default_flow_style=False)
        paramFile = open(platform_dir + "/" + platform['name'] + ".yml", 'w')
        paramFile.write(data_yaml)

elif args.action == "symlink":
    platforms = get_queried_platforms(args.name)

    for platform in platforms:
        set_symlink(platform)

elif args.action == 'refresh':
    platforms = get_queried_platforms(args.name)

    for platform in platforms:
        refresh(platform)

elif args.action == 'remote-db-dump':
    platforms = get_queried_platforms(args.name)

    for platform in platforms:
        remote_database_dump(platform)

else:
    print "DONE !"
