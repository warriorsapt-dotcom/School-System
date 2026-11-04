# School setup and account IDs

Each installation/database represents one school. This change does not isolate multiple schools sharing one database.

## Configure a new school

1. Sign in to the school dashboard as an Administrator.
2. Open **School Settings**.
3. Enter the school name and account suffix, then select **Save School Settings**.

Examples:

| School name | Account suffix | Example login ID |
| --- | --- | --- |
| Kahuho Secondary School | ksc | mary@ksc |
| Kiambogo Township Primary | ktp | mary@ktp |

The name appears on the login page and dashboard. When adding a teacher or student, enter either a local name such as `mary` (the suffix is appended), or a complete login ID/email address. The application rejects duplicate login IDs. A short suffix is an internal login identifier, not an email service or mailbox. Parent email fields continue to require normal email addresses.

Existing account IDs and passwords do not change when settings change. Old accounts can still sign in using their full existing ID. A bare name at login uses the current suffix, so use the full ID for accounts created under an earlier suffix.

The same settings are available to appropriately authorised staff in **Django admin > Users > School settings**. Only one settings record is allowed. When creating an administrator in Django admin or with `createsuperuser`, enter the full ID, such as `head@ksc`.

## Update the Ubuntu VM

Stop the development server with Ctrl+C. Back up your database before applying schema changes.

```bash
cd ~/apps/School-System
git status --short
git pull --ff-only
source .venv312/bin/activate
python manage.py migrate
python manage.py check
python manage.py runserver 100.99.57.75:8000
```

Reload the browser (Ctrl+Shift+R) so it fetches the updated JavaScript. No new Python dependency is required.

Migration `0002_alter_customuser_role` records the existing Principal role change. Migration `0003_school_configuration` adds the school configuration and changes the account identifier field without renaming existing accounts. If you previously generated a migration on the VM and Git reports a conflict, retain that file and inspect its contents/history before resolving it. Do not delete applied migration files or use `--fake` blindly.

## Access behaviour

Only administrators can update school settings through the API. The school name and account suffix are public so the login page can display them. Profile updates cannot change roles, and public registration cannot grant privileged roles.

## Verification

The feature is covered by tests for permissions, settings validation, internal login IDs, automatic suffixes, duplicate rejection, preservation of old logins, escaped branding, and Django admin form validation. The browser flow was checked using a separate temporary database.
