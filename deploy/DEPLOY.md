# Deploying TimeTrack to an Ubuntu VPS

A practical, top-to-bottom guide. Plan ~30–45 minutes. Commands assume Ubuntu
22.04/24.04 and that you can `sudo`. Replace `timetrack.example.com` with your
real subdomain and `YOUR_SERVER_IP` with your server's IP everywhere.

The layout we'll create:
- Code at `/srv/timetrack` (backend + frontend)
- Backend runs under Gunicorn as a systemd service on 127.0.0.1:8001
- Nginx serves the built frontend and proxies /api, /admin, /static to Gunicorn
- HTTPS via Let's Encrypt (certbot)

---

## 1. DNS — point a subdomain at the server
In your DNS (e.g. Cloudflare), add an **A record**:
`timetrack` → `YOUR_SERVER_IP`. (If using Cloudflare, you may set the proxy to
"DNS only" first to get the certificate, then turn proxy on.)

## 2. System packages
```
sudo apt update
sudo apt install -y python3-venv python3-pip nginx postgresql git curl
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

## 3. Get the code onto the server
Put the project at `/srv/timetrack` (upload the zip and unzip, or git clone):
```
sudo mkdir -p /srv/timetrack
sudo chown -R $USER:$USER /srv/timetrack
# upload + unzip so you have /srv/timetrack/backend and /srv/timetrack/frontend
```

## 4. PostgreSQL database
```
sudo -u postgres psql -c "CREATE DATABASE timetrack;"
sudo -u postgres psql -c "CREATE USER timetrack WITH PASSWORD 'CHOOSE_A_STRONG_PASSWORD';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE timetrack TO timetrack;"
sudo -u postgres psql -c "ALTER DATABASE timetrack OWNER TO timetrack;"
```
(Prefer to start simple? You can skip this and leave DATABASE_URL blank to use
SQLite, then move to Postgres later.)

## 5. Backend setup
```
cd /srv/timetrack/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```
Edit `.env`:
```
SECRET_KEY=<paste a long random string: python3 -c "import secrets;print(secrets.token_urlsafe(50))">
DEBUG=False
ALLOWED_HOSTS=timetrack.example.com
DATABASE_URL=postgres://timetrack:CHOOSE_A_STRONG_PASSWORD@localhost:5432/timetrack
CORS_ALLOWED_ORIGINS=https://timetrack.example.com
CSRF_TRUSTED_ORIGINS=https://timetrack.example.com
```
Then:
```
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser     # your admin login
```

## 6. Run the backend as a service (Gunicorn)
```
sudo cp /srv/timetrack/deploy/timetrack.service /etc/systemd/system/timetrack.service
# make sure the User= line and paths in that file match your setup
sudo chown -R www-data:www-data /srv/timetrack
sudo systemctl daemon-reload
sudo systemctl enable --now timetrack
sudo systemctl status timetrack      # should say "active (running)"
```

## 7. Build the frontend
The frontend must know the public API address at build time:
```
cd /srv/timetrack/frontend
echo "VITE_API_BASE_URL=https://timetrack.example.com/api" > .env
npm install
npm run build                        # produces /srv/timetrack/frontend/dist
```

## 8. Nginx
```
sudo cp /srv/timetrack/deploy/nginx.conf.example /etc/nginx/sites-available/timetrack
sudo sed -i 's/timetrack.example.com/YOUR_REAL_DOMAIN/' /etc/nginx/sites-available/timetrack
sudo ln -s /etc/nginx/sites-available/timetrack /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```
Visit http://timetrack.example.com — you should see the login screen.

## 9. HTTPS
```
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d timetrack.example.com
```
certbot adds the HTTPS server block and auto-renews. Reload isn't needed.

## 10. Done
Open https://timetrack.example.com and sign in. To update later: upload new
code, then `cd backend && source .venv/bin/activate && pip install -r
requirements.txt && python manage.py migrate && python manage.py collectstatic
--noinput && sudo systemctl restart timetrack`, and rebuild the frontend
(`npm run build`).

## Firewall (recommended)
```
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

## Troubleshooting
- 502 Bad Gateway → backend service isn't running: `sudo systemctl status timetrack` and `sudo journalctl -u timetrack -n 50`.
- Admin page unstyled → you didn't run `collectstatic`, or `/static/` isn't proxied.
- Login "wrong password" but credentials are right → check CORS_ALLOWED_ORIGINS / CSRF_TRUSTED_ORIGINS match your https domain exactly.
