"""
BarManGo — Flask Backend
Full REST API + Security (Users, Groups, Roles, Sessions)
"""

from flask import Flask, jsonify, request, send_from_directory, session
from flask_cors import CORS
import sqlite3, os, hashlib, secrets
from datetime import datetime
from functools import wraps

import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__, static_folder=os.path.join(BASE_DIR, 'client'), static_url_path='')
app.secret_key = os.environ.get('SECRET_KEY', 'barmango-secret-2025-xyz')
CORS(app, supports_credentials=True, origins=['http://localhost:5000','https://*.railway.app','https://*.up.railway.app'])

DB_PATH = os.path.join(BASE_DIR, 'db', 'delivery.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def row_to_dict(r):  return dict(r) if r else None
def rows_to_list(r): return [dict(x) for x in r]

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db()
    c = conn.cursor()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL UNIQUE,
        descripcion TEXT,
        permisos TEXT DEFAULT '{}',
        created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS grupos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL UNIQUE,
        descripcion TEXT,
        rol_id INTEGER REFERENCES roles(id),
        created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        username TEXT NOT NULL UNIQUE,
        email TEXT,
        password TEXT NOT NULL,
        grupo_id INTEGER REFERENCES grupos(id),
        activo INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now')),
        last_login TEXT
    );
    CREATE TABLE IF NOT EXISTS drivers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT, email TEXT, address TEXT, city TEXT, state TEXT, zip TEXT, notes TEXT, photo TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT, email TEXT, address TEXT, city TEXT, state TEXT, zip TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER REFERENCES customers(id),
        driver_id INTEGER REFERENCES drivers(id),
        status TEXT DEFAULT 'Pendiente',
        pu_address TEXT, pu_date TEXT, pu_time TEXT,
        del_address TEXT, del_date TEXT, del_time TEXT,
        signature TEXT, del_picture TEXT,
        costo_servicio REAL DEFAULT 0,
        ubicacion TEXT DEFAULT '',
        notes TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
    """)
    conn.commit()

    if c.execute("SELECT COUNT(*) FROM roles").fetchone()[0] == 0:
        # Roles
        c.executemany("INSERT INTO roles (nombre,descripcion,permisos) VALUES (?,?,?)", [
            ("Administrador","Acceso total al sistema",'{"admin":true,"jobs":true,"drivers":true,"customers":true,"reports":true,"security":true}'),
            ("Operador","Acceso operativo completo",'{"admin":false,"jobs":true,"drivers":true,"customers":true,"reports":true,"security":false}'),
            ("Mensajero","Solo encomiendas asignadas",'{"admin":false,"jobs":true,"drivers":false,"customers":false,"reports":false,"security":false}'),
            ("Supervisor","Visualización y reportes",'{"admin":false,"jobs":true,"drivers":true,"customers":true,"reports":true,"security":false}'),
        ])
        c.executemany("INSERT INTO grupos (nombre,descripcion,rol_id) VALUES (?,?,?)", [
            ("Administradores","Grupo administrativo",1),
            ("Operaciones","Equipo de operaciones",2),
            ("Mensajeros","Equipo en campo",3),
            ("Supervisores","Supervisión general",4),
        ])
        c.execute("INSERT INTO usuarios (nombre,username,email,password,grupo_id,activo) VALUES (?,?,?,?,?,?)",
            ("Administrador","admin","admin@barmango.ec",hash_pw("admin123"),1,1))
        conn.commit()

    if c.execute("SELECT COUNT(*) FROM drivers").fetchone()[0] == 0:
        c.executemany("INSERT INTO drivers (name,phone,email,address,city,state,zip,notes) VALUES (?,?,?,?,?,?,?,?)", [
            ("Carlos Mendoza","099-123-4567","cmendoza@barmango.ec","Av. Colón 123","Quito","Pichincha","170101",""),
            ("María Rodríguez","098-234-5678","mrodriguez@barmango.ec","Calle Sucre 456","Guayaquil","Guayas","090101",""),
            ("Luis Toapanta","097-345-6789","ltoapanta@barmango.ec","Av. Amazonas 789","Quito","Pichincha","170102",""),
            ("Ana Guamán","096-456-7890","aguaman@barmango.ec","Calle Bolívar 321","Cuenca","Azuay","010101",""),
            ("Roberto Sánchez","095-567-8901","rsanchez@barmango.ec","Av. 9 de Octubre 654","Guayaquil","Guayas","090102",""),
            ("Gabriela Vega","094-678-9012","gvega@barmango.ec","Calle Tarqui 987","Riobamba","Chimborazo","060101",""),
        ])
        c.executemany("INSERT INTO customers (name,phone,email,address,city,state,zip) VALUES (?,?,?,?,?,?,?)", [
            ("Andrés Morales","099-111-2233","amorales@gmail.com","Av. Patria 100","Quito","Pichincha","170101"),
            ("Lucía Herrera","098-222-3344","lherrera@gmail.com","Calle Olmedo 200","Guayaquil","Guayas","090101"),
            ("Diego Alvarado","097-333-4455","dalvarado@gmail.com","Av. Huayna Cápac 300","Cuenca","Azuay","010101"),
            ("Sofía Castillo","096-444-5566","scastillo@gmail.com","Calle Sucre 400","Ambato","Tungurahua","180101"),
            ("Mateo Vargas","095-555-6677","mvargas@gmail.com","Av. Remigio Crespo 500","Cuenca","Azuay","010102"),
            ("Valentina Ríos","094-666-7788","vrios@gmail.com","Calle García Moreno 600","Loja","Loja","110101"),
            ("Fernando Pazos","093-777-8899","fpazos@gmail.com","Av. Quito 700","Manta","Manabí","130101"),
            ("Isabella Núñez","092-888-9900","inunez@gmail.com","Calle Tarqui 800","Riobamba","Chimborazo","060101"),
            ("Camila Torres","091-999-0011","ctorres@gmail.com","Av. Eloy Alfaro 900","Quito","Pichincha","170103"),
            ("Sebastián Luna","090-888-1122","sluna@gmail.com","Calle Manabí 200","Guayaquil","Guayas","090103"),
            ("Natalia Flores","089-777-2233","nflores@gmail.com","Av. 24 de Mayo 300","Santo Domingo","Santo Domingo","230101"),
            ("Pablo Ortega","088-666-3344","portega@gmail.com","Calle España 400","Ambato","Tungurahua","180102"),
        ])
        c.executemany("""INSERT INTO jobs (customer_id,driver_id,status,pu_address,pu_date,pu_time,
                         del_address,del_date,del_time,signature,del_picture,costo_servicio,ubicacion,notes)
                         VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", [
            (1,1,"Pendiente","Av. Colón 1234, Quito","2025-05-01","09:00","Calle García Moreno 567, Guayaquil","2025-05-01","14:00","","",15.50,"","Manejar con cuidado"),
            (2,2,"Programado","Av. Amazonas 890, Quito","2025-05-02","10:00","Av. 9 de Octubre 234, Guayaquil","2025-05-02","15:00","","",22.00,"","Llamar antes de entregar"),
            (3,3,"Recogido","Calle Sucre 456, Cuenca","2025-05-03","08:30","Av. Huayna Capac 789, Cuenca","2025-05-03","13:00","","",18.75,"","Artículo frágil"),
            (4,1,"Entregado","Av. Patria 321, Quito","2025-05-04","09:00","Calle Olmedo 654, Guayaquil","2025-05-04","14:30","","",12.00,"","Dejado en puerta principal"),
            (5,4,"Cerrado","Av. 6 de Diciembre 111, Quito","2025-05-05","11:00","Av. Carlos Julio Arosemena 333","2025-05-05","16:00","","",20.00,"","Completado"),
            (6,2,"Pendiente","Av. República 777, Quito","2025-05-06","09:30","Calle Clemente Ballén 88, GYE","2025-05-06","14:00","","",9.50,"",""),
            (7,3,"Programado","Calle Bolívar 200, Ambato","2025-05-07","10:00","Av. Cevallos 400, Ambato","2025-05-07","15:30","","",14.00,"",""),
            (8,5,"Recogido","Av. Universitaria 55, Quito","2025-05-08","08:00","Calle Rocafuerte 300, Guayaquil","2025-05-08","13:00","","",16.50,"",""),
            (1,1,"Pendiente","Av. Naciones Unidas 800, Quito","2025-05-10","09:00","Calle Loja 500, Machala","2025-05-10","14:00","","",25.00,"",""),
            (2,2,"Programado","Av. De los Shyris 1200, Quito","2025-05-11","10:30","Av. Quito 900, Manta","2025-05-11","16:00","","",30.00,"",""),
            (3,6,"Pendiente","Calle Tarqui 78, Riobamba","2025-05-12","09:00","Av. Daniel León Borja 120, RIO","2025-05-12","14:00","","",11.00,"",""),
            (4,4,"Entregado","Av. Remigio Crespo 450, Quito","2025-05-13","10:00","Calle Gran Colombia 560, Cuenca","2025-05-13","15:00","","",19.00,"","Entregado a tiempo"),
        ])
        c.executemany("INSERT OR IGNORE INTO settings (key,value) VALUES (?,?)", [
            ("company_name","BarManGo"),
            ("address_1","Av. Amazonas N24-196, Quito, Ecuador"),
            ("address_2","Av. 9 de Octubre 100, Guayaquil, Ecuador"),
        ])
        conn.commit()
    conn.close()

