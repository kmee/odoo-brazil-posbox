#!/bin/bash
set -e -x
sudo locale-gen pt_BR.UTF-8

sudo apt-get update
sudo apt-get -y install software-properties-common
### Check if Distro is ubuntu
#!/bin/bash
DISTRO_NAME=`lsb_release -si`
DISTRO_RELEASE=`lsb_release -sc`
if [ $DISTRO_NAME == "Ubuntu" ]; then
        sudo add-apt-repository "deb http://archive.ubuntu.com/ubuntu $(lsb_release -sc) universe"
elif [ $DISTRO_NAME == "LinuxMint" ]; then
        if [ $DISTRO_RELEASE == "tara" ]; then
                sudo add-apt-repository "deb http://archive.ubuntu.com/ubuntu bionic universe"
        fi
fi
### Update repository
sudo apt-get update

if [ $DISTRO_RELEASE == "tara" ] || [ $DISTRO_RELEASE == "bionic" ]; then
        ### install packages with 18.04/bionic repository (libpng-dev)
        sudo apt-get install -y python-virtualenv expect-dev python-lxml \
          libxml2-dev libxslt-dev gcc python2.7-dev libevent-dev libsasl2-dev \
          libldap2-dev libpq-dev libpng-dev libjpeg-dev sudo supervisor git \
          curl wget postgresql gdebi-core
else
        ### install packages with 16.04/Xenial or older repository (libpng12-dev)
        sudo apt-get install -y python-virtualenv expect-dev python-lxml \
          libxml2-dev libxslt-dev gcc python2.7-dev libevent-dev libsasl2-dev \
          libldap2-dev libpq-dev libpng12-dev libjpeg-dev sudo supervisor git \
          curl wget postgresql gdebi-core
fi

ODOO_USER=odoo
ODOO_DIR=/opt/odoo
LIBBEMASAT_ZIP_URL="http://bematechpartners.com.br/wp01/?wpdmpro=libbemasat-1-0-2-26-ubuntu14-amd64&wpdmdl=2988"

if id -u $ODOO_USER &> /dev/null; then
        echo "Usuario existe:" $ODOO_USER
else
        sudo adduser odoo dialout
        sudo -u postgres createuser --createdb --no-createrole --superuser odoo
        sudo -u postgres createdb odoo
if [ ! -d "$ODOO_DIR" ]; then
        sudo mkdir -p $ODOO_DIR
        sudo chown $ODOO_USER:$ODOO_USER $ODOO_DIR
fi

# Install Bematech SAT DLL
# Script em Ansible vai lidar com essa parte agora
#if ! dpkg -l libbemasat &> /dev/null; then
#        _tmpdir=$(mktemp -d)
#        curl $LIBBEMASAT_ZIP_URL > $_tmpdir/libbemasat64.zip
#        unzip -d $_tmpdir $_tmpdir/libbemasat64.zip
#        sudo gdebi -n $_tmpdir/libbemasat_1.0.2.26-ubuntu14_amd64.deb
#        rm -f $_tmpdir/libbemasat_1.0.2.26-ubuntu14_amd64.deb $_tmpdir/libbemasat64.zip
#        rmdir $_tmpdir
#fi

sudo -H -u $ODOO_USER bash -c 'cd /opt/odoo && git clone https://github.com/kmee/odoo-brazil-posbox.git -b udev-rules'
sudo cp $ODOO_DIR/odoo-brazil-posbox/90-posbox.rules /etc/udev/rules.d/
sudo cp $ODOO_DIR/odoo-brazil-posbox/odoo-supervisor.conf /etc/supervisor/conf.d/odoo.conf
sudo -H -u $ODOO_USER bash -c 'cd /opt/odoo/odoo-brazil-posbox && bash init-buildout.sh'

sudo supervisorctl reread
sudo supervisorctl update

sudo supervisorctl restart odoo
