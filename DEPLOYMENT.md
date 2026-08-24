# Deployment Guide

Step-by-step instructions for deploying FilmGraph to a single AWS EC2 instance: the same app that
runs locally, reachable at a public IP, running as background services that survive a reboot or an
SSH disconnect. No Docker or Kubernetes here — a single plain EC2 instance is the right amount of
infrastructure for this stage of the project.

Follow the sections in order; each one exists because skipping it is a common way first deploys
break.

**Prerequisites:** an AWS account, this repo pushed to GitHub, and `movie-data.sql` available (see
the Database Setup section of the main README).

## 1. Launch the EC2 instance

1. In the AWS Console, go to **EC2 → Launch Instance**.
2. **AMI:** Ubuntu Server 24.04 LTS. Check the AMI picker's **Free tier eligible** tag before
   launching — AWS periodically changes which LTS version carries it.
3. **Instance type:** `t3.micro` or `t2.micro` (free-tier eligible) — plenty for a read-only,
   3-page app.
4. **Key pair:** create a new one and download the `.pem` file. AWS won't let you re-download it
   later, so save it somewhere safe outside this repo — never commit it.
5. **Storage:** the default 8 GB gp3 is fine.
6. **Security group** — this is the step most first deploys get wrong. Create a new security group
   with exactly these inbound rules:
   - **SSH (22)** — source: **My IP**, not `0.0.0.0/0`. If your IP changes later you'll need to
     edit this rule to reconnect; that's expected and safer than leaving SSH open to the internet.
   - **HTTP (80)** — source: `0.0.0.0/0`. This is the one port meant to be public.
   - **Leave 3306 (MySQL) and 8000 (FastAPI) closed to the internet entirely.** The database is
     only ever accessed from `localhost` on the same instance, and the API is only ever reached
     through Nginx on port 80 (step 8) — neither needs a public inbound rule. Opening 3306 or 8000
     to `0.0.0.0/0` is the single most common mistake in a first EC2 deploy, and it directly exposes
     the database or an unauthenticated API to the internet.
7. Launch the instance. Then go to **Elastic IPs**, allocate one, and **Actions → Associate Elastic
   IP address**:
   - **Resource type:** `Instance`.
   - **Instance:** the one you just launched.
   - **Private IP address:** leave blank.
   - **Reassociation:** leave checked (default).
   - Click **Associate**.

   Without an Elastic IP, the instance's public IP changes every time you stop/start it, silently
   breaking any link or bookmark pointing at the old one.

## 2. Connect and do first-time hardening

```bash
chmod 400 your-key.pem
ssh -i your-key.pem ubuntu@<elastic-ip>
```

Once connected:

```bash
sudo apt update && sudo apt upgrade -y
```

Turn on the host firewall as a second layer of defense behind the security group:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw enable
sudo ufw status
```

## 3. Install system dependencies

EC2's official Ubuntu AMIs ship with only the `main` apt component enabled — `universe` (which holds
`python3-pip`, `python3-venv`, `nodejs`, and `npm`) is off by default. Skipping this produces
`Unable to locate package` errors. Enable it first:

```bash
sudo apt install -y software-properties-common
sudo add-apt-repository universe
sudo apt update
```

Then install everything needed:

```bash
sudo apt install -y python3 python3-venv python3-pip mysql-server nginx git nodejs npm
```

This deliberately installs plain `python3` (Ubuntu 24.04's default is already 3.12, which satisfies
the project's 3.11+ requirement) rather than a pinned `python3.11`, which isn't packaged on this
release at all.

Check `node -v` — the frontend needs Node 20.19+ or 22.12+. Ubuntu 24.04's apt `nodejs` package
(v22.x) satisfies this; only reach for `nvm` if your version comes back lower.

## 4. Set up MySQL on the instance

```bash
sudo mysql_secure_installation
sudo mysql -u root
```

```sql
CREATE USER 'appuser'@'localhost' IDENTIFIED BY 'ChooseADifferentPasswordThanLocal!';
CREATE DATABASE moviedb;
GRANT ALL PRIVILEGES ON moviedb.* TO 'appuser'@'localhost';
```

Use a **different password than your local `.env`** — production credentials are their own secret,
never reused from dev.

Confirm MySQL is only listening on `localhost`, not the network interface — check the actual
listening socket, which is the ground truth regardless of what the config file says:

```bash
sudo ss -tlnp | grep 3306
```

You should see `127.0.0.1:3306` (not `0.0.0.0:3306`) next to `mysqld`. Combined with 3306 being
closed at the security group (step 1), this means the database is unreachable from outside the
instance even if something else is misconfigured — two independent layers, not one.

Schema and seed data are applied in step 5, once the repo — and its Alembic migrations — are
actually on the instance. Nothing to load here yet.

## 5. Clone the repo, configure the environment, and apply the schema

```bash
git clone <your-repo-url>
cd filmgraph
```

If the repo is private, use a GitHub personal access token or an SSH deploy key for the clone —
don't put your personal SSH key on a server.

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Create `backend/.env` **directly on the instance** (it's gitignored — it never travels through
git):

```
DATABASE_URL=mysql+pymysql://appuser:ChooseADifferentPasswordThanLocal!@localhost:3306/moviedb
```

**Apply the schema and load seed data.** `movie-data.sql` isn't in the repo (too large for git,
distributed as a GitHub Release asset instead) — pull it down now that `backend/db/` exists:

```bash
wget -O db/movie-data.sql \
  https://github.com/VOsokinP/filmgraph/releases/download/v1.0-seed-data/movie-data.sql