# ── Auth helpers ─────────────────────────────────────────────────────────────
def get_current_user():
    uid = session.get('user_id')
    if not uid: return None
    conn = get_db()
    u = conn.execute("""SELECT u.*,g.nombre as grupo_nombre,r.permisos,r.nombre as rol_nombre
        FROM usuarios u LEFT JOIN grupos g ON u.grupo_id=g.id
        LEFT JOIN roles r ON g.rol_id=r.id WHERE u.id=? AND u.activo=1""",(uid,)).fetchone()
    conn.close()
    return row_to_dict(u)

def require_auth(f):
    @wraps(f)
    def dec(*a,**kw):
        if not session.get('user_id'): return jsonify({'error':'No autorizado'}),401
        return f(*a,**kw)
    return dec

def require_admin(f):
    @wraps(f)
    def dec(*a,**kw):
        u = get_current_user()
        if not u: return jsonify({'error':'No autorizado'}),401
        import json
        p = json.loads(u.get('permisos') or '{}')
        if not p.get('admin'): return jsonify({'error':'Se requieren permisos de administrador'}),403
        return f(*a,**kw)
    return dec

def make_user_resp(u):
    import json
    return {'id':u['id'],'nombre':u['nombre'],'username':u['username'],
            'grupo':u['grupo_nombre'],'rol':u['rol_nombre'],
            'permisos':json.loads(u.get('permisos') or '{}')}

