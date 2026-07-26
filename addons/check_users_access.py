# Check if the remaining running shell process was using wrong session
# Also verify ACL for all users with univ roles

users_with_roles = env['res.users'].search([
    ('groups_id.category_id.name', '=', 'University SMS')
])
print(f"Users with University SMS roles: {len(users_with_roles)}")
for u in users_with_roles:
    groups = u.groups_id.filtered(lambda g: g.category_id.name == 'University SMS').mapped('name')
    env2 = env(user=u)
    enr_create = env2['univ.sms.enrollment'].check_access_rights('create', raise_exception=False)
    enr_read = env2['univ.sms.enrollment'].check_access_rights('read', raise_exception=False)
    fee_create = env2['univ.sms.fee'].check_access_rights('create', raise_exception=False)
    print(f"  User: {u.name} (id={u.id}) groups={groups}")
    print(f"    enrollment read={enr_read} create={enr_create} | fee create={fee_create}")
