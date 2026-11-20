FROM odoo:17.0

USER root

COPY ./addons /mnt/extra-addons
COPY ./deploy/odoo.conf /etc/odoo/odoo.conf
COPY ./deploy/render-entrypoint.sh /usr/local/bin/render-entrypoint.sh

# Xóa các script cũ/tạm không thuộc module khỏi image
RUN find /mnt/extra-addons -maxdepth 1 -type f -delete \
    && sed -i 's/\r$//' /usr/local/bin/render-entrypoint.sh \
    && chown -R odoo:odoo /mnt/extra-addons /etc/odoo/odoo.conf \
    && chmod +x /usr/local/bin/render-entrypoint.sh

USER odoo

EXPOSE 8069
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s \
    CMD python3 -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/web/health' % os.environ.get('PORT','8069'), timeout=8)" || exit 1

ENTRYPOINT ["/usr/local/bin/render-entrypoint.sh"]
CMD []
