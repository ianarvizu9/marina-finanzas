from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from datetime import date
from .database import engine, SessionLocal
from .models import Base
from . import schemas, crud, models
from fastapi import UploadFile, File
import shutil
import os
from datetime import datetime
import pdfplumber
from .parcers.detector import detect_parser
from app import models

app = FastAPI()
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

Base.metadata.create_all(bind=engine)

# Dependencia de DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def root():
    return {"mensaje": "Sistema Marina activo"}

@app.post("/movimientos/")
def crear_movimiento(movimiento: schemas.MovimientoCreate, db: Session = Depends(get_db)):
    return crud.crear_movimiento(db, movimiento)

from typing import List

@app.get("/movimientos/", response_model=List[schemas.MovimientoResponse])
def listar_movimientos(
    fecha_inicio: date | None = None,
    fecha_fin: date | None = None,
    banco: str | None = None,
    tipo: schemas.TipoMovimiento | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(models.Movimiento)

    if fecha_inicio:
        query = query.filter(models.Movimiento.fecha >= fecha_inicio)
    if fecha_fin:
        query = query.filter(models.Movimiento.fecha <= fecha_fin)
    if banco:
        query = query.filter(models.Movimiento.banco == banco)
    if tipo:
        query = query.filter(models.Movimiento.tipo == tipo)

    return query.order_by(models.Movimiento.fecha.desc()).offset(skip).limit(limit).all()

@app.get("/resumen", response_model=schemas.ResumenResponse)
def resumen(
    fecha_inicio: date | None = None,
    fecha_fin: date | None = None,
    db: Session = Depends(get_db)
):
    return crud.obtener_resumen(db, fecha_inicio, fecha_fin)

# Endpoint para subir PDF de estados de cuenta
# Crear carpeta si no existe
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.post("/upload-pdf")
def upload_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):

    if file.content_type != "application/pdf":
        return {"error": "Solo se permiten archivos PDF"}

    # Leer PDF en memoria
    text = ""

    with pdfplumber.open(file.file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""

    # Detectar parser
    try:
        parser = detect_parser(text)
    except ValueError as e:
        return {"error": str(e)}

    # Extraer movimientos
    movimientos = parser.parse(text)

    # Extraer todos los numeros de transaccion
    numeros = [mov["numero_transaccion"] for mov in movimientos]

    # Buscar si alguno ya existe
    existentes = db.query(models.Movimiento.numero_transaccion).filter(
        models.Movimiento.numero_transaccion.in_(numeros)
    ).all()

    if existentes:
        return {
            "error": "El archivo contiene movimientos ya registrados",
            "transacciones_duplicadas": [e[0] for e in existentes]
        }

    movimientos_guardados = []

    for mov in movimientos:
        nuevo = models.Movimiento(
            numero_transaccion=mov["numero_transaccion"],
            fecha=mov["fecha"],
            concepto=mov["concepto"],
            tipo=mov["tipo"],
            monto=mov["monto"],
            saldo=mov["saldo"],
            banco=mov["banco"],
            creado_por="sistema",
            modificado_por="sistema"
        )

        # Verificar si ya existe
        existe = db.query(models.Movimiento).filter(
            models.Movimiento.numero_transaccion == mov["numero_transaccion"]
        ).first()

        if existe:
            continue  # Saltar duplicado

        db.add(nuevo)
        movimientos_guardados.append(nuevo)

    db.commit()

    return {
        "mensaje": "Movimientos insertados correctamente",
        "cantidad": len(movimientos_guardados)
    }


@app.post("/procesar-archivo/{archivo_id}")
def procesar_archivo(archivo_id: int, db: Session = Depends(get_db)):

    archivo = db.query(models.ArchivoEstadoCuenta).filter(
        models.ArchivoEstadoCuenta.id == archivo_id
    ).first()

    if not archivo:
        return {"error": "Archivo no encontrado"}

    try:
        import pdfplumber

        texto = ""
        with pdfplumber.open(archivo.ruta) as pdf:
            for page in pdf.pages:
                texto += page.extract_text() or ""

        parser = detect_parser(texto)
        movimientos_extraidos = parser.parse(texto)

        for mov in movimientos_extraidos:
            nuevo = models.Movimiento(**mov)
            db.add(nuevo)

        archivo.procesado = "procesado"
        db.commit()

        return {
            "mensaje": "Movimientos insertados",
            "total_movimientos": len(movimientos_extraidos)
        }

    except Exception as e:
        archivo.procesado = "error"
        db.commit()
        return {"error": str(e)}