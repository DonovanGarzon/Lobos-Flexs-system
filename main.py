from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os

app = FastAPI(title="API Lobos Flexs")

# Permite que tu HTML se comunique con esta API sin ser bloqueado
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En el futuro cambiarás el "*" por el link de tu HTML
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Estructura de los datos que recibe
class Venta(BaseModel):
    modelo: str
    costo: float
    ganancia: float
    total: float

# Conexión a la base de datos usando la variable de entorno de la nube
def get_db_connection():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise Exception("Falta la variable de entorno DATABASE_URL")
    return psycopg2.connect(db_url)

@app.post("/api/ventas")
def registrar_venta(venta: Venta):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            INSERT INTO ventas (modelo, costo, ganancia, total_cobrado)
            VALUES (%s, %s, %s, %s) RETURNING *;
        """, (venta.modelo, venta.costo, venta.ganancia, venta.total))
        
        nueva_venta = cursor.fetchone()
        conn.commit()
        
        if 'fecha_hora' in nueva_venta:
            dt = nueva_venta['fecha_hora']
            nueva_venta['fecha'] = dt.strftime('%d/%m/%Y')
            nueva_venta['hora'] = dt.strftime('%H:%M')
            
        return nueva_venta
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.get("/api/ventas")
def obtener_ventas():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT * FROM ventas ORDER BY fecha_hora DESC;")
        ventas = cursor.fetchall()
        
        for v in ventas:
            dt = v['fecha_hora']
            v['fecha'] = dt.strftime('%d/%m/%Y')
            v['hora'] = dt.strftime('%H:%M')
            
        return ventas
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()
