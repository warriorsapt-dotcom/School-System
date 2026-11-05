# Set up the Kahuho school server in VMware

Use this guide to build a private test installation of School System for **Kahuho Secondary School**. Each school gets its own VM, PostgreSQL database, administrator account, and Tailscale address. The examples use `kahuho-server` for the VM, `kahuhoadmin` for the Ubuntu user, and `ksc` for the school's login suffix.

**Where you are now:** Your VM already reports Ubuntu 26.04.1 LTS, Python 3.14.4, and PostgreSQL accepting connections. **Start at Step 3** on that VM. For a fresh installation, begin at Step 1. Run each step separately and check the result before continuing.

## 1. Create the VM on Windows

1. Download the Ubuntu Server 26.04 LTS AMD64 installer from [Ubuntu Server](https://ubuntu.com/download/server).
2. In VMware Workstation, choose **File → New Virtual Machine → Typical** and select the Ubuntu ISO.
3. Name the VM `kahuho-server`. A starting configuration for this test is **2 CPU cores, 4 GB RAM, 60 GB virtual disk, and NAT networking**.
4. Start the VM. In the Ubuntu installer, use guided storage on the **new virtual disk**. Set the hostname to `kahuho-server`, create the user `kahuhoadmin`, and record its password. Select **Install OpenSSH server** if you want terminal access from another computer.
5. Finish installation, eject the installer ISO if prompted, restart, and sign in. The prompt should look like `kahuhoadmin@kahuho-server:~$`.

All terminal commands below run **inside Ubuntu**, unless a step explicitly says to open a browser on Windows.

## 2. Install the base packages and check PostgreSQL

~~~bash
sudo apt update
sudo apt install -y git curl ca-certificates openssh-client postgresql
sudo systemctl enable --now postgresql
hostname
cat /etc/os-release
python3 --version
pg_isready
~~~

**Checkpoint:** The hostname is `kahuho-server` and PostgreSQL reports `accepting connections`. On this VM, `python3` reports 3.14.4. The school application uses a separate Python 3.12 environment.

## 3. Install Python 3.12 for the school application

On Kahuho's Ubuntu 26.04 installation, APT reported `Unable to locate package python3.12`. Use **uv** under the `kahuhoadmin` account to install the project interpreter. [Official uv installation guide](https://docs.astral.sh/uv/getting-started/installation/)

~~~bash
sudo apt install -y curl ca-certificates git openssh-client
curl -fsSL https://astral.sh/uv/install.sh -o /tmp/uv-install.sh && sh /tmp/uv-install.sh
export PATH="$HOME/.local/bin:$PATH"
uv --version
uv python install 3.12
"$(uv python find 3.12)" --version
~~~

**Checkpoint:** The last line prints `Python 3.12.x`. Seeing 3.14 from `python3 --version` outside the project environment is expected.

## 4. Give the VM read access to the private GitHub repository

1. **In Ubuntu**, generate a key for this fresh VM. Accept the default filename. If a key already exists at that path, keep it and use its public key if appropriate.
   ~~~bash
   ssh-keygen -t ed25519 -C "kahuho-server"
   cat ~/.ssh/id_ed25519.pub
   ~~~
2. **In a browser**, open the [School-System repository](https://github.com/warriorsapt-dotcom/School-System). Under **Settings → Deploy keys → Add deploy key**, enter `kahuho-server` as the title and paste the single line printed by `cat`. Leave **Allow write access** unchecked. The file ending in `.pub` is the one to share. [GitHub deploy keys](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/managing-deploy-keys)
3. **Back in Ubuntu**, clone the project:
   ~~~bash
   mkdir -p ~/apps
   cd ~/apps
   git clone git@github.com:warriorsapt-dotcom/School-System.git
   cd School-System
   git log -1 --oneline
   ~~~

**Checkpoint:** Git shows the latest commit. If the first SSH connection asks about GitHub's identity, compare the fingerprint with [GitHub's published SSH fingerprints](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/githubs-ssh-key-fingerprints). For `Permission denied (publickey)`, check that the public key was added to this repository.

## 5. Create the isolated Python environment

~~~bash
cd ~/apps/School-System
uv venv --python 3.12 --seed .venv312
source .venv312/bin/activate
python --version
python -m pip install -r requirements.txt
python -m pip check
~~~

**Checkpoint:** Inside `(.venv312)`, Python reports 3.12.x and pip reports `No broken requirements found`. In a new terminal, return to the project and run `source .venv312/bin/activate` again.

## 6. Create Kahuho's database and test the password

Run these creation commands once on the new VM. Choose a strong database password and keep it in your password manager. You will enter the same password in Step 8.

~~~bash
sudo -u postgres createuser --pwprompt school_app
sudo -u postgres createdb --owner=school_app school_system
psql -h 127.0.0.1 -U school_app -d school_system -c 'SELECT current_database(), current_user;'
~~~

**Checkpoint:** The result shows database `school_system` and user `school_app`. If the role and database already exist from an earlier attempt, use the last command to test them before making changes.

## 7. Connect this VM to Tailscale

~~~bash
curl -fsSL https://tailscale.com/install.sh -o /tmp/install-tailscale.sh && sh /tmp/install-tailscale.sh
sudo systemctl enable --now tailscaled
sudo tailscale up
tailscale ip -4
~~~

Open the sign-in link printed by `tailscale up` and authorize the VM on Kahuho's intended Tailscale network. Record **this VM's IPv4 address**. The previous server's address, `100.99.57.75`, belongs to the earlier installation. [Tailscale for Linux](https://tailscale.com/docs/install/linux)

## 8. Create the application's local settings

Run this block from the Ubuntu terminal on the new VM. It prompts for the **Step 6 database password**, generates a unique Django secret, and writes the VM's Tailscale address to `.env`. Enter the password at the hidden terminal prompt. Keep `.env` private.

~~~bash
cd ~/apps/School-System
source .venv312/bin/activate
mkdir -p logs media
python - <<'PY'
import os
import secrets
import subprocess
from getpass import getpass
from ipaddress import IPv4Address
from pathlib import Path

ip = IPv4Address(subprocess.check_output(["tailscale", "ip", "-4"], text=True).strip())
password = getpass("PostgreSQL password for school_app: ")
if not password:
    raise SystemExit("A database password is required.")
os.umask(0o077)
with Path(".env").open("x", encoding="utf-8") as settings:
    settings.write(
        f"SECRET_KEY={secrets.token_urlsafe(64)}\nDEBUG=True\n"
        f"ALLOWED_HOSTS=localhost,127.0.0.1,{ip}\n"
        f"DB_NAME=school_system\nDB_USER=school_app\nDB_PASSWORD={password}\n"
        "DB_HOST=127.0.0.1\nDB_PORT=5432\n"
    )
print("Created .env for", ip)
PY
~~~

If you see `FileExistsError`, the file already exists. Review it locally with `nano .env` rather than replacing it. A database password error at the next step means you should repeat the connection test in Step 6 and check `DB_PASSWORD`.

## 9. Set up the tables and first administrator

~~~bash
python manage.py migrate
python manage.py check
python manage.py createsuperuser
~~~

For the email or school login ID, enter **`head@ksc`**. Supply a username such as `head`, the administrator's name, and a new login password. This password is for the school portal. Use the **full ID** on the first sign-in.

**Checkpoint:** Migrations finish, Django reports no system-check issues, and the superuser is created. A fresh school starts with empty records. On a disposable demonstration VM only, `python manage.py seed_data` also creates sample accounts, classes, and a timetable.

## 10. Enable startup and open the portal

From `~/apps/School-System`, run the installer as `kahuhoadmin`. If a manual Django server is already running, stop it with **Ctrl+C** first.

~~~bash
bash scripts/install-autostart.sh
systemctl is-enabled school-system
systemctl is-active school-system
~~~

**Checkpoint:** The installer prints `Ready at http://…:8000/ and enabled at boot.` The two status commands return `enabled` and `active`.

On Windows or Android, connect Tailscale on a device authorized for this VM. In its browser, open the **exact URL the installer printed**, including port **8000**. Sign in with `head@ksc`. For Django administration, add `/admin/` to the address.

## 11. Set the school identity and add its records

1. In the dashboard, open **School Settings**. Enter **Kahuho Secondary School** as the name, set the account suffix to **ksc**, and save.
2. Create the academic term, subjects, and classes in Django admin. Add teachers and students, assign students to their classes, and link teachers to class subjects.
3. In the dashboard, use **Timetable → Add lesson**. Sign in as a test teacher or student to check what that account can see. For subsequent new accounts, a short login name such as `mary` uses the configured suffix to become `mary@ksc`.

## 12. Verify startup after a reboot

~~~bash
sudo reboot
~~~

Once Ubuntu has booted, open the portal from your phone **before logging into the VM**. If the page fails to open, sign in to Ubuntu and check:

~~~bash
systemctl status school-system --no-pager
sudo journalctl -u school-system -b -n 50 --no-pager
tailscale ip -4
pg_isready
~~~

The service starts when the **guest VM** boots. For recovery after the **Windows host** restarts, also configure VMware to start this VM automatically and test that separately.

**Before entering real student records:** This guide reproduces the private test setup. The startup script uses Django's development server, the example enables debug mode, and the project pins Django 4.2.11. A live rollout needs a tested upgrade to a supported Django release, production web serving with HTTPS and debug disabled, and a successful backup-and-restore test. [Django deployment checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)
