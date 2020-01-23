ARG ODOO_VERSION="9.0"
FROM druidoo/foodcoops-posbox:$ODOO_VERSION
COPY odoo.conf /home/odoo/odoo/odoo.conf