# ── AUTH ─────────────────────────────────────────────────────────────────────
@app.route('/api/auth/login', methods=['POST'])
def login():
    d = request.json
    conn = get_db()
    u = conn.execute("""SELECT u.*,g.nombre as grupo_nombre,r.permisos,r.nombre as rol_nombre
        FROM usuarios u LEFT JOIN grupos g ON u.grupo_id=g.id
        LEFT JOIN roles r ON g.rol_id=r.id
        WHERE u.username=? AND u.activo=1""",(d.get('username',''),)).fetchone()
    if not u or u['password'] != hash_pw(d.get('password','')):
        conn.close(); return jsonify({'error':'Usuario o contraseña incorrectos'}),401
    conn.execute("UPDATE usuarios SET last_login=datetime('now') WHERE id=?",(u['id'],))
    conn.commit(); conn.close()
    session['user_id'] = u['id']; session.permanent = True
    return jsonify(make_user_resp(row_to_dict(u)))

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear(); return jsonify({'message':'Sesión cerrada'})

@app.route('/api/auth/me', methods=['GET'])
def me():
    u = get_current_user()
    if not u: return jsonify({'error':'No autorizado'}),401
    return jsonify(make_user_resp(u))

# ── ROLES ─────────────────────────────────────────────────────────────────────
@app.route('/api/roles', methods=['GET'])
@require_auth
def get_roles():
    conn = get_db()
    rows = rows_to_list(conn.execute("SELECT * FROM roles ORDER BY nombre").fetchall())
    conn.close(); return jsonify(rows)

