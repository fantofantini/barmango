"""
Mobile Delivery Manager — Flask Backend
Full REST API with SQLite database
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import sqlite3, os, json
from datetime import datetime

import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__, static_folder=os.path.join(BASE_DIR, 'client'), static_url_path='')
CORS(app)

DB_PATH = os.path.join(BASE_DIR, 'db', 'delivery.db')

# ── Database ────────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # PRAGMA foreign_keys set after seeding
    return conn

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db()
    c = conn.cursor()

    c.executescript("""
    CREATE TABLE IF NOT EXISTS drivers (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT NOT NULL,
        phone       TEXT,
        email       TEXT,
        address     TEXT,
        city        TEXT,
        state       TEXT,
        zip         TEXT,
        notes       TEXT,
        photo       TEXT,
        created_at  TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS customers (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT NOT NULL,
        phone       TEXT,
        email       TEXT,
        address     TEXT,
        city        TEXT,
        state       TEXT,
        zip         TEXT,
        created_at  TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS jobs (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id  INTEGER REFERENCES customers(id),
        driver_id    INTEGER REFERENCES drivers(id),
        status       TEXT DEFAULT 'Pendiente',
        pu_address   TEXT,
        pu_date      TEXT,
        pu_time      TEXT,
        del_address  TEXT,
        del_date     TEXT,
        del_time     TEXT,
        signature    TEXT,
        del_picture  TEXT,
        costo_servicio REAL DEFAULT 0,
        ubicacion    TEXT DEFAULT '',
        notes        TEXT,
        created_at   TEXT DEFAULT (datetime('now')),
        updated_at   TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS settings (
        key   TEXT PRIMARY KEY,
        value TEXT
    );
    """)
    conn.commit()

    # Seed sample data if empty
    if c.execute("SELECT COUNT(*) FROM drivers").fetchone()[0] == 0:
        seed_data(conn)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.close()

def seed_data(conn):
    c = conn.cursor()

    drivers = [
        ("Carlos Mendoza","099-123-4567","cmendoza@barmango.ec","Av. Colón 123","Quito","Pichincha","170101",""),
        ("María Rodríguez","098-234-5678","mrodriguez@barmango.ec","Calle Sucre 456","Guayaquil","Guayas","090101",""),
        ("Luis Toapanta","097-345-6789","ltoapanta@barmango.ec","Av. Amazonas 789","Quito","Pichincha","170102",""),
        ("Ana Guamán","096-456-7890","aguaman@barmango.ec","Calle Bolívar 321","Cuenca","Azuay","010101",""),
        ("Roberto Sánchez","095-567-8901","rsanchez@barmango.ec","Av. 9 de Octubre 654","Guayaquil","Guayas","090102",""),
        ("Gabriela Vega","094-678-9012","gvega@barmango.ec","Calle Tarqui 987","Riobamba","Chimborazo","060101",""),
    ]
    c.executemany("INSERT INTO drivers (name,phone,email,address,city,state,zip,notes) VALUES (?,?,?,?,?,?,?,?)", drivers)

    customers = [
        ("Andrés Morales","099-111-2233","amorales@gmail.com","Av. Patria 100","Quito","Pichincha","170101"),
        ("Lucía Herrera","098-222-3344","lherrera@gmail.com","Calle Olmedo 200","Guayaquil","Guayas","090101"),
        ("Diego Alvarado","097-333-4455","dalvarado@gmail.com","Av. Huayna Cápac 300","Cuenca","Azuay","010101"),
        ("Sofía Castillo","096-444-5566","scastillo@gmail.com","Calle Sucre 400","Ambato","Tungurahua","180101"),
        ("Mateo Vargas","095-555-6677","mvargas@gmail.com","Av. Remigio Crespo 500","Cuenca","Azuay","010102"),
        ("Valentina Ríos","094-666-7788","vrios@gmail.com","Calle García Moreno 600","Loja","Loja","110101"),
        ("Fernando Pazos","093-777-8899","fpazos@gmail.com","Av. Quito 700","Manta","Manabí","130101"),
        ("Isabella Núñez","092-888-9900","inunez@gmail.com","Calle Tarqui 800","Riobamba","Chimborazo","060101"),
    ]
    c.executemany("INSERT INTO customers (name,phone,email,address,city,state,zip) VALUES (?,?,?,?,?,?,?)", customers)

    jobs = [
        (1,1,"Pending",   "100 Sunset Blvd, LA",     "2025-05-01","09:00","200 Main St, Culver City",    "2025-05-01","14:00","","","Handle with care"),
        (2,2,"Scheduled", "200 Ocean Drive, SM",      "2025-05-02","10:00","300 Oak Ave, Burbank",         "2025-05-02","15:00","","","Call before delivery"),
        (3,3,"Picked Up", "300 Hollywood Blvd, HW",   "2025-05-03","08:30","400 Pine Rd, Pasadena",        "2025-05-03","13:00","","","Fragile item"),
        (4,1,"Delivered", "400 Venice Blvd, Venice",  "2025-05-04","09:00","500 Elm St, Torrance",         "2025-05-04","14:30","","","Left at front door"),
        (5,4,"Closed",    "500 Wilshire Blvd, BH",    "2025-05-05","11:00","600 Maple Dr, Glendale",       "2025-05-05","16:00","","","Complete"),
        (6,2,"Pending",   "600 Melrose Ave, WH",      "2025-05-06","09:30","700 Cedar Ln, Santa Monica",   "2025-05-06","14:00","","",""),
        (7,3,"Scheduled", "700 Santa Monica Blvd",    "2025-05-07","10:00","800 Birch Blvd, Culver City",  "2025-05-07","15:30","","",""),
        (8,5,"Picked Up", "800 La Brea Ave, LA",      "2025-05-08","08:00","900 Walnut Way, Burbank",      "2025-05-08","13:00","","",""),
        (9,1,"Pending",   "123 Business Park, LA",    "2025-05-10","09:00","100 Wilshire Blvd, LA",        "2025-05-10","14:00","","",""),
        (10,2,"Scheduled","456 Commerce Blvd, SM",    "2025-05-11","10:30","200 Sunset Blvd, LA",          "2025-05-11","16:00","","",""),
        (11,6,"Pending",  "789 Rodeo Dr, BH",         "2025-05-12","09:00","300 Pico Blvd, Santa Monica",  "2025-05-12","14:00","","",""),
        (12,4,"Delivered","321 Vine St, Hollywood",   "2025-05-13","10:00","400 Cahuenga Blvd, Hollywood", "2025-05-13","15:00","","","Delivered on time"),
    ]
    c.executemany("""INSERT INTO jobs (customer_id,driver_id,status,pu_address,pu_date,pu_time,
                     del_address,del_date,del_time,signature,del_picture,notes)
                     VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""", jobs)

    c.executemany("INSERT OR IGNORE INTO settings (key,value) VALUES (?,?)", [
        ("company_name", "BarManGo"),
        ("address_1", "Av. Amazonas N24-196, Quito, Ecuador"),
        ("address_2", "Av. 9 de Octubre 100, Guayaquil, Ecuador"),
    ])
    conn.commit()

def row_to_dict(row):
    return dict(row) if row else None

def rows_to_list(rows):
    return [dict(r) for r in rows]

# ── API: Jobs ───────────────────────────────────────────────────────────────
@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    conn = get_db()
    status  = request.args.get('status', '')
    search  = request.args.get('search', '')
    pu_date = request.args.get('pu_date', '')

    query = """
        SELECT j.*, c.name as customer_name, c.phone as customer_phone,
               d.name as driver_name
        FROM jobs j
        LEFT JOIN customers c ON j.customer_id = c.id
        LEFT JOIN drivers   d ON j.driver_id   = d.id
        WHERE 1=1
    """
    params = []
    if status:
        query += " AND j.status = ?"; params.append(status)
    if search:
        query += " AND (c.name LIKE ? OR d.name LIKE ? OR CAST(j.id AS TEXT) LIKE ?)"
        params += [f'%{search}%', f'%{search}%', f'%{search}%']
    if pu_date:
        query += " AND j.pu_date = ?"; params.append(pu_date)

    query += " ORDER BY j.id DESC"
    jobs = rows_to_list(conn.execute(query, params).fetchall())
    conn.close()
    return jsonify(jobs)

@app.route('/api/jobs/<int:job_id>', methods=['GET'])
def get_job(job_id):
    conn = get_db()
    row = conn.execute("""
        SELECT j.*, c.name as customer_name, c.phone as customer_phone,
               c.email as customer_email, c.address as customer_address,
               c.city as customer_city, c.state as customer_state,
               d.name as driver_name
        FROM jobs j
        LEFT JOIN customers c ON j.customer_id = c.id
        LEFT JOIN drivers   d ON j.driver_id   = d.id
        WHERE j.id = ?""", (job_id,)).fetchone()
    conn.close()
    if not row: return jsonify({'error': 'Not found'}), 404
    return jsonify(row_to_dict(row))

@app.route('/api/jobs', methods=['POST'])
def create_job():
    data = request.json
    conn = get_db()
    cur = conn.execute("""
        INSERT INTO jobs (customer_id, driver_id, status, pu_address, pu_date, pu_time,
                          del_address, del_date, del_time, signature, del_picture, notes, costo_servicio)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (data.get('customer_id'), data.get('driver_id'), data.get('status','Pendiente'),
         data.get('pu_address',''), data.get('pu_date',''), data.get('pu_time',''),
         data.get('del_address',''), data.get('del_date',''), data.get('del_time',''),
         data.get('signature',''), data.get('del_picture',''), data.get('notes',''),
         data.get('costo_servicio', 0),
         data.get('ubicacion', '')))
    conn.commit()
    job_id = cur.lastrowid
    conn.close()
    return jsonify({'id': job_id, 'message': 'Job created'}), 201

@app.route('/api/jobs/<int:job_id>', methods=['PUT'])
def update_job(job_id):
    data = request.json
    conn = get_db()
    conn.execute("""
        UPDATE jobs SET customer_id=?, driver_id=?, status=?, pu_address=?, pu_date=?,
                        pu_time=?, del_address=?, del_date=?, del_time=?, signature=?,
                        del_picture=?, notes=?, updated_at=datetime('now')
        WHERE id=?""",
        (data.get('customer_id'), data.get('driver_id'), data.get('status'),
         data.get('pu_address'), data.get('pu_date'), data.get('pu_time'),
         data.get('del_address'), data.get('del_date'), data.get('del_time'),
         data.get('signature'), data.get('del_picture'), data.get('notes'), job_id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Updated'})

@app.route('/api/jobs/<int:job_id>', methods=['DELETE'])
def delete_job(job_id):
    conn = get_db()
    conn.execute("DELETE FROM jobs WHERE id=?", (job_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Deleted'})

# ── API: Drivers ────────────────────────────────────────────────────────────
@app.route('/api/drivers', methods=['GET'])
def get_drivers():
    conn = get_db()
    search = request.args.get('search', '')
    query = "SELECT d.*, COUNT(j.id) as job_count FROM drivers d LEFT JOIN jobs j ON j.driver_id = d.id"
    params = []
    if search:
        query += " WHERE d.name LIKE ? OR d.city LIKE ?"; params = [f'%{search}%', f'%{search}%']
    query += " GROUP BY d.id ORDER BY d.name"
    rows = rows_to_list(conn.execute(query, params).fetchall())
    conn.close()
    return jsonify(rows)

@app.route('/api/drivers/<int:did>', methods=['GET'])
def get_driver(did):
    conn = get_db()
    row = conn.execute("SELECT * FROM drivers WHERE id=?", (did,)).fetchone()
    conn.close()
    if not row: return jsonify({'error': 'Not found'}), 404
    return jsonify(row_to_dict(row))

@app.route('/api/drivers', methods=['POST'])
def create_driver():
    data = request.json
    conn = get_db()
    cur = conn.execute("INSERT INTO drivers (name,phone,email,address,city,state,zip,notes) VALUES (?,?,?,?,?,?,?,?)",
        (data['name'], data.get('phone',''), data.get('email',''), data.get('address',''),
         data.get('city',''), data.get('state',''), data.get('zip',''), data.get('notes','')))
    conn.commit()
    conn.close()
    return jsonify({'id': cur.lastrowid}), 201

@app.route('/api/drivers/<int:did>', methods=['PUT'])
def update_driver(did):
    data = request.json
    conn = get_db()
    conn.execute("UPDATE drivers SET name=?,phone=?,email=?,address=?,city=?,state=?,zip=?,notes=? WHERE id=?",
        (data['name'], data.get('phone',''), data.get('email',''), data.get('address',''),
         data.get('city',''), data.get('state',''), data.get('zip',''), data.get('notes',''), did))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Updated'})

@app.route('/api/drivers/<int:did>', methods=['DELETE'])
def delete_driver(did):
    conn = get_db()
    conn.execute("DELETE FROM drivers WHERE id=?", (did,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Deleted'})

# ── API: Customers ──────────────────────────────────────────────────────────
@app.route('/api/customers', methods=['GET'])
def get_customers():
    conn = get_db()
    search = request.args.get('search', '')
    query = "SELECT c.*, COUNT(j.id) as job_count FROM customers c LEFT JOIN jobs j ON j.customer_id = c.id"
    params = []
    if search:
        query += " WHERE c.name LIKE ? OR c.email LIKE ?"; params = [f'%{search}%', f'%{search}%']
    query += " GROUP BY c.id ORDER BY c.name"
    rows = rows_to_list(conn.execute(query, params).fetchall())
    conn.close()
    return jsonify(rows)

@app.route('/api/customers/<int:cid>', methods=['GET'])
def get_customer(cid):
    conn = get_db()
    row = conn.execute("SELECT * FROM customers WHERE id=?", (cid,)).fetchone()
    conn.close()
    if not row: return jsonify({'error': 'Not found'}), 404
    return jsonify(row_to_dict(row))

@app.route('/api/customers', methods=['POST'])
def create_customer():
    data = request.json
    conn = get_db()
    cur = conn.execute("INSERT INTO customers (name,phone,email,address,city,state,zip) VALUES (?,?,?,?,?,?,?)",
        (data['name'], data.get('phone',''), data.get('email',''), data.get('address',''),
         data.get('city',''), data.get('state',''), data.get('zip','')))
    conn.commit()
    conn.close()
    return jsonify({'id': cur.lastrowid}), 201

@app.route('/api/customers/<int:cid>', methods=['PUT'])
def update_customer(cid):
    data = request.json
    conn = get_db()
    conn.execute("UPDATE customers SET name=?,phone=?,email=?,address=?,city=?,state=?,zip=? WHERE id=?",
        (data['name'], data.get('phone',''), data.get('email',''), data.get('address',''),
         data.get('city',''), data.get('state',''), data.get('zip',''), cid))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Updated'})

@app.route('/api/customers/<int:cid>', methods=['DELETE'])
def delete_customer(cid):
    conn = get_db()
    conn.execute("DELETE FROM customers WHERE id=?", (cid,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Deleted'})

# ── API: Dashboard Stats ────────────────────────────────────────────────────
@app.route('/api/stats', methods=['GET'])
def get_stats():
    conn = get_db()
    statuses = ['Pendiente','Programado','Recogido','Entregado','Cerrado']
    status_counts = {}
    for s in statuses:
        status_counts[s] = conn.execute("SELECT COUNT(*) FROM jobs WHERE status=?", (s,)).fetchone()[0]

    total_jobs      = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    total_drivers   = conn.execute("SELECT COUNT(*) FROM drivers").fetchone()[0]
    total_customers = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]

    top_drivers = rows_to_list(conn.execute("""
        SELECT d.name, COUNT(j.id) as job_count
        FROM drivers d LEFT JOIN jobs j ON j.driver_id = d.id
        GROUP BY d.id ORDER BY job_count DESC LIMIT 6""").fetchall())

    recent_jobs = rows_to_list(conn.execute("""
        SELECT j.id, j.status, j.pu_date, j.del_date, j.del_address,
               c.name as customer_name, d.name as driver_name
        FROM jobs j
        LEFT JOIN customers c ON j.customer_id = c.id
        LEFT JOIN drivers   d ON j.driver_id   = d.id
        ORDER BY j.id DESC LIMIT 8""").fetchall())

    total_ingresos = conn.execute("SELECT COALESCE(SUM(costo_servicio),0) FROM jobs").fetchone()[0]
    conn.close()
    return jsonify({
        'total_jobs': total_jobs,
        'total_ingresos': round(total_ingresos, 2),
        'total_drivers': total_drivers,
        'total_customers': total_customers,
        'status_counts': status_counts,
        'top_drivers': top_drivers,
        'recent_jobs': recent_jobs,
    })

# ── API: Schedule ───────────────────────────────────────────────────────────
@app.route('/api/schedule', methods=['GET'])
def get_schedule():
    year  = request.args.get('year',  datetime.now().year)
    month = request.args.get('month', datetime.now().month)
    conn = get_db()
    rows = rows_to_list(conn.execute("""
        SELECT j.id, j.status, j.pu_date, j.pu_time, j.del_date,
               c.name as customer_name, d.name as driver_name
        FROM jobs j
        LEFT JOIN customers c ON j.customer_id = c.id
        LEFT JOIN drivers   d ON j.driver_id   = d.id
        WHERE strftime('%Y', j.pu_date) = ? AND strftime('%m', j.pu_date) = ?
        ORDER BY j.pu_date, j.pu_time""",
        (str(year), str(month).zfill(2))).fetchall())
    conn.close()
    return jsonify(rows)

# ── API: Settings ───────────────────────────────────────────────────────────
@app.route('/api/settings', methods=['GET'])
def get_settings():
    conn = get_db()
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    conn.close()
    return jsonify({r['key']: r['value'] for r in rows})

@app.route('/api/settings', methods=['PUT'])
def update_settings():
    data = request.json
    conn = get_db()
    for key, value in data.items():
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)", (key, value))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Saved'})

# ── Serve frontend ──────────────────────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory('../client', 'index.html')

if __name__ == '__main__':
    init_db()
    print("\n🚚  Mobile Delivery Manager API")
    print("   Running at: http://localhost:5000\n")
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, port=port, host='0.0.0.0')
