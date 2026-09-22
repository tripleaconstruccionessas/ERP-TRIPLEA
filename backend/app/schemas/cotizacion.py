from uuid import UUID
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import date, datetime
from pydantic import BaseModel, EmailStr, field_validator


class CotizacionItemCreate(BaseModel):
    producto_id: Optional[UUID] = None
    descripcion: Optional[str] = None
    unidad: Optional[str] = None
    cantidad: Decimal
    precio_unitario: Decimal
    descuento_porcentaje: Optional[Decimal] = Decimal("0")
    impuesto_porcentaje: Optional[Decimal] = Decimal("19")
    orden: int = 0


class CotizacionItemOut(BaseModel):
    id: UUID
    producto_id: Optional[UUID] = None
    descripcion: Optional[str] = None
    unidad: Optional[str] = None
    cantidad: Decimal
    precio_unitario: Decimal
    descuento_porcentaje: Optional[Decimal] = None
    descuento_monto: Optional[Decimal] = None
    impuesto_porcentaje: Optional[Decimal] = None
    impuesto_monto: Optional[Decimal] = None
    subtotal: Decimal
    total: Decimal
    orden: int
    producto_nombre: Optional[str] = None
    producto_codigo: Optional[str] = None

    model_config = {"from_attributes": True}


class CotizacionCreate(BaseModel):
    cliente_id: UUID
    titulo: str
    descripcion: Optional[str] = None
    fecha_emision: date
    fecha_vencimiento: Optional[date] = None
    moneda: str = "COP"
    validez_dias: Optional[int] = 30
    condiciones_pago: Optional[str] = None
    terminos: Optional[str] = None
    observaciones: Optional[str] = None
    con_aiu: bool = False
    aiu_administracion: Optional[Decimal] = Decimal("0")
    aiu_imprevistos: Optional[Decimal] = Decimal("0")
    aiu_utilidad: Optional[Decimal] = Decimal("0")
    numero_sufijo: Optional[int] = None
    items: List[CotizacionItemCreate]

    @field_validator("items")
    @classmethod
    def items_not_empty(cls, v: list) -> list:
        if not v:
            raise ValueError("La cotización debe tener al menos un ítem")
        return v


class CotizacionUpdate(BaseModel):
    cliente_id: Optional[UUID] = None
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    fecha_emision: Optional[date] = None
    fecha_vencimiento: Optional[date] = None
    estado: Optional[str] = None
    moneda: Optional[str] = None
    validez_dias: Optional[int] = None
    condiciones_pago: Optional[str] = None
    terminos: Optional[str] = None
    observaciones: Optional[str] = None
    con_aiu: Optional[bool] = None
    aiu_administracion: Optional[Decimal] = None
    aiu_imprevistos: Optional[Decimal] = None
    aiu_utilidad: Optional[Decimal] = None
    items: Optional[List[CotizacionItemCreate]] = None


class CotizacionList(BaseModel):
    id: UUID
    numero: str
    titulo: str
    estado: str
    moneda: str
    subtotal: Decimal
    total: Decimal
    fecha_emision: date
    fecha_vencimiento: Optional[date] = None
    cliente_nombre: Optional[str] = None
    usuario_nombre: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CotizacionOut(CotizacionList):
    descripcion: Optional[str] = None
    impuesto: Decimal
    descuento: Decimal
    con_aiu: bool = False
    aiu_administracion: Decimal = Decimal("0")
    aiu_imprevistos: Decimal = Decimal("0")
    aiu_utilidad: Decimal = Decimal("0")
    aiu_monto: Decimal = Decimal("0")
    aiu_iva_monto: Decimal = Decimal("0")
    condiciones_pago: Optional[str] = None
    terminos: Optional[str] = None
    observaciones: Optional[str] = None
    cliente_email: Optional[str] = None
    cliente_nit: Optional[str] = None
    cliente_ciudad: Optional[str] = None
    cliente_contacto_nombre: Optional[str] = None
    cliente_contacto_telefono: Optional[str] = None
    validez_dias: Optional[int] = None
    token_publico: Optional[str] = None
    items: List[CotizacionItemOut] = []

    model_config = {"from_attributes": True}


class EstadoUpdate(BaseModel):
    estado: str


class EnviarEmailRequest(BaseModel):
    email: EmailStr
    asunto: Optional[str] = None
    mensaje: Optional[str] = None


class StatsOut(BaseModel):
    total: int
    aprobadas: int
    pendientes: int
    rechazadas: int
    ingresos_totales: Decimal
    ingresos_aprobados: Decimal
    por_estado: List[Dict[str, Any]]
    por_mes: List[Dict[str, Any]]