@app.route('/api/roles', methods=['POST'])
@require_admin
def create_role():
    d = request.json; import json
    conn = get_db()
    cur = conn.execute("INSERT INTO roles (nombre,descripcion,permisos) VALUES (?,?,?)",
        (d['nombre'],d.get('descripcion',''),json.dumps(d.get('permisos',{}))))
    conn.commit(); conn.close(); return jsonify({'id':cur.lastrowid}),201

@app.route('/api/roles/<int:rid>', methods=['PUT'])
@require_admin
def update_role(rid):
    d = request.json; import json
    conn = get_db()
    conn.execute("UPDATE roles SET nombre=?,descripcion=?,permisos=? WHERE id=?",
        (d['nombre'],d.get('descripcion',''),json.dumps(d.get('permisos',{})),rid))
    conn.commit(); conn.close(); return jsonify({'message':'Actualizado'})

@app.route('/api/roles/<int:rid>', methods=['DELETE'])
@require_admin
def delete_role(rid):
    conn = get_db(); conn.execute("DELETE FROM roles WHERE id=?",(rid,))
    conn.commit(); conn.close(); return jsonify({'message':'Eliminado'})

# ── GRUPOS ────────────────────────────────────────────────────────────────────
@app.route('/api/grupos', methods=['GET'])
@require_auth
def get_grupos():
    conn = get_db()
    rows = rows_to_list(conn.execute("""SELECT g.*,r.nombre as rol_nombre,COUNT(u.id) as usuario_count
        FROM grupos g LEFT JOIN roles r ON g.rol_id=r.id
        LEFT JOIN usuarios u ON u.grupo_id=g.id GROUP BY g.id ORDER BY g.nombre""").fetchall())
    conn.close(); return jsonify(rows)

@app.route('/api/grupos', methods=['POST'])
@require_admin
def create_grupo():
    d = request.json; conn = get_db()
    cur = conn.execute("INSERT INTO grupos (nombre,descripcion,rol_id) VALUES (?,?,?)",
        (d['nombre'],d.get('descripcion',''),d.get('rol_id')))
    conn.commit(); conn.close(); return jsonify({'id':cur.lastrowid}),201

@app.route('/api/grupos/<int:gid>', methods=['PUT'])
@require_admin
def update_grupo(gid):
    d = request.json; conn = get_db()
    conn.execute("UPDATE grupos SET nombre=?,descripcion=?,rol_id=? WHERE id=?",
        (d['nombre'],d.get('descripcion',''),d.get('rol_id'),gid))
    conn.commit(); conn.close(); return jsonify({'message':'Actualizado'})

@app.route('/api/grupos/<int:gid>', methods=['DELETE'])
@require_admin
def delete_grupo(gid):
    conn = get_db(); conn.execute("DELETE FROM grupos WHERE id=?",(gid,))
    conn.commit(); conn.close(); return jsonify({'message':'Eliminado'})

# ── USUARIOS ──────────────────────────────────────────────────────────────────
@app.route('/api/usuarios', methods=['GET'])
@require_admin
def get_usuarios():
    conn = get_db()
    rows = rows_to_list(conn.execute("""SELECT u.id,u.nombre,u.username,u.email,u.activo,
        u.created_at,u.last_login,g.nombre as grupo_nombre,r.nombre as rol_nombre
        FROM usuarios u LEFT JOIN grupos g ON u.grupo_id=g.id
        LEFT JOIN roles r ON g.rol_id=r.id ORDER BY u.nombre""").fetchall())
    conn.close(); return jsonify(rows)

@app.route('/api/usuarios', methods=['POST'])
@require_admin
def create_usuario():
    d = request.json
    if not d.get('password'): return jsonify({'error':'Contraseña requerida'}),400
    conn = get_db()
    try:
        cur = conn.execute("INSERT INTO usuarios (nombre,username,email,password,grupo_id,activo) VALUES (?,?,?,?,?,?)",
            (d['nombre'],d['username'],d.get('email',''),hash_pw(d['password']),d.get('grupo_id'),1))
        conn.commit(); conn.close(); return jsonify({'id':cur.lastrowid}),201
    except:
        conn.close(); return jsonify({'error':'El usuario ya existe'}),400

