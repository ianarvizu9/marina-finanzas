import enum

from pydantic import BaseModel
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

class TipoMovimiento(enum.Enum):
    CARGO = "CARGO"
    ABONO = "ABONO"

class MovimientoCreate(BaseModel):
    id: int | None = None
    referencia: str
    fecha_operacion: datetime
    fecha_aplicacion: datetime
    concepto: str
    tipo_movimiento: TipoMovimiento
    cargo: Decimal
    abono: Decimal
    saldo: Decimal | None = None
    subcuenta: str 
    banco: str | None = None
    descripcion_original: str | None = None
    archivo_origen: str | None = None
    creado_por: str | None = None
    fecha_de_creacion: datetime
    modificado_por: str | None = None
    fecha_de_modificacion: datetime

class MovimientoResponse(MovimientoCreate):
    id: int

    class Config:
        from_attributes = True  # SQLAlchemy compatibility

class ResumenResponse(BaseModel):
    total_ingresos: Decimal
    total_egresos: Decimal
    balance: Decimal