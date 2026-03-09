"""
Gmail Service — Lee y envía correos vía Gmail API
"""
import base64
import os
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from loguru import logger

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]

TOKEN_PATH = "config/gmail_token.json"
CREDENTIALS_PATH = "config/google_credentials.json"


def get_gmail_service():
    """Autenticar y retornar el servicio de Gmail."""
    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def fetch_unread_emails(max_results: int = 20) -> list[dict]:
    """
    Obtiene correos no leídos de la bandeja de entrada.
    Retorna lista de dicts con datos del correo.
    """
    service = get_gmail_service()

    try:
        results = service.users().messages().list(
            userId="me",
            labelIds=["INBOX", "UNREAD"],
            maxResults=max_results,
        ).execute()

        messages = results.get("messages", [])
        emails = []

        for msg in messages:
            email_data = _parse_message(service, msg["id"])
            if email_data:
                emails.append(email_data)

        logger.info(f"📧 Obtenidos {len(emails)} correos no leídos")
        return emails

    except HttpError as e:
        logger.error(f"Error obteniendo correos: {e}")
        return []


def _parse_message(service, message_id: str) -> Optional[dict]:
    """Parsea un mensaje de Gmail a dict estructurado."""
    try:
        msg = service.users().messages().get(
            userId="me",
            id=message_id,
            format="full",
        ).execute()

        headers = {h["name"]: h["value"] for h in msg["payload"].get("headers", [])}

        # Extraer from
        from_raw = headers.get("From", "")
        from_name, from_email = _parse_from(from_raw)

        # Extraer body
        body = _extract_body(msg["payload"])

        # Extraer fecha
        date_str = headers.get("Date", "")
        received_at = _parse_date(date_str)

        return {
            "gmail_message_id": message_id,
            "gmail_thread_id": msg.get("threadId"),
            "from_email": from_email,
            "from_name": from_name,
            "subject": headers.get("Subject", "(sin asunto)"),
            "body": body,
            "received_at": received_at,
        }
    except Exception as e:
        logger.error(f"Error parseando mensaje {message_id}: {e}")
        return None


def _parse_from(from_raw: str) -> tuple[str, str]:
    """Parsea 'Nombre <email@ejemplo.com>' a (nombre, email)."""
    if "<" in from_raw and ">" in from_raw:
        name = from_raw.split("<")[0].strip().strip('"')
        email = from_raw.split("<")[1].replace(">", "").strip()
    else:
        name = ""
        email = from_raw.strip()
    return name, email


def _extract_body(payload: dict) -> str:
    """Extrae el texto plano del body del mensaje."""
    body = ""

    if "parts" in payload:
        for part in payload["parts"]:
            if part.get("mimeType") == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                    break
            elif part.get("mimeType") == "text/html" and not body:
                data = part.get("body", {}).get("data", "")
                if data:
                    # Texto crudo del HTML (simple)
                    import re
                    html = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                    body = re.sub(r"<[^>]+>", " ", html).strip()
    else:
        data = payload.get("body", {}).get("data", "")
        if data:
            body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

    return body[:5000]  # Limitar a 5000 chars para no exceder contexto IA


def _parse_date(date_str: str):
    """Parsea fecha del header de email."""
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(date_str)
    except Exception:
        return datetime.now(timezone.utc)


def send_email(to_email: str, subject: str, body: str, reply_to_thread_id: Optional[str] = None) -> bool:
    """
    Envía un correo desde la cuenta de Gmail configurada.
    """
    service = get_gmail_service()

    try:
        message = MIMEMultipart()
        message["to"] = to_email
        message["subject"] = f"Re: {subject}" if not subject.startswith("Re:") else subject
        message.attach(MIMEText(body, "plain", "utf-8"))

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        body_payload = {"raw": raw}

        if reply_to_thread_id:
            body_payload["threadId"] = reply_to_thread_id

        service.users().messages().send(userId="me", body=body_payload).execute()
        logger.info(f"✅ Correo enviado a {to_email}")
        return True

    except HttpError as e:
        logger.error(f"Error enviando correo a {to_email}: {e}")
        return False


def mark_as_read(message_id: str):
    """Marca un correo como leído."""
    service = get_gmail_service()
    try:
        service.users().messages().modify(
            userId="me",
            id=message_id,
            body={"removeLabelIds": ["UNREAD"]},
        ).execute()
    except HttpError as e:
        logger.error(f"Error marcando como leído {message_id}: {e}")
