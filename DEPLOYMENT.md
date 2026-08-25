# Deployment Guide

Deploying FilmGraph to a single AWS EC2 instance, running as background services that survive a
reboot or an SSH disconnect. No Docker or Kubernetes - one plain instance is the right amount of
infrastructure for this stage.

**Sections 1-10 are first-time setup. [Section 11](#11-redeploying) is the runbook you'll actually
use day to day.** Long explanations live in the [appendix](#appendix--why-these-steps-exist) so the
command path stays scannable; each step links to its own note.

**Prerequisites:** an AWS account, the repo on GitHub, and `movie-data.sql` from
[Releases](https://github.com/VOsokinP/FilmGraph/releases).

---

## 1. Launch the EC2 instance

In **EC2 → Launch Instance**:

| Setting | Value |
|---|---|
| AMI | Ubuntu Server 24.04 LTS (confirm the **Free tier eligible** tag - AWS moves it between releases) |
| Instance type | `t3.micro` or `t2.micro` |
| Key pair | Create new, download the `.pem`. AWS won't let you re-download it. Never commit it. |
| Storage | 8 GB gp3 default |

Security group - inbound rules, exactly these:

- **SSH (22)** - source **My IP**, not `0.0.0.0/0`
- **HTTP (80)** - source `0.0.0.0/0`
- **3306 and 8000 - closed.** MySQL is reached only from `localhost`; the API only through Nginx.
  Opening either is the most common first-deploy mistake. [Why →](#a1-the-two-ports-that-must-stay-closed)

Then **Elastic IPs → Allocate → Actions → Associate**, resource type `Instance`, leave private IP
blank. Without one, the public IP changes on every stop/start.

## 2. Connect and harden

```bash
chmod 400 your-key.pem
ssh -i your-key.pem ubuntu@<elastic-ip>

sudo apt update && sudo apt upgrade -y
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw enable
```

The host firewall is a second layer behind the security group, not a replacement for it.

## 3. Install system dependencies

```bash
sudo apt install -y software-properties-common
sudo add-apt-repository universe
sudo apt update
sudo apt install -y python3 python3-venv python3-pip mysql-server nginx git nodejs npm
node -v          # need 20.19+ or 22.12+; Ubuntu 24.04 ships 22.x
```

`universe` must be enabled first or `python3-pip`, `python3-venv`, `nodejs`, and `npm` all fail with
`Unable to locate package`. Plain `python3` is deliberate - 24.04's default is 3.12, which satisfies
the project's 3.11+ floor, and `python3.11` isn't packaged on this release.

## 4. Set up MySQL

```bash
sudo mysql_secure_installation
sudo mysql -u root
```

```sql
CREATE USER 'appuser'@'localhost' IDENTIFIED BY 'ChooseADifferentPasswordThanLocal!';
CREATE DATABASE moviedb;
GRANT ALL PRIVILEGES ON moviedb.* TO 'appuser'@'localhost';
```

Use a **different password than your local `.env`**. Then confirm the listening socket - ground
truth, regardless of what the config file claims:

```bash
sudo ss -tlnp | grep 3306        # want 127.0.0.1:3306, not 0.0.0.0:3306
```

Schema and seed data come in step 5, once Alembic is on the box.

## 5. Clone, configure, and load data

```bash
git clone <your-repo-url>
cd filmgraph/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Create `backend/.env` **on the instance** - it's gitignored and never travels through git:

```
DATABASE_URL=mysql+pymysql://appuser:<the password from step 4>@localhost:3306/moviedb
JWT_SECRET_KEY=<generate>
SESSION_SECRET_KEY=<generate a different one>
```

```bash
[ -n "$(tail -c1 .env)" ] && echo >> .env
python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(48))" >> .env
python3 -c "import secrets; print('SESSION_SECRET_KEY=' + secrets.token_urlsafe(48))" >> .env
chmod 600 .env
```

Generate the two separately - they sign different things.
[Why →](#a2-two-secrets-never-one)

Schema and seed data:

```bash
wget -O db/movie-data.sql \
  https://github.com/VOsokinP/FilmGraph/releases/download/v1.0-seed-data/movie-data.sql
alembic upgrade head
mysql -u appuser -p --default-character-set=utf8mb4 moviedb < db/movie-data.sql
```

**Verify the row counts** - a clean exit code doesn't prove every row landed.
[Why →](#a3-seed-data-has-no-integrity-check)

```bash
mysql -u appuser -p moviedb -e "
SELECT 'movies' t, COUNT(*) n FROM movies UNION ALL SELECT 'stars', COUNT(*) FROM stars
UNION ALL SELECT 'stars_in_movies', COUNT(*) FROM stars_in_movies
UNION ALL SELECT 'genres_in_movies', COUNT(*) FROM genres_in_movies
UNION ALL SELECT 'ratings', COUNT(*) FROM ratings
UNION ALL SELECT 'creditcards', COUNT(*) FROM creditcards
UNION ALL SELECT 'customers', COUNT(*) FROM customers
UNION ALL SELECT 'genres', COUNT(*) FROM genres;"
```

Expected: 9052 / 60150 / 79921 / 15615 / 7998 / 517 / 453 / 23. Anything short means a partial load.

## 6. Run the backend under systemd

Create `/etc/systemd/system/filmgraph-api.service` (the repo copy is `deploy/filmgraph-api.service`):

```ini
[Unit]
Description=FilmGraph API
After=network.target mysql.service

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/filmgraph/backend
EnvironmentFile=/home/ubuntu/filmgraph/backend/.env
ExecStart=/home/ubuntu/filmgraph/backend/.venv/bin/gunicorn app.main:app \
    -k uvicorn.workers.UvicornWorker \
    --workers 2 \
    --bind 127.0.0.1:8000 \
    --access-logfile - \
    --error-logfile -
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now filmgraph-api
sudo systemctl status filmgraph-api
sudo journalctl -u filmgraph-api -n 50 --no-pager     # if it isn't active (running)
```

The four lines most likely to be wrong:

| Line | Why it matters |
|---|---|
| `EnvironmentFile` | Without it the app can't see `DATABASE_URL` and crash-loops |
| `--bind 127.0.0.1:8000` | Not `0.0.0.0` - the API is reachable only through Nginx |
| `--access-logfile -` | Without it a 401 or 500 produces **zero** journal output. [Why →](#a4-logs-you-dont-have) |
| `Restart=always` | A crash restarts instead of leaving the site down |

`gunicorn` is declared in `pyproject.toml`, so step 5's `pip install -e .` already installed it.
Don't install it ad hoc. [Why →](#a5-the-drift-class)

## 7. Build the frontend

```bash
free -h          # if Swap shows 0B, add swap first (below)
cd ~/filmgraph/frontend
npm ci
npm run build
ls -la dist/index.html
grep -r "localhost:8000" dist/ && echo "WARNING: localhost leaked" || echo "clean"
```

`npm ci`, not `npm install` - it installs exactly what `package-lock.json` pins. No config edits
needed: `frontend/.env.production` is committed and sets `VITE_API_BASE=/api`, a relative
same-origin path.

On a 1 GB `t2.micro`/`t3.micro` the TypeScript compile can be OOM-killed, which looks like success.
[Why →](#a6-the-build-that-looks-like-it-worked)

```bash
sudo fallocate -l 1G /swapfile && sudo chmod 600 /swapfile
sudo mkswap /swapfile && sudo swapon /swapfile
```

## 8. Install and configure Nginx

Nginx serves the built frontend and reverse-proxies `/api/` to `127.0.0.1:8000`. Create
`/etc/nginx/sites-available/filmgraph` (repo copy: `deploy/nginx.conf`):

```nginx
server {
    listen 80;
    server_name <elastic-ip-or-domain>;

    root /home/ubuntu/filmgraph/frontend/dist;
    index index.html;

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        try_files $uri /index.html;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/filmgraph /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t                    # always before reload - a broken config takes the site down
sudo systemctl reload nginx
```

Two traps this config addresses, both of which pass `nginx -t` and still break the site:

- `try_files $uri /index.html` - the SPA fallback. Without it, a refresh on `/movies/:id` 404s at
  Nginx before React Router sees it. [Why →](#a7-the-spa-fallback)
- `www-data` can't traverse `/home/ubuntu/` by default, so `/api/` works but `/` serves a 500.
  [Symptom and fix →](#a8-the-home-directory-permission-trap)

## 9. HTTPS

Login posts a password, so **HTTPS is a requirement, not a hardening step** - and HTTPS-first
browsers can't reliably reach a plain-HTTP bare IP at all. Let's Encrypt won't issue for an IP, so
a domain comes first:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

Certbot adds the certificate, the 80→443 redirect, and auto-renewal. Then open **443** in the
security group and keep 80 open so the redirect works.

## 10. Verify end-to-end

1. `http://<elastic-ip>/` loads `/login`.
2. Log in; the movie list returns 10 rows.
3. Dev tools → Network: API calls go to `/api/...` on the **same origin**, no CORS errors.
4. Sort by **Year**; click into a movie and a star.
5. Cart → payment → confirmation writes an order.
6. **Hard-refresh while on `/cart`** - tests the `try_files` fallback.
7. Visit `/nope` - the app's own "Page not found", not an Nginx 404.
8. `sudo systemctl status filmgraph-api nginx` - both `active (running)`.
9. AWS Console: security group still shows only 22 (your IP), 80, and 443. Nothing else.

---

## 11. Redeploying

The whole runbook. Steps 2-4 are cheap, idempotent, and **not optional** - every failed deploy so
far has been the server disagreeing with the repo, with nothing checking.
[Why →](#a5-the-drift-class)

```bash
# 1. pull
ssh -i your-key.pem ubuntu@<elastic-ip>
cd ~/filmgraph
git rev-parse --short HEAD                  # rollback point - write it down
git pull

# 2. sync dependencies (every time, not "if they changed")
cd backend && source .venv/bin/activate && pip install -e .

# 3. prove the settings load
python3 -c "from app.config import settings; print('config OK')"

# 4. restart, and prove it booted
sudo systemctl restart filmgraph-api
sudo systemctl status filmgraph-api         # active (running)
curl -i http://127.0.0.1:8000/health        # 200 - this is the real gate

# 5. rebuild the frontend, only if frontend code changed
free -h
cd ../frontend && npm ci && npm run build
grep -r "localhost:8000" dist/ && echo "WARNING: localhost leaked" || echo "clean"

# 6. watch the journal in a second session while you click through
sudo journalctl -u filmgraph-api -f
```

Notes:

- **Step 3** raises the same `ValidationError` the service would hit at boot, naming the exact
  missing field. Prefer it over diffing `.env` against `.env.example`.
  [Why →](#a9-check-the-invariant-that-matters)
- **Step 4:** `active (running)` only means systemd started a process. `/health` returning 200 is
  what proves the app loaded its settings and reached MySQL.
- **Step 5** needs no service restart - Nginx serves whatever is in `dist/` on the next request.
- If a required setting is missing, generate it with the commands in [step 5](#5-clone-configure-and-load-data).

**Rollback:** `git reset --hard <sha>`, rebuild the frontend, restart the service.

---

## Troubleshooting

Start with logs, not guesses:

```bash
sudo journalctl -u filmgraph-api -f                    # follow live
sudo journalctl -u filmgraph-api -n 100 --no-pager     # recent history
sudo journalctl -u filmgraph-api -p err --no-pager     # errors only
sudo tail -f /var/log/nginx/error.log                  # failures that never reached the app
sudo tail -f /var/log/nginx/access.log
```

An empty API journal while requests are clearly arriving means they aren't reaching the app - check Nginx and the `proxy_pass` target.

| Symptom | Likely cause | Step |
|---|---|---|
| Service starts then crash-loops | `EnvironmentFile` missing, or a required setting absent from `.env` | 6, 11.3 |
| `ModuleNotFoundError` at worker boot | Server venv drifted from `pyproject.toml` | 11.2 |
| `/api/` works, `/` returns 500 | `www-data` can't traverse `/home/ubuntu/`; `(13: Permission denied)` in the Nginx error log | 8 |
| `rewrite or internal redirection cycle` | `dist/index.html` doesn't exist - the build didn't finish | 7 |
| Works when clicking, 404 on refresh | SPA fallback missing | 8 |
| Site unchanged after a deploy | Nginx site never symlinked into `sites-enabled` | 8 |
| Frontend calls `localhost:8000` | `.env.production` missing at build time | 7 |
| Public IP changed after a restart | No Elastic IP | 1 |
| `Unable to locate package` | `universe` not enabled | 3 |

---

## Appendix - why these steps exist

Most of these are failures this project actually hit.

#### A1. The two ports that must stay closed
3306 and 8000 need no public inbound rule: MySQL is reached only over `localhost`, and the API only
through Nginx on 80. Opening 3306 exposes the database directly; opening 8000 exposes the API
bypassing Nginx. Combined with MySQL bound to `127.0.0.1` (step 4), that's two independent layers
rather than one.

#### A2. Two secrets, never one
`JWT_SECRET_KEY` signs identity; `SESSION_SECRET_KEY` signs the cart cookie. One shared value means
a weakness in either compromises both. `token_urlsafe` is deliberate over `openssl rand -base64` - it emits only `[A-Za-z0-9_-]`, with nothing systemd's `EnvironmentFile` parser could misread as
quoting.

#### A3. Seed data has no integrity check
The published release asset was once missing all 453 `customers` rows, and the failure surfaced days
later as "login is broken on EC2" - pointing at MySQL, the loader, and the schema, when the fault
was a file published earlier. An artifact with no checksum and no manifest is indistinguishable from
a corrupted one, so verify the counts at load time rather than discovering it at first login.

#### A4. Logs you don't have
Gunicorn without `--access-logfile -` writes nothing to the journal, so a 401 or a 500 leaves no
trace at all and debugging becomes guesswork. This cost real hours during the 2026-08-21 deploy,
where the frontend reported "Invalid email or password" while the actual problem was that the API
had never started.

#### A5. The drift class
Four separate deploy failures shared one shape: **two things that each look internally consistent,
with nothing comparing them.** Git index vs filesystem (a case-only filename difference that broke
only on Linux). Published asset vs local file. Installed packages vs `pyproject.toml`. Server `.env`
vs what `config.py` requires. In every case both sides were valid in isolation and the happy path
gave no signal they'd drifted. The fix is always a cheap check at the boundary - which is why
`pip install -e .` is unconditional and the config import is its own step.

#### A6. The build that looks like it worked
On 1 GB of RAM the TypeScript compile can be OOM-killed. The tell is `Killed` printed above a normal
prompt - it reads like completion. `dist/` then holds the previous build, so you deploy the old
frontend and see stale behavior with no error anywhere. Check `free -h` before building; if a build
seems stuck, check `top` from a second SSH session rather than waiting.

#### A7. The SPA fallback
The frontend is client-side routed (`<BrowserRouter>`). A direct visit or refresh on `/cart` is a
real HTTP request to Nginx for a path with no file behind it. Without `try_files $uri /index.html`,
Nginx 404s before React Router ever loads - the classic "works when I click around, breaks on
refresh" bug.

#### A8. The home-directory permission trap
Nginx workers run as `www-data`, but Ubuntu's default home permissions (`drwxr-x---`) block it from
*traversing into* `/home/ubuntu/`. `/api/` still works - that's proxied and never touches the
filesystem - while `/` and every static asset serve Nginx's 500 page, with `nginx -t` passing.
Confirm with `(13: Permission denied)` in `/var/log/nginx/error.log`, then:

```bash
sudo chmod o+x /home/ubuntu /home/ubuntu/filmgraph /home/ubuntu/filmgraph/frontend
sudo chmod -R o+rX /home/ubuntu/filmgraph/frontend/dist
```

#### A9. Check the invariant that matters
Diffing `.env` against `.env.example` looks like the obvious check but compares the wrong thing:
`.env.example` lists *every* setting, while only those with **no default** in `app/config.py` can
break the app - currently `DATABASE_URL`, `JWT_SECRET_KEY`, `SESSION_SECRET_KEY`. On a healthy
server that diff reports four missing keys that all have defaults. A check that cries wolf on a good
deploy is one you learn to skim past, which is how the original missing-secret failure slipped
through. Importing `app.config` tests the real condition and can't drift from the code.