@app.route('/api/usuarios/<int:uid>', methods=['PUT'])
@require_admin
def update_usuario(uid):
    d = request.json; conn = get_db()
    if d.get('password'):
        conn.execute("UPDATE usuarios SET nombre=?,username=?,email=?,password=?,grupo_id=?,activo=? WHERE id=?",
            (d['nombre'],d['username'],d.get('email',''),hash_pw(d['password']),d.get('grupo_id'),d.get('activo',1),uid))
    else:
        conn.execute("UPDATE usuarios SET nombre=?,username=?,email=?,grupo_id=?,activo=? WHERE id=?",
            (d['nombre'],d['username'],d.get('email',''),d.get('grupo_id'),d.get('activo',1),uid))
    conn.commit(); conn.close(); return jsonify({'message':'Actualizado'})

@app.route('/api/usuarios/<int:uid>', methods=['DELETE'])
@require_admin
def delete_usuario(uid):
    if uid == session.get('user_id'): return jsonify({'error':'No puedes eliminar tu propio usuario'}),400
    conn = get_db(); conn.execute("DELETE FROM usuarios WHERE id=?",(uid,))
    conn.commit(); conn.close(); return jsonify({'message':'Eliminado'})

# ── JOBS ──────────────────────────────────────────────────────────────────────
@app.route('/api/jobs', methods=['GET'])
@require_auth
def get_jobs():
    conn = get_db()
    q = "SELECT j.*,c.name as customer_name,c.phone as customer_phone,d.name as driver_name FROM jobs j LEFT JOIN customers c ON j.customer_id=c.id LEFT JOIN drivers d ON j.driver_id=d.id WHERE 1=1"
    p = []
    if request.args.get('status'): q+=" AND j.status=?"; p.append(request.args['status'])
    if request.args.get('search'):
        s=request.args['search']; q+=" AND (c.name LIKE ? OR d.name LIKE ? OR CAST(j.id AS TEXT) LIKE ?)"; p+=[f'%{s}%']*3
    if request.args.get('pu_date'): q+=" AND j.pu_date=?"; p.append(request.args['pu_date'])
    q+=" ORDER BY j.id DESC"
    jobs=rows_to_list(conn.execute(q,p).fetchall()); conn.close(); return jsonify(jobs)

@app.route('/api/jobs/<int:jid>', methods=['GET'])
@require_auth
def get_job(jid):
    conn = get_db()
    r = conn.execute("""SELECT j.*,c.name as customer_name,c.phone as customer_phone,c.email as customer_email,
        c.address as customer_address,c.city as customer_city,c.state as customer_state,d.name as driver_name
        FROM jobs j LEFT JOIN customers c ON j.customer_id=c.id LEFT JOIN drivers d ON j.driver_id=d.id WHERE j.id=?""",(jid,)).fetchone()
    conn.close()
    return jsonify(row_to_dict(r)) if r else (jsonify({'error':'Not found'}),404)

