#!/usr/bin/env python
# -*- coding: utf-8 -*-

import yaml
import os
import sys
import argparse
import datetime

with open('install.yml') as stream:
    parameters = yaml.load(stream)

claro_admin_pwd = parameters['claro_admin_pwd']
mysql_root_pwd = parameters['mysql_root_pwd']
backup_directory = parameters['backup_directory']
platform_dir = parameters['platform_dir']

permissions_script = os.path.dirname(os.path.abspath(__file__)) + '/permissions.sh'

help_action = """
    param:   Cree un nouveau fichier contenant les parametres d'installation d'une plateforme. \n
    create:  Genere l'arborescence de fichier d'une plateforme. \n
    install: Installe une plateforme. \n
    backup:  Genere le backup de toutes les plateforme. \n
    update:  Met a jour toutes les plateformes - attention au symlink. \n  
    restore: Restore une plateforme. \n
    perm:    Set the permissions. \n
    test:    Test si une plateforme existe. \n
    emain:   Enable the maintenance mode. \n
    dmain:   Remove the maintenance mode. \n
    assets:  Dump the assets. \n
    warm:    Warm the cache.\n
"""

help_nom = """
    Le nom de la plateforme.
"""

parser = argparse.ArgumentParser("Permet de maintenir des plateformes claroline.", formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("action", help=help_action)
parser.add_argument('-n', '--name', help=help_nom)
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
    command += backup_directory + '/' + zip_name
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
    os.chdir(platform['user_home'] + 'claroline')
    os.system('composer update --prefer-dist --no-dev')

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

######################################################################################################################################
######################################################################################################################################

###########
## PARAM ##
###########

if args.action == "param":
    if (not args.name): 
        raise Exception('Le nom de la plateforme est requis.')
    print(args)
    db_pwd_gen = os.popen("apg -a 1 -m 25 -n 1 -MCLN").read().rstrip()
    token_gen = os.popen("apg -a 1 -m 50 -n 1 -MCLN").read().rstrip()
    ecole_admin_pwd_gen = os.popen('apg -a 0 -m 12 -x 12 -n 1 -MCLN').read().rstrip()
    data = dict(
            name = args.name,
            user_home = '/home/' + args.name + '/',
            db_name = args.name,
            db_pwd = db_pwd_gen,
            token = token_gen,
            ecole_admin_pwd = ecole_admin_pwd_gen,
        )

    data_yaml = yaml.dump(data, explicit_start = True, default_flow_style=False)
    paramFile = open("plateformes/" + args.name + ".yml", 'w+')
    paramFile.write(data_yaml)

##########
# CREATE #
##########

elif args.action == "create":
    if (not args.name):
        raise Exception('Le nom de la plateforme est requis.')

    with open("plateformes/" + args.name + ".yml", 'r') as stream:
        config = yaml.load(stream)

    # create user and user home from skel

    cmd = "useradd --system --create-home --skel /root/install-script/skel/ " + config["name"]
    os.system(cmd)

    # Create apache vhost

    input  = open("/root/install-script/files/vhost.conf", 'r')
    output = open("/etc/apache2/sites-available/" + config["name"] + ".conf", 'w')
    clean  = input.read().replace("NEWUSER", config["name"])
    output.write(clean)

    os.system("a2ensite " + config["name"])
    os.system("service apache2 restart")

    # Config DB parameters in app/config

    parameters_dist = config["user_home"] + "claroline/app/config/parameters.yml.dist"
    parameters = config["user_home"] + "claroline/app/config/parameters.yml"

    input  = open(parameters_dist, 'r')
    output = open(parameters, 'w')
    clean  = input.read().replace("claroline", config["db_name"]).replace("CHANGEME", config["db_pwd"]).replace("ThisTokenIsNotSoSecretChangeIt", config["token"]).replace("root", config["db_name"])
    output.write(clean)

    # Create Database

    input  = open("/root/install-script/files/create-db.sql", 'r')
    output = open("/root/install-script/tmp/" + config["name"] + ".sql", 'w')
    clean  = input.read().replace("NEWUSER", config["db_name"]).replace("PASSWD", config["db_pwd"])
    output.write(clean)
    cmd = "mysql -u root -p'" + mysql_root_pwd + "' < /root/install-script/tmp/" + config["name"] + ".sql"
    print cmd
    print os.system(cmd)

    # Vendor link

    os.system("ln -s /home/ecoles-base/claroline/vendor " + config["user_home"] + "claroline/vendor")

    print config["name"] + " créé"

###########
# INSTALL #
###########

elif args.action == "install":
    if (not args.name):
        raise Exception('Le nom de la plateforme est requis.')

    platform = get_installed_platform(args.name)
    os.chdir(platform['user_home'] + 'claroline')
    claroline_console(platform, "claroline:install")
    claroline_console(platform, "assets:install --symlink")
    claroline_console(platform, "assetic:dump")
    claroline_console(platform,  "claroline:user:create -a Admin Claroline clacoAdmin " + claro_admin_pwd)
    claroline_console(platform,  "claroline:user:create -a Admin " + platform["name"] + " " + platform["name"] + "Admin " + platform["ecole_admin_pwd"])
    os.system("bash /root/install-script/permissions.sh " + platform["user_home"] + "claroline" )

##########
# BACKUP #
##########

elif args.action == 'backup':
    if (not args.name):
        raise Exception('Le nom de la plateforme est requis. "ecoles-base" pour toute les ecoles')

    if args.name == 'ecoles-base':
        platforms = get_installed_platforms()
        
        for platform in platforms:
            backup_files(platform)
            backup_database(platform)

        backup_sources(get_installed_platform('ecoles-base'))
        date = str(datetime.datetime.now().strftime('%Y-%d-%m'))
        os.system('mkdir /home/claroline_backup/tmp/' + date)
        os.system('mv /home/claroline_backup/tmp/* /home/claroline_backup/tmp/' + date + '/')
    else:
        platform = get_installed_platform(args.name)
        if (platform == None):
            raise Exception('La plateforme ' + args.name + ' n''existe pas')
        backup_files(platform)
        backup_database(platform)
        backup_sources(platform)

##########
# UPDATE #
##########

elif args.action == 'update':
    if (not args.name):
        raise Exception('Le nom de la plateforme est requis. "ecoles-base" pour toutes les ecoles"')

    if args.name == 'ecoles-base':
        platforms = get_installed_platforms()
        base = get_installed_platform('ecoles-base')

        for platform in platforms:
            claroline_console(platform, 'claroline:maintenance:enable')

        update_composer(base)

        print 'Copying operations.xml and bundles.ini...'

        for platform in platforms:
            os.system('cp ' + base['user_home'] + 'claroline/app/config/operations.xml ' + platform['user_home'] + 'claroline/app/config/operations.xml')
            os.system('cp ' + base['user_home'] + 'claroline/app/config/bundles.ini ' + platform['user_home'] + 'claroline/app/config/bundles.ini')

        for platform in platforms:
            update_claroline(platform)

###############
# PERMISSIONS #
###############

elif args.action == 'perm':
    if (not args.name):
        raise Exception('Le nom de la plateforme est requis. "ecoles-base" pour toutes les ecoles')
    
    if args.name == 'ecoles-base':
        platforms = get_installed_platforms()

        for platform in platforms:
            command = 'sh ' + permissions_script + ' ' + platform['user_home'] + 'claroline'
            print command
            os.system(command)

###############
# MAINTENANCE #
###############

elif args.action == 'dmain':
    if (not args.name):
        raise Exception('Le nom de la plateforme est requis. "ecoles-base" pour toutes les ecoles')

    if args.name == 'ecoles-base':
        platforms = get_installed_platforms()

        for platform in platforms:
            claroline_console(platform, 'claroline:maintenance:disable')

elif args.action == 'emain':
    if (not args.name):
        raise Exception('Le nom de la plateforme est requis. "ecoles-base" pour toutes les ecoles')

    if args.name == 'ecoles-base':
        platforms = get_installed_platforms()

        for platform in platforms:
            claroline_console(platform, 'claroline:maintenance:enable')

elif args.action == 'assets':
    if (not args.name):
        raise Exception('Le nom de la plateforme est requis. "ecoles-base" pour toutes les ecoles')
         
    if args.name == 'ecoles-base':
        platforms = get_installed_platforms()

        for platform in platforms:
            os.chdir(platform['user_home'] + 'claroline')
            claroline_console(platform, 'assets:install')  

elif args.action == 'warm':
    if (not args.name):
        raise Exception('Le nom de la plateforme est requis. "ecoles-base" pour toutes les ecoles')

    if args.name == 'ecoles-base':
        platforms = get_installed_platforms()

        for platform in platforms:
            os.chdir(platform['user_home'] + 'claroline')
            claroline_console(platform, 'assets:install')

else:
    print "Parametres incorrects"


