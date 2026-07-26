FROM odoo:17.0

USER root

COPY ./addons /mnt/extra-addons
COPY ./deploy/odoo.conf /etc/odoo/odoo.conf
COPY ./deploy/render-entrypoint.sh /usr/local/bin/render-entrypoint.sh

RUN chown -R odoo:odoo /mnt/extra-addons /etc/odoo/odoo.conf \
    && chmod +x /usr/local/bin/render-entrypoint.sh

USER odoo

ENTRYPOINT ["/usr/local/bin/render-entrypoint.sh"]
CMD ["odoo"]
