#!/bin/bash
sudo locale-gen pt_BR.UTF-8

REPO_UNIVERSE=$(grep universe /etc/apt/sources.list|wc -l)
if [ $REPO_UNIVERSE -eq 0 ] ; then
	sudo -H -u root bash -c 'echo "deb http://archive.ubuntu.com/ubuntu/ xenial universe" >> /etc/apt/souces.list'
fi

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
fi
if [ ! -d "$ODOO_DIR" ]; then
        sudo mkdir -p $ODOO_DIR
        sudo chown $ODOO_USER:$ODOO_USER $ODOO_DIR
fi
clear
sudo -H -u odoo bash -c 'cd /opt/odoo && git clone https://github.com/kmee/odoo-brazil-posbox.git -b udev-rules && cd /opt/odoo/odoo-brazil-posbox && bash init-buildout.sh'
sudo cp $ODOO_DIR/odoo-brazil-posbox/90-posbox.rules /etc/udev/rules.d/
sudo cp $ODOO_DIR/odoo-brazil-posbox/odoo-supervisor.conf /etc/supervisor/conf.d/odoo.conf

sudo supervisorctl reread
sudo supervisorctl update

sudo supervisorctl restart odoo
