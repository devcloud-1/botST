"""
AI Email Reader — Interpreta correos entrantes con Claude
Extrae intención, datos del cliente, y genera respuesta sugerida.
"""
import json
from typing import Optional
import anthropic
from loguru import logger
from config.settings import settings


client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)


SYSTEM_PROMPT = """Eres el asistente de IA de {business_name}, un servicio técnico de reparación de equipos.
Tu trabajo es analizar correos entrantes de clientes y extraer información estructurada.

Responde SIEMPRE en JSON válido con esta estructura exacta:
{{
  "intent": "consulta|presupuesto|envio|seguimiento|reclamo|otro",
  "sentiment": "positivo|neutro|negativo",
  "summary": "resumen breve del correo en 1-2 oraciones",
  "extracted_data": {{
    "name": "nombre completo del remitente o null",
    "phone": "teléfono encontrado en el correo o null",
    "address": "dirección exacta mencionada o null",
    "city": "ciudad o null",
    "equipment_type": "tipo de equipo a reparar o null",
    "equipment_brand": "marca del equipo o null",
    "problem_description": "descripción del problema técnico o null"
  }},
  "needs_reply": true|false,
  "urgency": "alta|media|baja",
  "suggested_reply": "respuesta sugerida en español o null si no necesita respuesta inmediata"
}}

Reglas:
- Detecta datos de envío aunque estén en texto libre ("te mando el equipo a Av. Providencia 123, Santiago")
- Si el cliente pregunta por precios, marca needs_reply=true
- Si es un presupuesto aceptado, marca intent="presupuesto" y urgency="alta"
- La suggested_reply debe ser cordial, profesional y en nombre de {business_name}
- Incluye siempre el teléfono {business_phone} y horario {business_hours} si es relevante
- NO inventes información que no esté en el correo"""


def analyze_email(
    from_email: str,
    from_name: str,
    subject: str,
    body: str,
    sheets_context: Optional[str] = None,
) -> dict:
    """
    Analiza un correo con Claude y retorna datos estructurados.

    Args:
        from_email: Email del remitente
        from_name: Nombre del remitente
        subject: Asunto del correo
        body: Cuerpo del correo
        sheets_context: Información relevante de Google Sheets (FAQs, precios, etc.)

    Returns:
        Dict con intent, extracted_data, suggested_reply, etc.
    """
    system = SYSTEM_PROMPT.format(
        business_name=settings.BUSINESS_NAME,
        business_phone=settings.BUSINESS_PHONE,
        business_hours=settings.BUSINESS_HOURS,
    )

    user_message = f"""Analiza este correo y extrae toda la información relevante:

DE: {from_name} <{from_email}>
ASUNTO: {subject}
CUERPO:
{body}
"""

    if sheets_context:
        user_message += f"""
---
INFORMACIÓN DE REFERENCIA (de nuestra base de datos interna para responder):
{sheets_context}
---
Usa esta información para generar una respuesta más precisa si aplica.
"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            system=system,
            messages=[{"role": "user", "content": user_message}],
        )

        raw = response.content[0].text.strip()

        # Limpiar posibles backticks
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        result = json.loads(raw)
        logger.info(f"✅ Email analizado: intent={result.get('intent')}, urgency={result.get('urgency')}")
        return result

    except json.JSONDecodeError as e:
        logger.error(f"Error parseando JSON de Claude: {e}")
        return _fallback_result()
    except Exception as e:
        logger.error(f"Error analizando email con IA: {e}")
        return _fallback_result()


def _fallback_result() -> dict:
    """Resultado por defecto cuando la IA falla."""
    return {
        "intent": "otro",
        "sentiment": "neutro",
        "summary": "No se pudo analizar automáticamente. Requiere revisión manual.",
        "extracted_data": {
            "name": None, "phone": None, "address": None,
            "city": None, "equipment_type": None,
            "equipment_brand": None, "problem_description": None,
        },
        "needs_reply": False,
        "urgency": "media",
        "suggested_reply": None,
    }
