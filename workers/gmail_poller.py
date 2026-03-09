"""
Gmail Poller Worker — Revisa correos nuevos cada N segundos
Procesa con IA y guarda en base de datos.
"""
from datetime import datetime, timezone
from loguru import logger
from sqlalchemy.orm import Session

from db.database import SessionLocal
from db.models import Client, EmailRecord, EmailStatus, Shipment
from api.services.gmail_service import fetch_unread_emails, mark_as_read
from api.services.sheets_service import get_knowledge_context
from ai.email_reader import analyze_email
from telegram.bot import send_notification


def process_new_emails():
    """
    Función principal del worker.
    - Obtiene correos no leídos de Gmail
    - Los analiza con IA
    - Guarda clientes y registros en DB
    - Notifica en Telegram
    """
    logger.info("🔄 Iniciando revisión de correos...")
    db = SessionLocal()

    try:
        emails = fetch_unread_emails(max_results=10)

        if not emails:
            logger.info("📭 No hay correos nuevos.")
            return

        for email_data in emails:
            _process_single_email(db, email_data)

        db.commit()
        logger.info(f"✅ Procesados {len(emails)} correos.")

    except Exception as e:
        logger.error(f"Error en worker de Gmail: {e}")
        db.rollback()
    finally:
        db.close()


def _process_single_email(db: Session, email_data: dict):
    """Procesa un correo individual."""

    # Verificar si ya fue procesado
    existing = db.query(EmailRecord).filter(
        EmailRecord.gmail_message_id == email_data["gmail_message_id"]
    ).first()

    if existing:
        logger.debug(f"Correo {email_data['gmail_message_id']} ya procesado, omitiendo.")
        return

    logger.info(f"📧 Procesando correo de {email_data['from_email']}: {email_data['subject']}")

    # Obtener contexto de Google Sheets (para respuestas más precisas)
    sheets_context = get_knowledge_context("general")

    # Analizar con IA
    analysis = analyze_email(
        from_email=email_data["from_email"],
        from_name=email_data["from_name"],
        subject=email_data["subject"],
        body=email_data["body"],
        sheets_context=sheets_context,
    )

    # Buscar o crear cliente
    client = _get_or_create_client(db, email_data, analysis)

    # Guardar registro del correo
    record = EmailRecord(
        gmail_message_id=email_data["gmail_message_id"],
        gmail_thread_id=email_data["gmail_thread_id"],
        client_id=client.id if client else None,
        from_email=email_data["from_email"],
        from_name=email_data["from_name"],
        subject=email_data["subject"],
        body=email_data["body"],
        received_at=email_data["received_at"],
        ai_summary=analysis.get("summary"),
        ai_intent=analysis.get("intent"),
        ai_sentiment=analysis.get("sentiment"),
        ai_extracted_data=analysis.get("extracted_data"),
        ai_suggested_reply=analysis.get("suggested_reply"),
        status=EmailStatus.processing if analysis.get("needs_reply") else EmailStatus.unread,
    )
    db.add(record)
    db.flush()  # Para obtener el ID

    # Si hay datos de envío, guardar shipment
    extracted = analysis.get("extracted_data", {})
    if extracted.get("address") and analysis.get("intent") == "envio":
        _create_shipment(db, client, record, extracted)

    # Marcar como leído en Gmail
    mark_as_read(email_data["gmail_message_id"])

    # Notificar en Telegram
    _notify_telegram(email_data, analysis, client)


def _get_or_create_client(db: Session, email_data: dict, analysis: dict) -> Client:
    """Busca cliente por email, lo crea si no existe."""
    extracted = analysis.get("extracted_data", {})

    client = db.query(Client).filter(Client.email == email_data["from_email"]).first()

    if not client:
        # Crear nuevo cliente
        client = Client(
            name=extracted.get("name") or email_data.get("from_name") or email_data["from_email"],
            email=email_data["from_email"],
            phone=extracted.get("phone"),
            address=extracted.get("address"),
            city=extracted.get("city"),
        )
        db.add(client)
        db.flush()
        logger.info(f"👤 Nuevo cliente creado: {client.name} <{client.email}>")
    else:
        # Actualizar datos si la IA extrajo info nueva
        updated = False
        if not client.phone and extracted.get("phone"):
            client.phone = extracted["phone"]
            updated = True
        if not client.address and extracted.get("address"):
            client.address = extracted["address"]
            updated = True
        if not client.city and extracted.get("city"):
            client.city = extracted["city"]
            updated = True
        if updated:
            logger.info(f"👤 Cliente actualizado: {client.name}")

    return client


def _create_shipment(db: Session, client: Client, record: EmailRecord, extracted: dict):
    """Crea registro de envío con datos extraídos por IA."""
    shipment = Shipment(
        client_id=client.id,
        email_record_id=record.id,
        recipient_name=extracted.get("name") or client.name,
        recipient_email=client.email,
        recipient_phone=extracted.get("phone") or client.phone,
        recipient_address=extracted.get("address"),
        recipient_city=extracted.get("city"),
    )
    db.add(shipment)
    logger.info(f"📦 Datos de envío registrados para {client.name}")


def _notify_telegram(email_data: dict, analysis: dict, client: Client):
    """Envía notificación a Telegram."""
    urgency_emoji = {"alta": "🔴", "media": "🟡", "baja": "🟢"}.get(
        analysis.get("urgency", "media"), "🟡"
    )
    intent_emoji = {
        "consulta": "❓", "presupuesto": "💰", "envio": "📦",
        "seguimiento": "🔍", "reclamo": "⚠️", "otro": "📧",
    }.get(analysis.get("intent", "otro"), "📧")

    message = (
        f"{urgency_emoji} {intent_emoji} *Nuevo correo*\n"
        f"👤 *De:* {email_data['from_name'] or email_data['from_email']}\n"
        f"📧 *Email:* `{email_data['from_email']}`\n"
        f"📌 *Asunto:* {email_data['subject']}\n"
        f"🏷️ *Tipo:* {analysis.get('intent', 'desconocido')}\n"
        f"📝 *Resumen:* {analysis.get('summary', 'Sin resumen')}\n"
    )

    if analysis.get("needs_reply"):
        message += f"\n⚡ *Requiere respuesta*"

    send_notification(message)
