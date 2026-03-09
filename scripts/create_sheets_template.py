"""
Crea la plantilla de Google Sheets desde cero.
Ejecutar: python scripts/create_sheets_template.py
"""
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from loguru import logger

TOKEN_PATH = "config/gmail_token.json"

SHEETS_STRUCTURE = {
    "Servicios": [
        ["Servicio", "Descripción", "Precio_base", "Precio_max", "Tiempo_estimado", "Incluye"],
        ["Diagnóstico", "Evaluación completa del equipo", "5000", "15000", "1-2 días hábiles", "Informe detallado"],
        ["Reparación básica", "Reparaciones menores sin repuestos", "15000", "35000", "2-3 días hábiles", "Mano de obra"],
        ["Reparación con repuesto", "Reparación incluyendo partes", "25000", "80000", "3-7 días hábiles", "Repuesto + mano de obra"],
    ],
    "FAQs": [
        ["Pregunta", "Respuesta", "Tags"],
        ["¿Cuánto demora una reparación?", "Depende del tipo de equipo. En promedio 3-5 días hábiles. Si requiere repuesto importado puede demorar más.", "tiempo, demora, plazo"],
        ["¿Tienen garantía los trabajos?", "Sí, todos nuestros trabajos tienen garantía de 90 días por la misma falla.", "garantía"],
        ["¿Cómo puedo enviar mi equipo?", "Puedes traerlo directamente o enviarlo por Starken o Chilexpress a nuestra dirección.", "envío, despacho"],
        ["¿Hacen presupuesto antes de reparar?", "Sí, siempre enviamos presupuesto antes de proceder con cualquier reparación.", "presupuesto, precio"],
    ],
    "Zonas_envio": [
        ["Region", "Ciudad", "Costo_envio", "Tiempo_entrega", "Operador"],
        ["Metropolitana", "Santiago", "3500", "1-2 días", "Starken / Chilexpress"],
        ["Valparaíso", "Valparaíso", "4500", "2-3 días", "Starken"],
        ["Biobío", "Concepción", "5000", "2-3 días", "Starken"],
        ["Araucanía", "Temuco", "5500", "3-4 días", "Starken"],
    ],
    "Garantias": [
        ["Tipo_servicio", "Garantia_dias", "Condiciones", "Qué_cubre"],
        ["Reparación electrónica", "90", "Misma falla original, uso normal", "Mano de obra y repuesto instalado"],
        ["Diagnóstico", "0", "No aplica garantía", "Solo evaluación"],
        ["Limpieza", "30", "Mismo problema de suciedad", "Mano de obra"],
    ],
}


def create_sheets():
    creds = Credentials.from_authorized_user_file(TOKEN_PATH)
    service = build("sheets", "v4", credentials=creds)

    # Crear el spreadsheet
    spreadsheet = service.spreadsheets().create(body={
        "properties": {"title": "CRM Servicio Técnico — Base de Conocimiento"},
        "sheets": [{"properties": {"title": name}} for name in SHEETS_STRUCTURE.keys()],
    }).execute()

    sheet_id = spreadsheet["spreadsheetId"]
    logger.info(f"✅ Spreadsheet creado: https://docs.google.com/spreadsheets/d/{sheet_id}")

    # Agregar datos a cada hoja
    for sheet_name, rows in SHEETS_STRUCTURE.items():
        service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=f"{sheet_name}!A1",
            valueInputOption="RAW",
            body={"values": rows},
        ).execute()
        logger.info(f"  ✅ Hoja '{sheet_name}' poblada con {len(rows)} filas")

    print(f"\n🎉 Google Sheets creado exitosamente!")
    print(f"📋 ID del Sheets: {sheet_id}")
    print(f"🔗 URL: https://docs.google.com/spreadsheets/d/{sheet_id}")
    print(f"\n👉 Agrega este ID a tu .env como: GOOGLE_SHEETS_ID={sheet_id}")


if __name__ == "__main__":
    create_sheets()
