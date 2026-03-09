"""
Script de autenticación con Google OAuth2.
Ejecutar UNA VEZ para generar el token: python scripts/auth_google.py
"""
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from loguru import logger

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/spreadsheets.readonly",
]

CREDENTIALS_PATH = "config/google_credentials.json"
TOKEN_PATH = "config/gmail_token.json"


def main():
    if not os.path.exists(CREDENTIALS_PATH):
        print(f"""
❌ No se encontró {CREDENTIALS_PATH}

Pasos para obtener las credenciales:
1. Ve a https://console.cloud.google.com
2. Crea o selecciona un proyecto
3. Ve a "APIs y servicios" → "Habilitar APIs"
   - Habilita: Gmail API
   - Habilita: Google Sheets API
4. Ve a "Credenciales" → "Crear credenciales" → "ID de cliente OAuth"
5. Tipo de aplicación: "App de escritorio"
6. Descarga el JSON y guárdalo como: {CREDENTIALS_PATH}
7. Ejecuta este script nuevamente
        """)
        return

    logger.info("Iniciando autenticación con Google...")
    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
    creds = flow.run_local_server(port=0)

    os.makedirs("config", exist_ok=True)
    with open(TOKEN_PATH, "w") as f:
        f.write(creds.to_json())

    logger.success(f"✅ Token guardado en {TOKEN_PATH}")
    logger.info("Ya puedes iniciar el CRM.")


if __name__ == "__main__":
    main()
