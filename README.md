### HOW TO USE

/!\ warning: this script should be used as root for the moment /!\

#### REQUIREMENTS
- python
- apg
- zip

You can install them with apt-get

#### INSTALLATION
- clone this repository
- cp claroline.yml.dist claroline.yml 
- set a value for the claro_admin_pwd and set your mysql root password in the other field
- sudo python claroline.py init //this will create the basic directory structure
- you should check the file in skel/claroline/composer.json is correct for new installations
- python claroline.py --help //this will show you the list of available tools

#### CREATE A NEW PLATFORM
- sudo python claroline.py param --name=PLATFORM_NAME
- sudo python claroline.py create --name=PLATFORM_NAME
- sudo python claroline.py install --name=PLATFORM_NAME
- sudo service apache2 restart //this could be added to the script

#### CREATING A PLATFORM WITH SHARED VENDOR DIRECTORY
- sudo python claroline.py param --name=PLATFORM_NAME --symlink=BASE_PLATFORM
- sudo python claroline.py create --name=PLATFORM_NAME
- sudo python claroline.py install --name=PLATFORM_NAME
- sudo service apache2 restart //this could be added to the script
 
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

### TODO
- hooks
- debug
