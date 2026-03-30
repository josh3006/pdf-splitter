import os
import shutil
import tempfile
import subprocess
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash

app = Flask(__name__)
# NOTE: For demo purposes only. In production, set via environment variable.
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")

USERNAME = os.environ.get("APP_USERNAME", "admin")
PASSWORD = os.environ.get("APP_PASSWORD", "password123")


def login_required(view_func):
    from functools import wraps

    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapped


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if username == USERNAME and password == PASSWORD:
            session["logged_in"] = True
            session["username"] = username
            return redirect(url_for("index"))
        flash("Invalid username or password", "error")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/", methods=["GET"]) 
@login_required
def index():
    return render_template("index.html")


@app.route("/split", methods=["POST"]) 
@login_required
def split_pdf():
    if "pdf" not in request.files:
        flash("No file part named 'pdf' in the form.", "error")
        return redirect(url_for("index"))

    file = request.files["pdf"]
    if file.filename == "":
        flash("No selected file.", "error")
        return redirect(url_for("index"))

    if not file.filename.lower().endswith(".pdf"):
        flash("Only PDF files are allowed.", "error")
        return redirect(url_for("index"))

    tmp_dir = tempfile.mkdtemp(prefix="pdfsplit_")
    input_path = os.path.join(tmp_dir, file.filename)

    try:
        file.save(input_path)

        # Build output pattern using a fixed literal as requested.
        # Example result: file-xxxxxxx-1.pdf, file-xxxxxxx-2.pdf, ...
        output_prefix = "file-xxxxxxx-"
        output_pattern = os.path.join(tmp_dir, output_prefix + "%d.pdf")

        # Call pdfseparate to split the PDF into single-page PDFs.
        # pdfseparate <input> <output-pattern>
        try:
            completed = subprocess.run(
                ["pdfseparate", input_path, output_pattern],
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError:
            flash("'pdfseparate' not found. Ensure poppler-utils is installed in the environment.", "error")
            return redirect(url_for("index"))

        if completed.returncode != 0:
            flash(f"Failed to split PDF. stderr: {completed.stderr}", "error")
            return redirect(url_for("index"))

        # Create a zip archive containing only the split PDFs
        zip_path = os.path.join(tmp_dir, "output.zip")

        import zipfile

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for p in sorted(Path(tmp_dir).glob(f"{output_prefix}*.pdf")):
                zf.write(p, arcname=p.name)

        if not os.path.exists(zip_path):
            flash("Failed to create output.zip", "error")
            return redirect(url_for("index"))

        # Stream the zip to the client. Clean-up of temp folder after sending is tricky; we'll rely on OS cleanup
        # or you can add a background job. For now we remove the tmp_dir after sending by using 'as_attachment' stream.
        return send_file(zip_path, as_attachment=True, download_name="output.zip")

    finally:
        # Best effort cleanup: remove everything except if we're in the middle of sending.
        # Since send_file may start streaming immediately, delaying cleanup could break the response. We'll avoid
        # deleting right away here. In a more advanced setup, use a background cleanup scheduler.
        pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port, debug=False)