@app.route('/api/jobs', methods=['POST'])
@require_auth
def create_job():
    d=request.json; conn=get_db()
    cur=conn.execute("INSERT INTO jobs (customer_id,driver_id,status,pu_address,pu_date,pu_time,del_address,del_date,del_time,signature,del_picture,notes,costo_servicio,ubicacion) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (d.get('customer_id'),d.get('driver_id'),d.get('status','Pendiente'),d.get('pu_address',''),d.get('pu_date',''),d.get('pu_time',''),d.get('del_address',''),d.get('del_date',''),d.get('del_time',''),d.get('signature',''),d.get('del_picture',''),d.get('notes',''),d.get('costo_servicio',0),d.get('ubicacion','')))
    conn.commit(); conn.close(); return jsonify({'id':cur.lastrowid}),201

@app.route('/api/jobs/<int:jid>', methods=['PUT'])
@require_auth
def update_job(jid):
    d=request.json; conn=get_db()
    conn.execute("UPDATE jobs SET customer_id=?,driver_id=?,status=?,pu_address=?,pu_date=?,pu_time=?,del_address=?,del_date=?,del_time=?,signature=?,del_picture=?,notes=?,costo_servicio=?,ubicacion=?,updated_at=datetime('now') WHERE id=?",
        (d.get('customer_id'),d.get('driver_id'),d.get('status'),d.get('pu_address'),d.get('pu_date'),d.get('pu_time'),d.get('del_address'),d.get('del_date'),d.get('del_time'),d.get('signature'),d.get('del_picture'),d.get('notes'),d.get('costo_servicio',0),d.get('ubicacion',''),jid))
    conn.commit(); conn.close(); return jsonify({'message':'Updated'})

@app.route('/api/jobs/<int:jid>', methods=['DELETE'])
@require_auth
def delete_job(jid):
    conn=get_db(); conn.execute("DELETE FROM jobs WHERE id=?",(jid,)); conn.commit(); conn.close(); return jsonify({'message':'Deleted'})

# ── DRIVERS ───────────────────────────────────────────────────────────────────
@app.route('/api/drivers', methods=['GET'])
@require_auth
def get_drivers():
    conn=get_db(); s=request.args.get('search','')
    q="SELECT d.*,COUNT(j.id) as job_count FROM drivers d LEFT JOIN jobs j ON j.driver_id=d.id"
    p=[]
    if s: q+=" WHERE d.name LIKE ? OR d.city LIKE ?"; p=[f'%{s}%']*2
    rows=rows_to_list(conn.execute(q+' GROUP BY d.id ORDER BY d.name',p).fetchall()); conn.close(); return jsonify(rows)

@app.route('/api/drivers/<int:did>', methods=['GET'])
@require_auth
def get_driver(did):
    conn=get_db(); r=conn.execute("SELECT * FROM drivers WHERE id=?",(did,)).fetchone(); conn.close()
    return jsonify(row_to_dict(r)) if r else (jsonify({'error':'Not found'}),404)

@app.route('/api/drivers', methods=['POST'])
@require_auth
def create_driver():
    d=request.json; conn=get_db()
    cur=conn.execute("INSERT INTO drivers (name,phone,email,address,city,state,zip,notes) VALUES (?,?,?,?,?,?,?,?)",
        (d['name'],d.get('phone',''),d.get('email',''),d.get('address',''),d.get('city',''),d.get('state',''),d.get('zip',''),d.get('notes','')))
    conn.commit(); conn.close(); return jsonify({'id':cur.lastrowid}),201

@app.route('/api/drivers/<int:did>', methods=['PUT'])
@require_auth
def update_driver(did):
    d=request.json; conn=get_db()
    conn.execute("UPDATE drivers SET name=?,phone=?,email=?,address=?,city=?,state=?,zip=?,notes=? WHERE id=?",
        (d['name'],d.get('phone',''),d.get('email',''),d.get('address',''),d.get('city',''),d.get('state',''),d.get('zip',''),d.get('notes',''),did))
    conn.commit(); conn.close(); return jsonify({'message':'Updated'})

@app.route('/api/drivers/<int:did>', methods=['DELETE'])
@require_auth
def delete_driver(did):
    conn=get_db(); conn.execute("DELETE FROM drivers WHERE id=?",(did,)); conn.commit(); conn.close(); return jsonify({'message':'Deleted'})

# ── CUSTOMERS ─────────────────────────────────────────────────────────────────
@app.route('/api/customers', methods=['GET'])
@require_auth
def get_customers():
    conn=get_db(); s=request.args.get('search','')
    q="SELECT c.*,COUNT(j.id) as job_count FROM customers c LEFT JOIN jobs j ON j.customer_id=c.id"
    p=[]
    if s: q+=" WHERE c.name LIKE ? OR c.email LIKE ?"; p=[f'%{s}%']*2
    rows=rows_to_list(conn.execute(q+' GROUP BY c.id ORDER BY c.name',p).fetchall()); conn.close(); return jsonify(rows)

@app.route('/api/customers/<int:cid>', methods=['GET'])
@require_auth
def get_customer(cid):
    conn=get_db(); r=conn.execute("SELECT * FROM customers WHERE id=?",(cid,)).fetchone(); conn.close()
    return jsonify(row_to_dict(r)) if r else (jsonify({'error':'Not found'}),404)

@app.route('/api/customers', methods=['POST'])
@require_auth
def create_customer():
    d=request.json; conn=get_db()
    cur=conn.execute("INSERT INTO customers (name,phone,email,address,city,state,zip) VALUES (?,?,?,?,?,?,?)",
        (d['name'],d.get('phone',''),d.get('email',''),d.get('address',''),d.get('city',''),d.get('state',''),d.get('zip','')))
    conn.commit(); conn.close(); return jsonify({'id':cur.lastrowid}),201

@app.route('/api/customers/<int:cid>', methods=['PUT'])
@require_auth
def update_customer(cid):
    d=request.json; conn=get_db()
    conn.execute("UPDATE customers SET name=?,phone=?,email=?,address=?,city=?,state=?,zip=? WHERE id=?",
        (d['name'],d.get('phone',''),d.get('email',''),d.get('address',''),d.get('city',''),d.get('state',''),d.get('zip',''),cid))
    conn.commit(); conn.close(); return jsonify({'message':'Updated'})

@app.route('/api/customers/<int:cid>', methods=['DELETE'])
@require_auth
def delete_customer(cid):
    conn=get_db(); conn.execute("DELETE FROM customers WHERE id=?",(cid,)); conn.commit(); conn.close(); return jsonify({'message':'Deleted'})

# ── STATS ─────────────────────────────────────────────────────────────────────
@app.route('/api/stats', methods=['GET'])
@require_auth
def get_stats():
    conn=get_db()
    sc={s:conn.execute("SELECT COUNT(*) FROM jobs WHERE status=?",(s,)).fetchone()[0] for s in ['Pendiente','Programado','Recogido','Entregado','Cerrado']}
    rows=rows_to_list(conn.execute("""SELECT j.id,j.status,j.pu_date,j.del_date,j.del_address,j.costo_servicio,
        c.name as customer_name,d.name as driver_name FROM jobs j
        LEFT JOIN customers c ON j.customer_id=c.id LEFT JOIN drivers d ON j.driver_id=d.id
        ORDER BY j.id DESC LIMIT 8""").fetchall())
    td=rows_to_list(conn.execute("SELECT d.name,COUNT(j.id) as job_count FROM drivers d LEFT JOIN jobs j ON j.driver_id=d.id GROUP BY d.id ORDER BY job_count DESC LIMIT 6").fetchall())
    ti=conn.execute("SELECT COALESCE(SUM(costo_servicio),0) FROM jobs").fetchone()[0]
    tj=conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    tdr=conn.execute("SELECT COUNT(*) FROM drivers").fetchone()[0]
    tc=conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    conn.close()
    return jsonify({'total_jobs':tj,'total_drivers':tdr,'total_customers':tc,'total_ingresos':round(ti,2),'status_counts':sc,'top_drivers':td,'recent_jobs':rows})

# ── SCHEDULE ──────────────────────────────────────────────────────────────────
@app.route('/api/schedule', methods=['GET'])
@require_auth
def get_schedule():
    yr=request.args.get('year',datetime.now().year); mo=request.args.get('month',datetime.now().month)
    conn=get_db()
    rows=rows_to_list(conn.execute("""SELECT j.id,j.status,j.pu_date,j.pu_time,j.del_date,c.name as customer_name,d.name as driver_name
        FROM jobs j LEFT JOIN customers c ON j.customer_id=c.id LEFT JOIN drivers d ON j.driver_id=d.id
        WHERE strftime('%Y',j.pu_date)=? AND strftime('%m',j.pu_date)=? ORDER BY j.pu_date,j.pu_time""",(str(yr),str(mo).zfill(2))).fetchall())
    conn.close(); return jsonify(rows)

# ── SETTINGS ──────────────────────────────────────────────────────────────────
@app.route('/api/settings', methods=['GET'])
@require_auth
def get_settings():
    conn=get_db(); rows=conn.execute("SELECT key,value FROM settings").fetchall(); conn.close()
    return jsonify({r['key']:r['value'] for r in rows})

@app.route('/api/settings', methods=['PUT'])
@require_admin
def update_settings():
    conn=get_db()
    for k,v in request.json.items(): conn.execute("INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)",(k,v))
    conn.commit(); conn.close(); return jsonify({'message':'Saved'})

# ── Serve frontend ─────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory(os.path.join(BASE_DIR,'client'),'index.html')

if __name__=='__main__':
    init_db()
    print("\n🚚  BarManGo con Seguridad — http://localhost:5000\n")
    port=int(os.environ.get('PORT',5000))
    app.run(debug=False,port=port,host='0.0.0.0')
