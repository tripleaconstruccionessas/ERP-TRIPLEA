from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.api.deps import get_db_session, get_authenticated_user, require_admin
from app.models.auth import Usuario
from app.repositories.cotizacion import CotizacionRepository
from app.services.cotizacion_service import CotizacionService, peek_next_numero
from app.schemas.cotizacion import CotizacionCreate, CotizacionUpdate, CotizacionOut, CotizacionList, StatsOut, EstadoUpdate, EnviarEmailRequest
from app.schemas.common import MessageResponse
from app.utils.email import send_cotizacion_email
from app.schemas.common import PaginatedResponse
import math

router = APIRouter(prefix="/cotizaciones", tags=["Cotizaciones"])


@router.get("/stats", response_model=StatsOut)
def get_stats(db: Session = Depends(get_db_session), _: Usuario = Depends(get_authenticated_user)):
    return CotizacionRepository(db).get_stats()


@router.get("/next-numero")
def get_next_numero(db: Session = Depends(get_db_session), _: Usuario = Depends(get_authenticated_user)):
    return peek_next_numero(db)


@router.get("/", response_model=PaginatedResponse[CotizacionList])
def list_cotizaciones(
    search: str = Query(""),
    estado: str = Query(""),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db_session),
    user: Usuario = Depends(get_authenticated_user),
):
    repo = CotizacionRepository(db)
    roles = [r.nombre for r in user.roles]
    uid = None if ("ADMIN" in roles or "ADMINISTRADOR" in roles) else user.id
    skip = (page - 1) * limit
    items, total = repo.search(search=search, estado=estado, usuario_id=uid, skip=skip, limit=limit)

    def enrich(c):
        c.cliente_nombre = c.cliente.nombre if c.cliente else None
        c.usuario_nombre = f"{c.usuario.nombres} {c.usuario.apellidos}" if c.usuario else None
        return c

    return {"data": [enrich(c) for c in items], "total": total, "page": page, "limit": limit, "pages": math.ceil(total / limit) or 1}


@router.get("/{id}", response_model=CotizacionOut)
def get_cotizacion(id: UUID, db: Session = Depends(get_db_session), _: Usuario = Depends(get_authenticated_user)):
    cot = CotizacionRepository(db).get_with_items(id)
    if not cot:
        raise HTTPException(404, "Cotización no encontrada")
    cot.cliente_nombre = cot.cliente.nombre if cot.cliente else None
    cot.cliente_email = cot.cliente.contacto_email if cot.cliente else None
    cot.usuario_nombre = f"{cot.usuario.nombres} {cot.usuario.apellidos}" if cot.usuario else None
    for item in cot.items:
        item.producto_nombre = item.producto.nombre if item.producto else None
        item.producto_codigo = item.producto.codigo if item.producto else None
    return cot


@router.post("/", response_model=CotizacionOut, status_code=201)
def create_cotizacion(data: CotizacionCreate, db: Session = Depends(get_db_session), user: Usuario = Depends(get_authenticated_user)):
    return CotizacionService(db).create(data, user.id)


@router.put("/{id}", response_model=CotizacionOut)
def update_cotizacion(id: UUID, data: CotizacionUpdate, db: Session = Depends(get_db_session), user: Usuario = Depends(get_authenticated_user)):
    repo = CotizacionRepository(db)
    cot = repo.get(id)
    if not cot:
        raise HTTPException(404, "Cotización no encontrada")
    return CotizacionService(db).update(cot, data)


@router.delete("/{id}", status_code=204)
def delete_cotizacion(id: UUID, db: Session = Depends(get_db_session), _: Usuario = Depends(require_admin)):
    repo = CotizacionRepository(db)
    cot = repo.get(id)
    if not cot:
        raise HTTPException(404, "Cotización no encontrada")
    repo.delete(cot)


@router.patch("/{id}/estado", response_model=MessageResponse)
def update_estado(
    id: UUID,
    body: EstadoUpdate,
    db: Session = Depends(get_db_session),
    _: Usuario = Depends(get_authenticated_user),
):
    estados_validos = {"BORRADOR", "PENDIENTE", "ACEPTADA", "RECHAZADA", "CANCELADA"}
    if body.estado not in estados_validos:
        raise HTTPException(400, f"Estado inválido: {body.estado}")
    cot = CotizacionRepository(db).get(id)
    if not cot:
        raise HTTPException(404, "Cotización no encontrada")
    cot.estado = body.estado
    db.commit()
    return {"message": f"Estado actualizado a {body.estado}"}


@router.get("/{id}/pdf")
def descargar_pdf(id: UUID, db: Session = Depends(get_db_session), _: Usuario = Depends(get_authenticated_user)):
    from app.utils.pdf import generate_cotizacion_pdf
    cot = CotizacionRepository(db).get_with_items(id)
    if not cot:
        raise HTTPException(404, "Cotización no encontrada")
    if cot.cliente:
        cot.cliente_nombre          = cot.cliente.nombre
        cot.cliente_nit             = cot.cliente.rut or ""
        cot.cliente_ciudad          = cot.cliente.ciudad or ""
        cot.cliente_telefono        = cot.cliente.contacto_telefono or ""
        cot.cliente_contacto_nombre = cot.cliente.contacto_nombre or ""
        cot.cliente_contacto_email  = cot.cliente.contacto_email or "tripleaconstruccionessas@gmail.com"
    else:
        cot.cliente_nombre = cot.cliente_nit = cot.cliente_ciudad = ""
        cot.cliente_telefono = cot.cliente_contacto_nombre = ""
        cot.cliente_contacto_email = "tripleaconstruccionessas@gmail.com"
    for item in cot.items:
        item.producto_nombre  = item.producto.nombre if item.producto else None
        item.producto_unidad  = item.unidad or (item.producto.unidad_medida if item.producto else "UN")
        item.unidad           = item.producto_unidad
    try:
        pdf_bytes = generate_cotizacion_pdf(cot)
    except Exception as exc:
        raise HTTPException(500, f"Error generando PDF: {exc}")
    filename = f"Cotizacion-{cot.numero}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/{id}/enviar-email", response_model=MessageResponse)
def enviar_email_cotizacion(
    id: UUID,
    body: EnviarEmailRequest,
    db: Session = Depends(get_db_session),
    user: Usuario = Depends(get_authenticated_user),
):
    cot = CotizacionRepository(db).get_with_items(id)
    if not cot:
        raise HTTPException(404, "Cotización no encontrada")
    cot.cliente_nombre = cot.cliente.nombre if cot.cliente else None
    cot.usuario_nombre = f"{cot.usuario.nombres} {cot.usuario.apellidos}" if cot.usuario else None
    for item in cot.items:
        item.producto_nombre = item.producto.nombre if item.producto else None
        item.producto_codigo = item.producto.codigo if item.producto else None

    sender_nombre = f"{user.nombres} {user.apellidos}"
    sent = send_cotizacion_email(
        to_email=body.email,
        cotizacion=cot,
        sender_nombre=sender_nombre,
        asunto=body.asunto,
        mensaje_extra=body.mensaje,
    )
    if not sent:
        raise HTTPException(500, "No se pudo enviar el correo. Verifica la configuración SMTP.")
    return {"message": f"Cotización enviada a {body.email}"}
