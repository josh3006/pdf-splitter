# PDF Splitter (Dockerized)

A minimal web application to split a PDF into individual pages using the Linux tool `pdfseparate` and download the results as a single `output.zip` file. The app includes a basic login screen.

- Default login: `admin` / `password123`
- Splitting command used under the hood: `pdfseparate <input.pdf> file-xxxxxxx-%d.pdf`

## Features

- Simple authentication (session-based; single user)
- Upload a PDF and split it server-side using `pdfseparate` (from poppler-utils)
- Download all split pages as `output.zip`
- Ready-to-run Docker image

## Quick start with Docker

Prerequisites: Docker Desktop or Docker Engine installed.

1) Build the image

```bash
docker build -t pdf-splitter .
```

2) Run the container

- Foreground (press Ctrl+C to stop):
```bash
docker run -p 8080:8080 --name pdf-splitter pdf-splitter
```

- Detached/background (with auto-restart on reboot):
```bash
docker run -d --restart unless-stopped -p 8080:8080 --name pdf-splitter pdf-splitter
```

3) Open the app
- Visit http://localhost:8080
- Login with username `admin` and password `password123`

4) Stop the container (if running detached)
```bash
docker stop pdf-splitter
```

## Keep it running across reboots

- Use `--restart unless-stopped`, as shown above, so Docker restarts it after host reboots and on crashes.
- If you already created the container without a restart policy, set it without recreating it:

```bash
docker update --restart unless-stopped pdf-splitter
```

- To disable auto-restart later:

```bash
docker update --restart no pdf-splitter
```

Optional: run with custom credentials and secret key (persistent)
```bash
docker run -d --restart unless-stopped -p 8080:8080 \
  -e APP_USERNAME=myuser -e APP_PASSWORD=mypass \
  -e FLASK_SECRET_KEY=change-me \
  --name pdf-splitter pdf-splitter
```

For a one-off/dev run that cleans up automatically, add `--rm` and omit the restart policy.

Optional: bind-mount source code for quick iteration (no rebuild)
- Linux/macOS:
```bash
docker run --rm -p 8080:8080 -v "$PWD":/app --name pdf-splitter pdf-splitter
```
- Windows PowerShell:
```powershell
docker run --rm -p 8080:8080 -v "${PWD}:/app" --name pdf-splitter pdf-splitter
```

## Environment variables

- APP_USERNAME: default `admin`
- APP_PASSWORD: default `password123`
- FLASK_SECRET_KEY: secret for Flask session cookies (set this in production)
- PORT: default `8080`

Example with custom credentials (persistent):
   docker run -d --restart unless-stopped -p 8080:8080 -e APP_USERNAME=myuser -e APP_PASSWORD=mypass --name pdf-splitter pdf-splitter

## How it works

- After login, upload a PDF file.
- The backend invokes:
  pdfseparate <your-input.pdf> file-xxxxxxx-%d.pdf
  substituting your uploaded file for the input name.
- The generated files named like `file-xxxxxxx-1.pdf`, `file-xxxxxxx-2.pdf`, ... are collected and zipped as `output.zip` and returned.

## Development (without Docker)

Requirements: Python 3.11+, poppler-utils installed (for `pdfseparate`). On Ubuntu/Debian:
   sudo apt-get update && sudo apt-get install -y poppler-utils

Setup and run:
   pip install -r requirements.txt
   set FLASK_SECRET_KEY=dev
   set APP_USERNAME=admin
   set APP_PASSWORD=password123
   python app.py

Then open http://localhost:8080

## Production release
Rebuild and start the container

Rebuild with new .env
```
docker compose build --no-cache
```
Start the container
```
docker compose up -d
```
Verify it's running
```
docker compose ps
docker compose logs
```

## GitHub Actions deployment

The repository includes `.github/workflows/deploy.yml` for RackNerd Docker deployment.

Required GitHub repository secrets:

```text
PROD_SSH_HOST=155.94.157.140
PROD_SSH_USER=root
PROD_SSH_PRIVATE_KEY=private SSH key with server access
PROD_DEPLOY_PATH=/opt/eqlsquare/pdf-splitter
APP_PASSWORD=strong login password
FLASK_SECRET_KEY=long random Flask session secret
```

Optional GitHub repository variables:

```text
APP_USERNAME=admin
APP_PORT=8081
PROXY_NETWORK=proxy
COMPOSE_PROJECT_NAME=pdfsplitter
NGINX_DEPLOY_PATH=/opt/eqlsquare/payslip/nginx
WEB_CONCURRENCY=2
GUNICORN_TIMEOUT=120
```

The app deploys to the shared Docker network as `pdfsplitter-app`. The existing shared Nginx reverse proxy should forward `pdfsplitter.eqlsquare.com` to:

```text
http://pdfsplitter-app:8080
```

To activate the Nginx config on the server:

```bash
cd /opt/eqlsquare/payslip/nginx
cp templates/pdfsplitter.http.conf conf.d/pdfsplitter.conf
docker compose exec nginx nginx -t
docker compose exec nginx nginx -s reload
```

After DNS points `pdfsplitter.eqlsquare.com` to the server, issue the certificate:

```bash
docker compose run --rm certbot certonly --webroot --webroot-path /var/www/certbot -d pdfsplitter.eqlsquare.com --email YOUR_EMAIL --agree-tos --no-eff-email
cp templates/pdfsplitter.https.conf conf.d/pdfsplitter.conf
docker compose exec nginx nginx -t
docker compose exec nginx nginx -s reload
```
## Notes

- This app is intentionally simple and uses hard-coded naming per requirement. If you prefer using the input file name as a prefix, you can adjust `output_pattern` in `app.py`.
- Temporary files are stored in a temp directory per request and not persisted.
- For production use, consider adding CSRF protection, HTTPS, and persistent storage if needed.
