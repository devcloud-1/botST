"""
AI Email Writer — Redacta correos profesionales con Claude
"""
import anthropic
from loguru import logger
from config.settings import settings

client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Eres el redactor de correos de {business_name}, un servicio técnico profesional.
Redacta correos claros, cordiales y profesionales en español.

Reglas:
- Tono: profesional pero cercano, nunca robótico
- Incluye siempre una despedida con el nombre del negocio
- Si se solicita presupuesto, sé claro con los precios y condiciones
- Si confirmas recepción de un equipo, da un tiempo estimado realista
- Máximo 200 palabras salvo que se indique lo contrario
- NO uses frases cliché como "Estimado/a cliente"
- Usa el nombre del cliente si está disponible"""


def draft_reply(
    original_subject: str,
    original_body: str,
    client_name: Optional[str],
    intent: str,
    custom_instructions: Optional[str] = None,
    sheets_context: Optional[str] = None,
) -> str:
    """
    Redacta una respuesta al correo del cliente.

    Returns:
        Texto del correo redactado listo para enviar
    """
    from typing import Optional

    system = SYSTEM_PROMPT.format(business_name=settings.BUSINESS_NAME)

    greeting = f"al cliente {client_name}" if client_name else "al cliente"

    user_message = f"""Redacta una respuesta {greeting} para este correo:

ASUNTO ORIGINAL: {original_subject}
CORREO ORIGINAL:
{original_body}

TIPO DE CONSULTA DETECTADA: {intent}
TELÉFONO DE CONTACTO: {settings.BUSINESS_PHONE}
HORARIO: {settings.BUSINESS_HOURS}
"""

    if sheets_context:
        user_message += f"\nINFORMACIÓN DE REFERENCIA:\n{sheets_context}\n"

    if custom_instructions:
        user_message += f"\nINSTRUCCIONES ADICIONALES: {custom_instructions}\n"

    user_message += "\nRedacta solo el cuerpo del correo, sin asunto ni encabezados técnicos."

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            system=system,
            messages=[{"role": "user", "content": user_message}],
        )
        result = response.content[0].text.strip()
        logger.info(f"✅ Correo redactado para intent={intent}")
        return result
    except Exception as e:
        logger.error(f"Error redactando correo: {e}")
        return (
            f"Hola,\n\nGracias por contactarnos. Hemos recibido tu mensaje y "
            f"te responderemos a la brevedad.\n\nSaludos,\n{settings.BUSINESS_NAME}\n"
            f"{settings.BUSINESS_PHONE}"
        )


def draft_budget_email(
    client_name: str,
    equipment: str,
    items: list[dict],
    total: float,
    currency: str = "CLP",
    notes: str = "",
) -> str:
    """Redacta correo de presupuesto formal."""
    items_text = "\n".join(
        [f"- {item.get('description', '')}: ${item.get('amount', 0):,.0f} {currency}"
         for item in items]
    )

    prompt = f"""Redacta un correo de presupuesto para {client_name}.

Equipo: {equipment}
Ítems del presupuesto:
{items_text}
Total: ${total:,.0f} {currency}
Notas adicionales: {notes or 'ninguna'}
Horario: {settings.BUSINESS_HOURS}
Teléfono: {settings.BUSINESS_PHONE}

El correo debe:
1. Presentar el presupuesto de forma clara y profesional
2. Explicar qué incluye cada ítem brevemente
3. Indicar que el presupuesto tiene validez de 15 días
4. Invitar al cliente a contactarnos si tiene preguntas
5. Incluir instrucciones para aceptar (responder el correo o llamar)"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=SYSTEM_PROMPT.format(business_name=settings.BUSINESS_NAME),
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()
    except Exception as e:
        logger.error(f"Error redactando presupuesto: {e}")
        return f"Hola {client_name},\n\nAdjuntamos el presupuesto solicitado por un total de ${total:,.0f} {currency}.\n\nSaludos,\n{settings.BUSINESS_NAME}"
