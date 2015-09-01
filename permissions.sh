#!/bin/bash

chown -R root:www-data $1

chmod -R 0755 $1
chmod -R 0775 $1/app/cache
chmod -R 0775 $1/app/sessions
chmod 0770 $1/app/config
chmod 0770 $1/app/config/bundles.ini
chmod 0770 $1/app/config/parameters.yml
chmod 0770 $1/app/config/platform_options.yml
chmod -R 0770 $1/app/logs
chmod 0770 $1/composer.json
chmod 0770 $1/composer.lock
chmod 0770 -R $1/files
chmod -R 0775 $1/vendor
chmod 0755 $1/web
chmod -R 0775 $1/web/bundles
chmod -R 0775 $1/web/js
chmod -R 0775 $1/web/themes
chmod -R 0775 $1/web/uploads
chmod -R 0775 $1/web/uploads/badges
chmod -R 0775 $1/web/uploads/logos
chmod -R 0775 $1/web/vendor

exit 0

