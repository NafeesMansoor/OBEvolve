"""Seed data for newly-provisioned tenants.

`app.services.tenancy.provision_tenant` calls these in order:
`default_permissions.seed_default_permissions` -> `default_roles.seed_default_roles`
-> (optionally) `demo_institution.seed_demo_data`.
"""
