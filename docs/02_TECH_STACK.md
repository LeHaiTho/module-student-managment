Backend Framework: Odoo 17.0 Community
Language: Python 3.10+
Database: PostgreSQL 15
Frontend (Backend UI): XML Views (Form/List/Kanban/Search) - chuẩn Odoo, KHÔNG dùng Studio
Frontend (Portal): 
  - QWeb templates kế thừa portal.portal_layout
  - Bootstrap 5 (có sẵn trong Odoo assets)
  - JS: Odoo OWL framework (cho component động nếu cần)
Reports: QWeb PDF (wkhtmltopdf)
API (nếu cần app mobile sau này): Odoo external API (XML-RPC/JSON-RPC) hoặc module REST tùy chọn (Phase 2+)
Dev Environment: Docker Compose (odoo:17.0 + postgres:15)
Version Control: Git, branch theo module (feature/univ_sms_student...)
Dependency Modules (core Odoo): base, mail, portal, account (cho fee), website (cho portal nếu cần landing)