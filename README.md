# 🚚 Mobile Delivery Manager — Web App

Full-stack delivery management system built with **Python Flask + SQLite**.

## Quick Start

### 1. Install Python dependencies
```bash
pip install flask flask-cors
```

### 2. Run the server
```bash
python app.py
```

### 3. Open your browser
```
http://localhost:5000
```

That's it! The database (`delivery.db`) is created automatically on first run with sample data.

---

## Features

| Module | Description |
|--------|-------------|
| **Dashboard** | Live KPIs, status chart, driver workload, recent jobs |
| **Jobs** | Full CRUD — create, edit, delete, search & filter jobs |
| **Schedule** | Monthly calendar with jobs shown per day, click to filter |
| **Drivers** | Driver roster management with job count tracking |
| **Customers** | Customer database with auto-fill on job creation |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/dashboard` | KPIs, charts, recent jobs |
| GET/POST | `/api/jobs` | List / create jobs |
| GET/PUT/DELETE | `/api/jobs/<id>` | Get / update / delete job |
| GET/POST | `/api/drivers` | List / create drivers |
| GET/PUT/DELETE | `/api/drivers/<id>` | Get / update / delete driver |
| GET/POST | `/api/customers` | List / create customers |
| GET/PUT/DELETE | `/api/customers/<id>` | Get / update / delete customer |
| GET | `/api/schedule?year=&month=` | Jobs for a given month |
| GET/PUT | `/api/settings` | System settings |

## File Structure

```
delivery-app/
├── app.py              ← Flask server + all API routes
├── delivery.db         ← SQLite database (auto-created)
├── templates/
│   └── index.html      ← Main HTML page
└── static/
    ├── css/main.css    ← All styles
    └── js/app.js       ← Frontend JavaScript
```

## Deploying to a Server

1. Upload all files to your server
2. Install: `pip install flask flask-cors gunicorn`
3. Run with Gunicorn: `gunicorn -w 4 -b 0.0.0.0:5000 app:app`
4. Set up Nginx to proxy port 5000

## Customization

- **Add fields**: Edit the `CREATE TABLE` in `app.py` and update the form in `index.html`
- **Change colors**: Edit CSS variables at the top of `static/css/main.css`
- **Add pages**: Add a new `<section class="page">` in HTML, a nav item, and a load function in `app.js`