```

```bash
alembic upgrade head
mysql -u appuser -p moviedb < db/movie-data.sql
```

**If `movie-data.sql` includes tables outside this schema** (e.g. `creditcards`/`customers`/`sales`
from the original dataset this was sourced from — not part of FilmGraph's schema), `mysql` aborts
the entire script on the first error when run without `--force`, so an unsupported-table insert
ahead of `ratings` in the file silently prevents `ratings` from loading at all, even though the
command exits looking like it worked. Rather than editing the dump, pull just the missing table's
inserts out and pipe them in directly:

```bash
grep -i "^INSERT INTO ratings" db/movie-data.sql | mysql -u appuser -p moviedb
```

Verify with `SELECT COUNT(*) FROM ratings;` after any bulk load — a clean exit code doesn't
guarantee every row loaded.

## 6. Run the backend as a systemd service

Running `uvicorn` by hand over SSH only works until you disconnect — the process dies with the
shell session. A systemd unit keeps it running permanently, restarts it if it crashes, and starts it
on reboot.

Add `gunicorn` to manage multiple Uvicorn worker processes, so one slow request doesn't block every
other request:

```bash
pip install gunicorn
```

Create `/etc/systemd/system/filmgraph-api.service`:

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

Notes on the parts most likely to be misconfigured:
- `EnvironmentFile` is what makes `DATABASE_URL` visible to the process — forgetting this line is
  the most common cause of a service that starts, then immediately crash-loops.
- `--bind 127.0.0.1:8000`, not `0.0.0.0:8000` — the backend should only be reachable from Nginx on
  the same machine (step 8), never directly from the internet.
- `Restart=always` means a crash restarts the service instead of leaving the site down until someone
  notices.
- `--access-logfile -` / `--error-logfile -` send gunicorn's logs to stdout, which systemd captures
  into the journal. Without them a 401 or a 500 produces **zero** journal output and debugging is
  guesswork — that cost real time during the 2026-08-21 deploy.

```bash
sudo systemctl daemon-reload
sudo systemctl enable filmgraph-api
sudo systemctl start filmgraph-api
sudo systemctl status filmgraph-api
```

If it's not `active (running)`, check the actual error first:

```bash
sudo journalctl -u filmgraph-api -n 50 --no-pager
```

## 7. Build the frontend for production

No manual edits needed — `frontend/src/api/client.ts` reads its API base URL from
`import.meta.env.VITE_API_BASE`, and Vite automatically loads `frontend/.env.production` (already
committed) whenever you run `npm run build`, setting it to the relative, same-origin path `/api`.
This matters because a build with `localhost` baked in would mean every API call from a real
visitor's browser tries to reach *their own machine*, not the server, and fails silently.

```bash
cd frontend
npm ci
npm run build
```

This outputs static files to `frontend/dist/`. `npm ci` (not `npm install`) installs exactly what
`package-lock.json` specifies — reproducible on a server.

`npm run build` runs in the foreground and returns the prompt when done — it's not a server, so
there's no need to background it or open a second terminal for it to complete. But on a free-tier
`t2.micro`/`t3.micro` (1 GB RAM), the TypeScript compile can be slow, or even get silently
OOM-killed. If it's stuck far longer than expected, open a **separate SSH session** and check
`free -h` / `top` — if the original session already dropped back to a prompt with `Killed` printed,
that's the OOM killer, not a hang. Fix with temporary swap if needed:

```bash
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

Then retry the build. Sanity-check the output before moving on:

