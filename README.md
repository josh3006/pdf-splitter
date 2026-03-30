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
## Notes

- This app is intentionally simple and uses hard-coded naming per requirement. If you prefer using the input file name as a prefix, you can adjust `output_pattern` in `app.py`.
- Temporary files are stored in a temp directory per request and not persisted.
- For production use, consider adding CSRF protection, HTTPS, and persistent storage if needed.