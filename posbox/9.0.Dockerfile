FROM debian:jessie AS base
MAINTAINER Iván Todorovich <ivan.todorovich@druidoo.io>

ENV ODOO_SRC_PATH="/home/odoo/odoo-src"
ENV ODOO_DEST="/home/odoo/odoo"
ENV REPOSITORY_URL="https://github.com/AwesomeFoodCoops/odoo-production.git"
ENV REPOSITORY_BRANCH="9.0"

# Install some deps, lessc and less-plugin-clean-css, and wkhtmltopdf
RUN set -x; \
        apt-get update \
        && apt-get install -y --no-install-recommends \
	    sudo \
	    adduser \
	    apache2 \
	    postgresql-client \
	    python python-dateutil \
	    python-decorator \
	    python-docutils \
	    python-feedparser \
	    python-imaging \
	    python-jinja2 \
	    python-ldap \
	    python-libxslt1 \
	    python-lxml \
	    python-mako \
	    python-mock \
	    python-openid \
	    python-passlib \
	    python-psutil \
	    python-psycopg2 \
	    python-pybabel \
	    python-pychart \
	    python-pydot \
	    python-pyparsing \
	    python-pypdf \
	    python-reportlab \
	    python-requests \
	    python-simplejson \
	    python-tz python-unittest2 \
	    python-vatnumber \
	    python-vobject \
	    python-werkzeug \
	    python-xlwt \
	    python-yaml \
	    python-gevent \
	    python-serial \
	    python-pip \
	    python-dev \
	    net-tools \
	    vim \
	    mc \
	    mg \
	    screen \
	    iw \
	    hostapd \
	    isc-dhcp-server \
	    git \
	    rsync \
	    console-data \
	    gcc \
	    cron \
	    usbutils

RUN pip install pyusb==1.0b1 \
	    qrcode==4.0.1 \
	    evdev

RUN apt-get install -y libyaml-dev libpython2.7-dev \
	&& pip install pyyaml \
	    pycountry \
	    pyserial


RUN useradd --create-home --shell /bin/bash odoo \
	&& groupadd usbusers \
	&& usermod -a -G usbusers odoo \
	&& usermod -a -G lp odoo

RUN echo '* * * * * rm /var/run/odoo/sessions/*' | crontab -

# Clone repo. TODO: use sparse-checkout instead
RUN git clone -b "$REPOSITORY_BRANCH" --single-branch --depth 1 "$REPOSITORY_URL" "$ODOO_SRC_PATH"

WORKDIR "$ODOO_SRC_PATH"

# Copy addons
RUN mkdir -p "$ODOO_DEST/addons"
RUN cp -r "$ODOO_SRC_PATH/odoo/addons/web" $ODOO_DEST/addons/ || true
RUN cp -r "$ODOO_SRC_PATH/odoo/addons/web_kanban" $ODOO_DEST/addons/ || true
RUN cp -r ${ODOO_SRC_PATH}/odoo/addons/hw_* $ODOO_DEST/addons/ || true

# Copy point_of_sale/tools
RUN mkdir -p "$ODOO_DEST/addons/point_of_sale/tools/posbox/"
RUN cp -r "$ODOO_SRC_PATH/odoo/addons/point_of_sale/tools/posbox/configuration" $ODOO_DEST/addons/point_of_sale/tools/posbox/ || true

# Copy odoo
RUN cp -r "$ODOO_SRC_PATH/odoo/openerp" $ODOO_DEST/ || true
RUN cp -r "$ODOO_SRC_PATH/odoo/odoo.py" $ODOO_DEST/ || true

# Copy hw_* addons
RUN cp -r $ODOO_SRC_PATH/extra_addons/hw_* $ODOO_DEST/addons/ || true
RUN cp -r $ODOO_SRC_PATH/OCA_addons/hw_* $ODOO_DEST/addons/ || true
RUN cp -r $ODOO_SRC_PATH/louve_addons/hw_* $ODOO_DEST/addons/ || true
RUN cp -r $ODOO_SRC_PATH/intercoop_addons/hw_* $ODOO_DEST/addons/ || true

RUN chown -R odoo:odoo "$ODOO_DEST"
RUN mkdir -p /var/run/odoo
RUN touch /var/run/odoo/odoo.pid && chown odoo:odoo -R /var/run/odoo
RUN rm -rf "$ODOO_SRC_PATH"

#WORKDIR "/home/odoo/odoo"
#USER odoo
#RUN set -x; \
#	git config core.sparsecheckout true \
#	&& echo -e "addons/web\naddons/web_kanban\naddons/hw_*\naddons/point_of_sale/tools/posbox/configuration\nopenerp/\nodoo.py" > sparse-checkout > /dev/null \
#	&& git read-tree -mu HEAD

WORKDIR "$ODOO_DEST"
USER odoo
VOLUME /var/log/odoo
EXPOSE 8069

ONBUILD ARG DB_HOST="db"
ONBUILD ARG DB_USER="odoo"
ONBUILD ARG DB_PASS="odoo"
ONBUILD ARG SERVER_WIDE_MODULES="hw_proxy,hw_escpos"

ONBUILD ENV DB_HOST="$DB_HOST"
ONBUILD ENV DB_USER="$DB_USER"
ONBUILD ENV DB_PASS="$DB_PASS"
ONBUILD ENV SERVER_WIDE_MODULES="$SERVER_WIDE_MODULES"

ONBUILD RUN echo "db_host = db" >> $ODOO_DEST/addons/point_of_sale/tools/posbox/configuration/odoo.conf \
 && echo "db_user = odoo" >> $ODOO_DEST/addons/point_of_sale/tools/posbox/configuration/odoo.conf \
 && echo "db_password = odoo" >> $ODOO_DEST/addons/point_of_sale/tools/posbox/configuration/odoo.conf \
 && echo "server_wide_modules = ${SERVER_WIDE_MODULES}" >> $ODOO_DEST/addons/point_of_sale/tools/posbox/configuration/odoo.conf

ONBUILD CMD ["/home/odoo/odoo/odoo.py", "-c", "/home/odoo/odoo/addons/point_of_sale/tools/posbox/configuration/odoo.conf"]
