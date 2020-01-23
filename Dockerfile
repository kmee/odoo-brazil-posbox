ARG ODOO_VERSION="9.0"
FROM druidoo/foodcoops-posbox:$ODOO_VERSION
USER odoo
COPY odoo.conf /home/odoo/odoo/odoo.conf
USER root
