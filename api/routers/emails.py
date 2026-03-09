"""
Router: Correos
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from db.database import get_db
from db.models import EmailRecord, EmailStatus
from api.services.gmail_service import send_email
from ai.email_writer import draft_reply
from api.services.sheets_service import get_knowledge_context

router = APIRouter()


@router.get("/")
def list_emails(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(EmailRecord)
    if status:
        query = query.filter(EmailRecord.status == status)
    total = query.count()
    items = query.order_by(EmailRecord.received_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "items": items}


@router.get("/{email_id}")
def get_email(email_id: int, db: Session = Depends(get_db)):
    email = db.query(EmailRecord).filter(EmailRecord.id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Correo no encontrado")
    return email


@router.post("/{email_id}/reply")
def send_reply(
    email_id: int,
    body: dict,  # {"body": "texto del correo", "auto": true/false}
    db: Session = Depends(get_db),
):
    """Envía una respuesta al correo. Si auto=true, usa la respuesta sugerida por IA."""
    email = db.query(EmailRecord).filter(EmailRecord.id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Correo no encontrado")

    reply_text = body.get("body")

    if body.get("auto") and email.ai_suggested_reply:
        reply_text = email.ai_suggested_reply
    elif not reply_text:
        raise HTTPException(status_code=400, detail="Se requiere el cuerpo del correo")

    success = send_email(
        to_email=email.from_email,
        subject=email.subject,
        body=reply_text,
        reply_to_thread_id=email.gmail_thread_id,
    )

    if success:
        email.status = EmailStatus.replied
        from datetime import datetime, timezone
        email.replied_at = datetime.now(timezone.utc)
        email.reply_body = reply_text
        db.commit()
        return {"ok": True, "message": "Correo enviado"}
    else:
        raise HTTPException(status_code=500, detail="Error enviando correo")


@router.post("/{email_id}/draft-reply")
def generate_draft(
    email_id: int,
    instructions: Optional[dict] = None,
    db: Session = Depends(get_db),
):
    """Genera una nueva respuesta con IA (sin enviar)."""
    email = db.query(EmailRecord).filter(EmailRecord.id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Correo no encontrado")

    sheets_context = get_knowledge_context(email.ai_intent or "general")
    custom = (instructions or {}).get("instructions")

    draft = draft_reply(
        original_subject=email.subject,
        original_body=email.body,
        client_name=email.from_name,
        intent=email.ai_intent or "consulta",
        custom_instructions=custom,
        sheets_context=sheets_context,
    )

    return {"draft": draft}


@router.patch("/{email_id}/status")
def update_status(email_id: int, data: dict, db: Session = Depends(get_db)):
    email = db.query(EmailRecord).filter(EmailRecord.id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Correo no encontrado")
    if data.get("status") in [s.value for s in EmailStatus]:
        email.status = data["status"]
        db.commit()
    return {"ok": True}
