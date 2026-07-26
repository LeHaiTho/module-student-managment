# Script disable menu Phase 6-7 truc tiep trong database
# Chay: docker compose exec -T odoo odoo shell -d odoo < addons/disable_phase67_menus.py

# Odoo 17 - name trong ir_ui_menu la kieu JSONB (da ngu)
# Can dung ->>'en_US' hoac ->>'vi_VN' de lay text

import json

# Buoc 1: In toan bo menu hien tai de debug
print("=== ALL MENUS IN DATABASE ===")
env.cr.execute("""SELECT id, name, parent_id FROM ir_ui_menu ORDER BY id""")
all_menu = env.cr.fetchall()

# Odoo 17 luu name JSONB, can parse
for mid, mname, pid in all_menu:
    try:
        name_dict = json.loads(mname) if isinstance(mname, str) else mname
        if isinstance(name_dict, dict):
            name_text = name_dict.get('vi_VN', name_dict.get('en_US', str(name_dict)))
        else:
            name_text = str(name_dict)
    except:
        name_text = str(mname)
    print(f"  ID={mid} | Name='{name_text}' | Parent={pid}")

print(f"\n=== Total menus: {len(all_menu)} ===")