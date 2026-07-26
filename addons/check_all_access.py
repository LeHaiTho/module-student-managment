# Check all models in univ_sms_ for missing ACL
models_to_check = env['ir.model'].search([('model', 'like', 'univ.sms')])
admin_user = env['res.users'].browse(2)
env2 = env(user=admin_user)

print("=== Access Rights Check for admin (uid=2) ===")
errors = []
for m in models_to_check:
    model_name = m.model
    try:
        if model_name in env2:
            ok_r = env2[model_name].check_access_rights('read', raise_exception=False)
            ok_c = env2[model_name].check_access_rights('create', raise_exception=False)
            ok_w = env2[model_name].check_access_rights('write', raise_exception=False)
            if not ok_r or not ok_c or not ok_w:
                errors.append(f"MISSING: {model_name} - read:{ok_r} create:{ok_c} write:{ok_w}")
    except Exception as ex:
        errors.append(f"ERROR checking {model_name}: {ex}")

if errors:
    print("Problems found:")
    for e in errors:
        print(f"  - {e}")
else:
    print("All models have correct access rights for admin!")
