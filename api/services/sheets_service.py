"""
Google Sheets Service — Lee la base de conocimiento del negocio
"""
import os
from typing import Optional
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from loguru import logger
from config.settings import settings

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
TOKEN_PATH = "config/gmail_token.json"  # Mismo token (incluye permisos de Sheets)

# Nombres de las hojas esperadas
SHEET_SERVICES = "Servicios"
SHEET_FAQS = "FAQs"
SHEET_SHIPPING = "Zonas_envio"
SHEET_WARRANTIES = "Garantias"


def get_sheets_service():
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    return build("sheets", "v4", credentials=creds)


def get_knowledge_context(query_type: str = "general") -> str:
    """
    Obtiene contexto relevante de Google Sheets según el tipo de consulta.
    Retorna texto formateado para pasar al prompt de IA.
    """
    try:
        service = get_sheets_service()
        sheet_id = settings.GOOGLE_SHEETS_ID
        context_parts = []

        # Siempre incluir FAQs
        faqs = _read_sheet(service, sheet_id, SHEET_FAQS)
        if faqs:
            context_parts.append("PREGUNTAS FRECUENTES:\n" + _format_rows(faqs))

        # Incluir servicios si es consulta de precio/servicio
        if query_type in ("consulta", "presupuesto", "general"):
            services = _read_sheet(service, sheet_id, SHEET_SERVICES)
            if services:
                context_parts.append("SERVICIOS Y PRECIOS:\n" + _format_rows(services))

        # Incluir envíos si es envío
        if query_type in ("envio", "general"):
            shipping = _read_sheet(service, sheet_id, SHEET_SHIPPING)
            if shipping:
                context_parts.append("ZONAS DE ENVÍO:\n" + _format_rows(shipping))

        # Garantías siempre útiles
        warranties = _read_sheet(service, sheet_id, SHEET_WARRANTIES)
        if warranties:
            context_parts.append("GARANTÍAS:\n" + _format_rows(warranties))

        return "\n\n".join(context_parts) if context_parts else ""

    except Exception as e:
        logger.warning(f"No se pudo leer Google Sheets: {e}")
        return ""


def _read_sheet(service, sheet_id: str, sheet_name: str) -> list[list]:
    """Lee todas las filas de una hoja."""
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=sheet_name,
        ).execute()
        return result.get("values", [])
    except Exception as e:
        logger.warning(f"No se pudo leer hoja '{sheet_name}': {e}")
        return []


def _format_rows(rows: list[list]) -> str:
    """Formatea filas como texto legible."""
    if not rows:
        return ""
    header = rows[0] if rows else []
    lines = []
    for row in rows[1:]:
        if row:
            pairs = [f"{header[i]}: {row[i]}" for i in range(min(len(header), len(row)))]
            lines.append(" | ".join(pairs))
    return "\n".join(lines[:30])  # Máximo 30 filas para no saturar el contexto


def get_sheets_template() -> dict:
    """
    Retorna la estructura de plantilla recomendada para el Google Sheets.
    Útil para crear la hoja desde cero.
    """
    return {
        "Servicios": {
            "headers": ["Servicio", "Descripción", "Precio_base", "Precio_max", "Tiempo_estimado", "Incluye"],
            "example": ["Diagnóstico", "Evaluación completa del equipo", "5000", "15000", "1-2 días hábiles", "Informe detallado"],
        },
        "FAQs": {
            "headers": ["Pregunta", "Respuesta", "Tags"],
            "example": ["¿Cuánto demora una reparación?", "Depende del tipo de equipo. En promedio 3-5 días hábiles.", "tiempo, demora, plazo"],
        },
        "Zonas_envio": {
            "headers": ["Region", "Ciudad", "Costo_envio", "Tiempo_entrega", "Operador"],
            "example": ["Metropolitana", "Santiago", "3500", "1-2 días", "Starken"],
        },
        "Garantias": {
            "headers": ["Tipo_servicio", "Garantia_dias", "Condiciones", "Qué_cubre"],
            "example": ["Reparación electrónica", "90", "Misma falla original", "Mano de obra y repuesto instalado"],
        },
    }
