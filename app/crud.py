from psycopg2 import IntegrityError
from sqlalchemy.orm import Session
from . import models, schemas
from sqlalchemy import func
from decimal import Decimal
from typing import List

def crear_movimiento_individual(db, movimiento):

    cargo = Decimal("0.00")
    abono = Decimal("0.00")

    if movimiento.tipo_movimiento == models.TipoMovimiento.CARGO:
        cargo = movimiento.monto
    else:
        abono = movimiento.monto

    nuevo = models.Movimiento(
        referencia=movimiento.referencia,
        fecha_operacion=movimiento.fecha_operacion,
        fecha_aplicacion=movimiento.fecha_aplicacion,
        concepto=movimiento.concepto,
        tipo_movimiento=movimiento.tipo_movimiento,
        cargo=cargo,
        abono=abono,
        saldo=movimiento.saldo,
        subcuenta=movimiento.subcuenta,
        banco=movimiento.banco,
        creado_por=movimiento.creado_por,
    )

    try:
        db.add(nuevo)
        db.commit()
        db.refresh(nuevo)
        return nuevo, None

    except IntegrityError:
        db.rollback()
        return None, "duplicado"
    
def procesar_movimientos_masivos(db, lista_movimientos):

    insertados = []
    duplicados = []

    for movimiento in lista_movimientos:

        nuevo, error = crear_movimiento_individual(db, movimiento)

        if nuevo:
            insertados.append(nuevo.referencia)
        else:
            duplicados.append(movimiento.referencia)

    return {
        "total_procesados": len(lista_movimientos),
        "insertados": len(insertados),
        "duplicados": len(duplicados),
        "detalle_duplicados": duplicados
    }

# ---------------------------------------------------------
# Crear movimiento individual (SIN commit)
# ---------------------------------------------------------

def crear_movimiento_sin_commit(db: Session, movimiento: schemas.MovimientoCreate):

    cargo = Decimal("0.00")
    abono = Decimal("0.00")

    if movimiento.tipo_movimiento == models.TipoMovimiento.CARGO:
        cargo = movimiento.monto
    else:
        abono = movimiento.monto

    nuevo = models.Movimiento(
        referencia=movimiento.referencia,
        fecha_operacion=movimiento.fecha_operacion,
        fecha_aplicacion=movimiento.fecha_aplicacion,
        concepto=movimiento.concepto,
        tipo_movimiento=movimiento.tipo_movimiento,
        cargo=cargo,
        abono=abono,
        saldo=movimiento.saldo,
        subcuenta=movimiento.subcuenta,
        banco=movimiento.banco,
        creado_por=movimiento.creado_por,
        fecha_de_creacion=movimiento.fecha_de_creacion,
        modificado_por=movimiento.modificado_por,
        fecha_de_modificacion=movimiento.fecha_de_modificacion
    )

    db.add(nuevo)

    try:
        db.flush()  # valida constraints sin hacer commit
        return nuevo, None

    except IntegrityError:
        db.rollback()
        return None, "duplicado"


# ---------------------------------------------------------
# Procesar carga masiva (UN SOLO COMMIT)
# ---------------------------------------------------------

def procesar_movimientos_masivos(
    db: Session,
    lista_movimientos: List[schemas.MovimientoCreate]
):

    insertados = []
    duplicados = []

    for movimiento in lista_movimientos:

        nuevo, error = crear_movimiento_sin_commit(db, movimiento)

        if nuevo:
            insertados.append(nuevo.referencia)
        else:
            duplicados.append(movimiento.referencia)

    # Commit único al final
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise e

    return {
        "total_procesados": len(lista_movimientos),
        "insertados": len(insertados),
        "duplicados": len(duplicados),
        "detalle_duplicados": duplicados
    }


# ---------------------------------------------------------
# Listar movimientos con filtros
# ---------------------------------------------------------

def listar_movimientos(
    db: Session,
    fecha_inicio=None,
    fecha_fin=None,
    banco=None,
    tipo_movimiento=None
):

    query = db.query(models.Movimiento)

    if fecha_inicio:
        query = query.filter(models.Movimiento.fecha_operacion >= fecha_inicio)

    if fecha_fin:
        query = query.filter(models.Movimiento.fecha_operacion <= fecha_fin)

    if banco:
        query = query.filter(models.Movimiento.banco == banco)

    if tipo_movimiento:
        query = query.filter(models.Movimiento.tipo_movimiento == tipo_movimiento)

    return query.order_by(models.Movimiento.fecha_operacion.desc()).all()

# ---------------------------------------------------------
# Obtener movimientos con filtros
# ---------------------------------------------------------

def obtener_movimientos(
    db: Session,
    fecha_inicio=None,
    fecha_fin=None,
    banco=None,
    tipo_movimiento=None
):

    query = db.query(models.Movimiento)

    if fecha_inicio:
        query = query.filter(models.Movimiento.fecha_operacion >= fecha_inicio)

    if fecha_fin:
        query = query.filter(models.Movimiento.fecha_operacion <= fecha_fin)

    if banco:
        query = query.filter(models.Movimiento.banco == banco)

    if tipo_movimiento:
        query = query.filter(models.Movimiento.tipo_movimiento == tipo_movimiento)

    return query.order_by(models.Movimiento.fecha_operacion.desc()).all()


# ---------------------------------------------------------
# Obtener resumen financiero
# ---------------------------------------------------------

def obtener_resumen(db: Session, fecha_inicio=None, fecha_fin=None):

    query = db.query(models.Movimiento)

    if fecha_inicio:
        query = query.filter(models.Movimiento.fecha_operacion >= fecha_inicio)

    if fecha_fin:
        query = query.filter(models.Movimiento.fecha_operacion <= fecha_fin)

    total_cargos = query.with_entities(
        func.coalesce(func.sum(models.Movimiento.cargo), 0)
    ).scalar()

    total_abonos = query.with_entities(
        func.coalesce(func.sum(models.Movimiento.abono), 0)
    ).scalar()

    total_movimientos = query.count()

    balance = total_abonos - total_cargos

    return {
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "total_movimientos": total_movimientos,
        "total_cargos": float(total_cargos),
        "total_abonos": float(total_abonos),
        "balance_neto": float(balance)
    }