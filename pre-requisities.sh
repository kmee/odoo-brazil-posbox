#!/bin/bash
set -e -x
sudo locale-gen pt_BR.UTF-8

sudo apt-get update
sudo apt-get install software-properties-common
sudo add-apt-repository "deb http://archive.ubuntu.com/ubuntu $(lsb_release -sc) universe"

sudo apt-get update

sudo apt-get install -y python-virtualenv expect-dev python-lxml \
  libxml2-dev libxslt-dev gcc python2.7-dev libevent-dev libsasl2-dev \
  libldap2-dev libpq-dev libpng12-dev libjpeg-dev sudo supervisor git \
  curl wget postgresql

ODOO_USER=odoo
ODOO_DIR=/opt/odoo

if id -u $ODOO_USER &> /dev/null; then
        echo "Usuario existe:" $ODOO_USER
else
        sudo adduser --system --shell=/bin/bash --home=$ODOO_DIR --group $ODOO_USER
        sudo adduser odoo dialout
        sudo -u postgres createuser --createdb --no-createrole --superuser $ODOO_USER
        sudo -u postgres createdb $ODOO_USER
fi
if [ ! -d "$ODOO_DIR" ]; then
        sudo mkdir -p $ODOO_DIR
        sudo chown $ODOO_USER:$ODOO_USER $ODOO_DIR
fi

sudo -H -u $ODOO_USER bash -c 'cd /opt/odoo && git clone https://github.com/kmee/odoo-brazil-posbox.git -b udev-rules'
sudo cp $ODOO_DIR/odoo-brazil-posbox/90-posbox.rules /etc/udev/rules.d/
sudo cp $ODOO_DIR/odoo-brazil-posbox/odoo-supervisor.conf /etc/supervisor/conf.d/odoo.conf
sudo -H -u $ODOO_USER bash -c 'cd /opt/odoo/odoo-brazil-posbox && bash init-buildout.sh'

sudo supervisorctl reread
sudo supervisorctl update

sudo supervisorctl restart odoo
