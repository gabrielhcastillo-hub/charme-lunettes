import sqlite3
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import os
import json
from io import BytesIO
from PIL import Image

app = FastAPI(title="Sistema CHARME LUNETTES")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "charme_lunettes.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS marcos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            marca TEXT, modelo TEXT, color TEXT, stock INTEGER, precio REAL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cristales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            material TEXT, tratamiento TEXT, esf REAL, cil REAL, stock INTEGER
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            cliente TEXT, telefono TEXT, marco_id INTEGER, 
            precio_total REAL, monto_sena REAL, saldo REAL, estado TEXT
        )
    ''')
    
    cursor.execute("SELECT COUNT(*) FROM marcos")
    if cursor.fetchone() == 0:
        cursor.executemany("INSERT INTO marcos (marca, modelo, color, stock, precio) VALUES (?,?,?,?,?)", [
            ("Ray-Ban", "Aviator", "Negro", 6, 45000),
            ("Vulk", "Detroit", "Carey", 4, 38000),
            ("Infinit", "Way", "Transparente", 5, 29000)
        ])
        cursor.executemany("INSERT INTO cristales (material, tratamiento, esf, cil, stock) VALUES (?,?,?,?,?)", [
            ("Orgánico", "Antirreflex", 0.00, 0.00, 30),
            ("Policarbonato", "Filtro Azul", -1.50, -0.25, 12),
            ("Orgánico", "Fotocromático", +2.00, 0.00, 8)
        ])
        conn.commit()
    conn.close()

init_db()

class ItemVenta(BaseModel):
    cliente: str
    telefono: str | None = None
    marco_id: int | None = None
    precio_total: float
    monto_sena: float
    estado: str

@app.get("/api/productos")
def obtener_productos():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, marca, modelo, color, stock FROM marcos")
    marcos = [{"id": r, "marca": r, "modelo": r, "color": r, "stock": r} for r in cursor.fetchall()]
    conn.close()
    return {"marcos": marcos, "cristales": []}

@app.post("/api/vender")
def registrar_venta(venta: ItemVenta):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    saldo_calculado = venta.precio_total - venta.monto_sena
    try:
        cursor.execute('''
            INSERT INTO ventas (cliente, telefono, marco_id, precio_total, monto_sena, saldo, estado)
            VALUES (?,?,?,?,?,?,?)
        ''', (venta.cliente, venta.telefono, venta.marco_id, venta.precio_total, venta.monto_sena, saldo_calculado, venta.estado))
        conn.commit()
        return {"status": "success"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

@app.get("/", response_class=HTMLResponse)
def index():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Error: No se encontró el archivo index.html en el servidor.</h1>"
