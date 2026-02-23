import enum
from .database import Base
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    DateTime,
    Numeric,
    Enum,
    CheckConstraint,
    UniqueConstraint,
    Index
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()
    
class TipoMovimiento(enum.Enum):
    CARGO = "CARGO"
    ABONO = "ABONO"

class Movimiento(Base):
    __tablename__ = "movimientos"

    id = Column(Integer, primary_key=True, index=True)

    referencia = Column(String(50), nullable=False)
    fecha_operacion = Column(Date, nullable=False)
    fecha_aplicacion = Column(Date, nullable=False)
    concepto = Column(String(255), nullable=False)

    tipo_movimiento = Column(
        Enum(TipoMovimiento, name="tipo_movimiento_enum"),
        nullable=False
    )

    cargo = Column(Numeric(15, 2), nullable=False, default=0)
    abono = Column(Numeric(15, 2), nullable=False, default=0)
    saldo = Column(Numeric(15, 2), nullable=True)

    subcuenta = Column(String(50), nullable=False)
    banco = Column(String(50), nullable=True)

    creado_por = Column(String(50), nullable=True)
    fecha_de_creacion = Column(DateTime, default=datetime.utcnow)

    modificado_por = Column(String(50), nullable=True)
    fecha_de_modificacion = Column(DateTime, onupdate=datetime.utcnow)

    # 🔥 Constraints importantes
    __table_args__ = (

        # Índice para búsquedas rápidas
        Index("idx_referencia", "referencia"),

        # Evitar duplicados
        UniqueConstraint(
            "referencia",
            "fecha_operacion",
            "cargo",
            "abono",
            name="uq_movimiento_unico"
        ),

        # cargo >= 0
        CheckConstraint("cargo >= 0", name="check_cargo_positive"),

        # abono >= 0
        CheckConstraint("abono >= 0", name="check_abono_positive"),

        # Solo uno puede ser mayor a 0
        CheckConstraint(
            "(cargo = 0 AND abono > 0) OR (abono = 0 AND cargo > 0)",
            name="check_solo_un_tipo_movimiento"
        ),
    )


class ArchivoEstadoCuenta(Base):
    __tablename__ = "archivos_estado_cuenta"

    id = Column(Integer, primary_key=True, index=True)
    nombre_archivo = Column(String, nullable=False)
    banco = Column(String, nullable=True)
    fecha_carga = Column(DateTime, default=datetime.utcnow)
    ruta = Column(String, nullable=False)
    procesado = Column(String, default="pendiente")  # pendiente | procesado | error