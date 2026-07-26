# docker-compose.yml
version: '3.8'
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: odoo
      POSTGRES_PASSWORD: odoo
      POSTGRES_DB: postgres
    volumes:
      - db_data:/var/lib/postgresql/data

  odoo:
    image: odoo:17.0
    depends_on:
      - db
    ports:
      - "8069:8069"
    volumes:
      - ./addons:/mnt/extra-addons
      - ./odoo.conf:/etc/odoo/odoo.conf
    environment:
      - HOST=db
      - USER=odoo
      - PASSWORD=odoo

volumes:
  db_data:
ini# odoo.conf
[options]
addons_path = /mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons
db_host = db
db_user = odoo
db_password = odoo
Lệnh chạy / cập nhật module:
bashdocker compose up -d
docker compose exec odoo odoo -d univ_sms_db -i univ_sms_base,univ_sms_student --stop-after-init
docker compose exec odoo odoo -d univ_sms_db -u univ_sms_student --stop-after-init