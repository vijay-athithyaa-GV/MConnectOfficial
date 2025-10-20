# MConnect – Campus Marketplace (Flask)

A simple campus marketplace web app built with Flask and SQLAlchemy. Students can list items for sale, browse available listings, search by keyword/category, and submit purchase requests. Email usage is restricted to a configurable domain (e.g., `@college.edu`).

## Project Structure

```
MainCloudProject/
├─ mconnect/
│  ├─ app.py                 # Flask app entrypoint
│  ├─ requirements.txt       # Python dependencies
│  ├─ templates/             # Jinja2 templates (UI)
│  │  ├─ index.html
│  │  ├─ upload.html
│  │  ├─ my_listings.html
│  │  └─ product_detail.html
│  ├─ static/                # CSS/JS assets
│  │  ├─ style.css
│  │  └─ script.js
│  ├─ uploads/               # Uploaded images (runtime)
│  ├─ database.db            # SQLite DB (runtime; can move via DATA_DIR)
│  ├─ _deploy/               # Deployment helpers (optional)
│  └─ .venv/                 # Local virtual env (optional)
├─ makeZip.py                # Utility script (optional)
└─ README.md                 # This file
```

## Features

- **List items for sale**: Upload image, name, category, description, price.
- **Browse and search**: Filter by keyword and category.
- **Product details**: View item details and related items by category.
- **Purchase requests**: Buyers submit interest to sellers.
- **Seller tools**: View your listings and mark items as sold.
- **Email domain restriction**: Only emails ending with your configured domain can interact.
- **Health check**: `GET /healthz` returns `{ "status": "ok" }`.

## Tech Stack

- **Backend**: Python, Flask (`mconnect/app.py`)
- **Database**: SQLite via Flask-SQLAlchemy
- **Templates**: Jinja2 (`mconnect/templates/`)
- **Static Assets**: CSS/JS in `mconnect/static/`

## Requirements

- Python 3.10+ recommended
- pip
- Windows PowerShell or any shell

Python dependencies (from `mconnect/requirements.txt`):
- Flask==3.0.3
- Flask-SQLAlchemy==3.1.1
- Werkzeug==3.0.4
- gunicorn==21.2.0 (for Linux production; not used on Windows)

## Getting Started (Local Development)

### 1) Clone the repository

```bash
# using HTTPS
git clone <YOUR_GIT_REMOTE_URL> MainCloudProject

# or using SSH
git clone git@github.com:<your-org>/<your-repo>.git MainCloudProject
```

### 2) Create and activate a virtual environment (Windows)

```powershell
python -m venv .venv
.venv\Scripts\activate
```

On macOS/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3) Install dependencies

```bash
pip install -r mconnect/requirements.txt
```

### 4) Configure environment variables (optional but recommended)

Create a `.env` file or export in your shell before running. Common vars:

- `SECRET_KEY`: Flask secret key. Example: `SECRET_KEY="change-me"`.
- `ALLOWED_EMAIL_DOMAIN`: Restrict emails to this domain. Default: `college.edu`.
- `DATABASE_URL`: SQLAlchemy URI. Default is SQLite in `DATA_DIR/database.db`.
  - Examples: `sqlite:///C:/path/to/database.db`, `postgresql+psycopg2://user:pass@host:5432/db`.
- `DATA_DIR`: Writable directory for runtime data (uploads, SQLite). Default: `mconnect/`.

You can set these in PowerShell for the current session:
```powershell
$env:SECRET_KEY = "change-me"
$env:ALLOWED_EMAIL_DOMAIN = "mycollege.edu"
# Optional: custom data dir
$env:DATA_DIR = "C:\\temp\\mconnect-data"
```

### 5) Run the app (development server)

```bash
# from the project root
python mconnect/app.py
```

- The app starts in debug mode on `http://127.0.0.1:5000/`.
- On first run, tables are auto-created in the SQLite DB.
- Uploaded images are saved under `<DATA_DIR>/uploads`.

## Usage Guide

- **Home/Buy**: `GET /` redirects to `GET /buy` to browse items.
- **Search**: `GET /search?q=<keyword>&category=<name>`.
- **Upload**: `GET/POST /upload` to create a listing.
- **My Listings**: `GET /my-listings?seller_email=<your_email@domain>`.
- **Product Detail**: `GET /product/<id>`.
- **Request to Buy**: `POST /product/<id>/buy` with `buyer_name`, `buyer_email`, `message`.
- **Mark as Sold**: `POST /product/<id>/mark_sold` with `seller_email_confirm`.
- **Health**: `GET /healthz`.

## Data & File Locations

- **Database**: Defaults to SQLite at `<DATA_DIR>/database.db`.
- **Uploads**: Saved to `<DATA_DIR>/uploads`.
- **Static assets**: Served from `mconnect/static/`.
- **Templates**: Located in `mconnect/templates/`.

On Azure App Service (Linux), the app auto-detects writable directories and uses `/home/site/data` for `DATA_DIR`.

## Production Deployment Notes

- Gunicorn is included and suitable for Linux hosts. Example command (Linux only):
  ```bash
  gunicorn -w 2 -k gthread -b 0.0.0.0:8000 app:app --chdir mconnect
  ```
- Ensure environment variables are set in your hosting platform.
- Persist `DATA_DIR` on a writable volume.
- For reverse proxy (Nginx/Apache), proxy to the Gunicorn port.

### Azure App Service (General Guidance)

- Deploy the `mconnect/` folder as the app root.
- App auto-resolves templates and static paths for Azure.
- Set `WEBSITE_RUN_FROM_PACKAGE` or use a deployment pipeline of your choice.
- Configure App Settings for `SECRET_KEY`, `ALLOWED_EMAIL_DOMAIN`, and optionally `DATABASE_URL`.

## Troubleshooting

- **Module not found / ImportError**: Ensure venv is activated and requirements installed.
- **Database locked (SQLite)**: Close other processes. Consider a server DB (Postgres) for multi-user writes.
- **Uploads not appearing**: Verify `DATA_DIR` exists and the process has write permissions.
- **Email domain blocked**: Set `ALLOWED_EMAIL_DOMAIN` to your institution domain.
- **Windows & Gunicorn**: Use Flask dev server for local Windows development; Gunicorn is for Linux servers.

## Development Tips

- Run with debug auto-reload using the provided `if __name__ == '__main__'` in `mconnect/app.py`.
- Update UI in `mconnect/templates/` and `mconnect/static/`.
- Database models are in `mconnect/app.py` (`Product`, `PurchaseRequest`).

## Security Notes

- Always set a strong `SECRET_KEY` in production.
- Validate and sanitize file uploads. Only image types `png, jpg, jpeg, gif, webp` are allowed.
- Consider using a managed database (Postgres/MySQL) for production.

## License

Specify your license here (e.g., MIT). If omitted, the default is "all rights reserved".
