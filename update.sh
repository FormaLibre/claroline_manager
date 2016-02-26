set -e

REF=frontend

echo "Making backup of previous composer.* files"
[ -f composer.json ] && cp composer.json composer.json.bup
[ -f composer.lock ] && cp composer.json composer.json.bup

for FILE in \
  .bowerrc \
  bower.json \
  composer.json \
  composer.lock \
  npm-shrinkwrap.json \
  package.json \
  pre-update.php \
  webpack.config.js
do
  URL=https://raw.githubusercontent.com/claroline/Claroline/$REF/$FILE
  echo "Fetching $URL..."
  curl -fO $URL
done