```bash
grep -r "localhost:8000" dist/ && echo "WARNING: localhost leaked into the build" || echo "clean"
ls dist/index.html   # confirms the build actually produced output
```

## 8. Install and configure Nginx

Nginx does two jobs: serves the built frontend's static files, and reverse-proxies `/api/` requests
to the backend running on `127.0.0.1:8000`.

Create `/etc/nginx/sites-available/filmgraph`:

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

`try_files $uri /index.html` matters because this is a client-side-routed SPA
(`react-router-dom`'s `<BrowserRouter>`): a direct browser visit to `/movies/mv1` is a real request
to Nginx for a path that doesn't exist as a file on disk. Without this fallback, that request 404s
at the Nginx level before React Router gets a chance to handle it — a "works when I click around,
breaks on refresh or direct link" bug.

**Watch for a home-directory permission trap.** Nginx's worker process runs as `www-data`, but
Ubuntu's default home directory permissions (`drwxr-x---`, owner-only) block `www-data` from even
*traversing into* `/home/ubuntu/`. The symptom is distinctive: `/api/...` requests work fine (that's
proxied straight to the backend, never touches the filesystem), but `/` — and every static file —
serves Nginx's own 500 error page, even though `nginx -t` passes and the reload succeeds. Confirm
with:

```bash
sudo tail -30 /var/log/nginx/error.log
```

`(13: Permission denied)` confirms it. Fix by opening traverse access on the parent directories:

```bash
sudo chmod o+x /home/ubuntu /home/ubuntu/filmgraph /home/ubuntu/filmgraph/frontend
sudo chmod -R o+rX /home/ubuntu/filmgraph/frontend/dist
```

(A `rewrite or internal redirection cycle` message instead means `dist/index.html` doesn't exist at
all — usually because `npm run build` didn't finish; see step 7's OOM note.)

Enable the site (a symlink into `sites-enabled` — creating the file in `sites-available` alone does
nothing):

```bash
sudo ln -s /etc/nginx/sites-available/filmgraph /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

`nginx -t` validates the config *before* reloading — always run it first, since reloading a broken
config takes the whole site down.

## 9. HTTPS (optional at this stage)

This project's security requirements call for HTTPS everywhere, but that applies once there's a
real login/JWT flow — this narrow read-only slice has no auth yet. Let's Encrypt's automated
certificates (via `certbot`) require a domain, not a bare IP:

- **If you have a domain pointed at the Elastic IP:**
  ```bash
  sudo apt install -y certbot python3-certbot-nginx
  sudo certbot --nginx -d yourdomain.com
  ```
  `certbot` edits the Nginx config to add the certificate and a redirect from 80→443, and sets up
  automatic renewal. Update the security group to also allow inbound **443**.
- **If you're only testing against the raw EC2 IP:** skip this until a domain exists.

## 10. Verify end-to-end

1. Visit `http://<elastic-ip-or-domain>/` in a browser — confirm the movie list loads.
2. Open browser dev tools → Network tab, confirm API calls go to `/api/movies` on the **same
   origin** as the page (no separate `localhost:8000`, no CORS errors).
3. Click into a movie and a star, confirm cross-navigation works.
4. **Refresh the page while on `/movies/mv1` directly** (not by clicking there) — this tests the
   `try_files` fallback from step 8; if it 404s, that config is the first thing to recheck.
5. On the instance: `sudo systemctl status filmgraph-api` and `sudo systemctl status nginx` should
   both show `active (running)`.
6. Confirm in the AWS Console that the security group still shows only 22 (your IP), 80, and (if
   applicable) 443 open — nothing else.

## 11. Redeploying after changes

Run these in order. Steps 2 and 3 are cheap, idempotent, and **not optional** — every failed deploy
so far has been the server disagreeing with the repo, with nothing checking.

### 11.1 Pull

```bash
ssh -i your-key.pem ubuntu@<elastic-ip>
cd ~/filmgraph
git pull
```

`git pull` here puts whatever is on `main` straight onto a running production service, which is why
every commit on `main` should leave the app in a working state.

### 11.2 Sync backend dependencies — every time, not conditionally

```bash
cd ~/filmgraph/backend
source .venv/bin/activate
pip install -e .
```

Run this on every deploy, including the ones where you're sure nothing changed. It's idempotent and
takes seconds when there's nothing to do. The conditional version ("only if dependencies changed")
is a trap: it's only safe if the server was already in sync, and nothing verifies that. A stale venv
is what produced `ModuleNotFoundError: itsdangerous` at worker boot.

### 11.3 Check `.env` against `.env.example`

```bash
diff <(grep -oE '^[A-Z_]+' .env.example | sort) <(grep -oE '^[A-Z_]+' .env | sort)
```

No output means the server has every key the repo expects. A line starting with `<` is a variable
the repo template defines and the server is missing. `app/config.py` gives `JWT_SECRET_KEY` and
`SESSION_SECRET_KEY` no defaults, so a missing key is a Pydantic `ValidationError` at import — the
app never starts and every request 500s or hangs. Generate anything missing, **one secret at a
time**:

```bash
[ -n "$(tail -c1 .env)" ] && echo >> .env      # don't glue the key onto the last line
python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(48))" >> .env
python3 -c "import secrets; print('SESSION_SECRET_KEY=' + secrets.token_urlsafe(48))" >> .env
chmod 600 .env
```

Never reuse one value for both — they sign different things (JWT = identity, session cookie = cart),
so a shared secret means a weakness in either compromises both. `token_urlsafe` is deliberate over
`openssl rand -base64`: it emits only `[A-Za-z0-9_-]`, with nothing systemd's `EnvironmentFile`
parser could misread as quoting.

### 11.4 Restart the backend and prove it booted

```bash
sudo systemctl restart filmgraph-api
sudo systemctl status filmgraph-api        # want "active (running)"
curl -i http://127.0.0.1:8000/health       # want 200 — this is the real gate
```

`active (running)` only means systemd started a process. `/health` returning 200 is the only thing
that proves the app imported its settings, reached MySQL, and can serve a request.

### 11.5 Rebuild the frontend — only if frontend code changed

```bash
free -h        # if Swap shows 0B, add swap (step 7) before building
cd ~/filmgraph/frontend
npm ci
npm run build
grep -r "localhost:8000" dist/ && echo "WARNING: localhost leaked into the build" || echo "clean"
```

No service restart needed — Nginx serves whatever is in `dist/` on the next request. On a 1 GB
`t2.micro`/`t3.micro` the TypeScript compile is the step most likely to be OOM-killed; see step 7.

### 11.6 Watch the logs while you click through

```bash
sudo journalctl -u filmgraph-api -f
```

Leave this running in a second SSH session while you exercise the site in a browser. With
`--access-logfile -` on the unit (step 6), every request appears here with its status code.

## Troubleshooting checklist

### Reading the logs

Start here, not with guesses. The API logs to the systemd journal:

```bash
sudo journalctl -u filmgraph-api -f                    # follow live
sudo journalctl -u filmgraph-api -n 100 --no-pager     # last 100 lines
sudo journalctl -u filmgraph-api -p err --no-pager     # errors only
sudo journalctl -u filmgraph-api --since "10 min ago" --no-pager
sudo tail -f /var/log/nginx/error.log                  # 500s that never reached the app
sudo tail -f /var/log/nginx/access.log
```

If the API journal is empty while requests are clearly arriving, the request isn't reaching the app
at all — check Nginx's logs and the `proxy_pass` target (step 8).

### Mistakes worth checking first

Each one can leave the app looking "almost working":

- Security group or MySQL `bind-address` exposing the database to the public internet (steps 1, 4).
- `EnvironmentFile` missing from the systemd unit, so the app can't find `DATABASE_URL` and
  crash-loops (step 6).
- `frontend/.env.production` missing or wrong, so the build falls back to `localhost` (step 7) —
  the `grep dist/` check in that step catches this before you ship it.
- Nginx site created in `sites-available` but never symlinked into `sites-enabled` (step 8).
- Missing the SPA fallback (`try_files ... /index.html`), which breaks direct/refreshed links to
  `/movies/:id` and `/stars/:id` even though in-app navigation still works (step 8).
- `root` under `/home/ubuntu/` blocked by default home-directory permissions, so `www-data` can't
  traverse to `dist/` — `/api/...` works fine, but `/` serves a 500. Check
  `/var/log/nginx/error.log` for `(13: Permission denied)` (step 8).
- No Elastic IP, so the public address changes on every stop/start (step 1).
- Installing packages before enabling the `universe` apt component, producing `Unable to locate
  package` errors for `python3-pip`, `python3-venv`, `nodejs`, and `npm` (step 3).
- Reusing the local dev database password in production (step 4).
- Server `.env` drifted from `.env.example`, so a required setting has no value and `Settings` fails
  Pydantic validation at import — the service crash-loops and every request 500s or hangs. The
  `diff` in step 11.3 catches this in one command (step 11).
- Server venv drifted from `pyproject.toml`, producing `ModuleNotFoundError` at worker boot. The
  unconditional `pip install -e .` in step 11.2 prevents it (step 11).
