# Deploy Odoo Community free/khong chay local

Project nay dung custom addon Python, nen khong dua len Odoo Online/SaaS free duoc.
Can deploy theo kieu self-host: Odoo Community Docker + PostgreSQL.

## Phuong an 1: Render free de demo nhanh

Repo da co san `render.yaml`. Render se tao:

- Web service Docker `univ-sms-odoo`
- PostgreSQL free `univ-sms-db`
- URL public dang `https://...onrender.com`

Cac buoc:

1. Day repo nay len GitHub.
2. Vao Render Dashboard -> New -> Blueprint.
3. Chon repo, de Blueprint path la `render.yaml`.
4. Bam Deploy Blueprint.
5. Doi build xong, mo URL public -> `/web/login`.
6. Dang nhap Odoo bang user mac dinh:
   - Email: `admin`
   - Password: `admin`
7. Vao Apps -> Update Apps List.
8. Cai cac module `univ_sms_*` can demo.

Mac dinh Render se auto init database bang module `base`. Neu muon tu dong cai module do an
ngay khi deploy, doi trong `render.yaml`:

```yaml
- key: ODOO_INSTALL_MODULES
  value: base,univ_sms_portal,univ_sms_report,univ_sms_notification
```

Neu cai tat ca module mot lan bi loi do free RAM yeu, hay de `base` va cai module trong giao dien Apps.

## Gioi han cua Render free

- Free Postgres cua Render co dung luong 1 GB va het han sau 30 ngay.
- Web service free co the sleep khi khong truy cap.
- Persistent disk cho `/var/lib/odoo` khong mien phi, nen file upload/attachment co the mat sau restart.

=> Hop de demo/do an ngan han, khong nen dung production.

## Phuong an 2: Oracle Cloud Always Free de dung lau hon

Neu can mien phi lau hon va chap nhan tu quan tri server:

1. Tao Oracle Cloud Free Tier.
2. Tao VM Ubuntu Always Free.
3. Cai Docker va Docker Compose tren VM.
4. Clone repo len VM.
5. Chay:

```bash
docker compose up -d
```

6. Mo firewall/security list port `8069`.
7. Truy cap `http://IP_VM:8069`.

Phuong an nay dung `docker-compose.yml` hien co, co volume PostgreSQL va Odoo nen ben hon Render free.

## Bien moi truong Odoo Docker

Odoo Docker image dung cac bien sau de ket noi PostgreSQL:

- `HOST`: hostname PostgreSQL
- `PORT`: port PostgreSQL, thuong la `5432`
- `USER`: user PostgreSQL
- `PASSWORD`: password PostgreSQL

Tren Render, `deploy/render-entrypoint.sh` se tu parse `DATABASE_URL` thanh cac bien tren.
