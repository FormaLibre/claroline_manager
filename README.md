### HOW TO USE

/!\ warning: this script should be used as root for the moment /!\

#### REQUIREMENTS
- python (v2+) && python-yaml
- apg
- zip
- git
- ssh (optionnaly)

You can install them with apt-get

#### INSTALLATION
- git clone https://github.com/FormaLibre/claroline_manager.git
- cp claroline.yml.dist claroline.yml 
- set a value for the claro_admin_pwd and set your mysql root password in the other field
- sudo python claroline.py init //this will create the basic directory structure
- you should check the file in skel/claroline/composer.json is correct for new installations
- python claroline.py --help //this will show you the list of available tools

#### CREATE A NEW PLATFORM
- sudo python claroline.py build --name=PLATFORM_NAME [--symlink=BASE_PLATFORM]
- sudo service apache2 restart //you can uncommented the line in the script if you want to but it is discouraged

#### CUSTOMIZING INSTALLATION
- edit the platform_options.yml.dist and masters.yml.dist file and run the init command. 

#### ADDING A PLATFORM TO THE MANAGED PLATFORMS
- cp platform.yml.dist /platforms/PLATFORM_NAME.yml
- set the required values (claroline_root, db_name, db_pwd, name - the others aren't required)

#### UPDATING 
- sudo python claroline.py update --name=PLATFORM_NAME

#### BACKUP
- sudo python claroline.py backup --name=PLATFORM_NAME

#### REMOVE
- sudo python claroline.py remove --name=PLATFORM_NAME

#### RESTORE
- sudo python claroline.py restore --restore=FOLDER [--symlink=BASE_PLATFORM] [-rm]

#### MIGRATE
- sudo python claroline.py migrate --restore=FOLDER [--symlink=BASE_PLATFORM]

#### DIST MIGRATE (requires root account)
- sudo su
- ssh-agent /bin/bash
- ssh-add /path/to/key
- python claroline.py dist-migrate --name=PLATFORM_NAME [--symlink=BASE_PLATFORM]

### TODO
- hooks
- autocomplete
