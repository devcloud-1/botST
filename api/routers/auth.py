"""
Router: Autenticación Google OAuth2 vía web
Permite autenticar desde el navegador sin necesitar Python local.
Ruta: /auth/setup
"""
import json
import os
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from loguru import logger

router = APIRouter()

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/spreadsheets.readonly",
]

TOKEN_PATH = "config/gmail_token.json"
CREDENTIALS_PATH = "config/google_credentials.json"


def get_redirect_uri(request: Request) -> str:
    """Construye la URI de redirección correcta según el entorno."""
    base = str(request.base_url).rstrip("/")
    return f"{base}/auth/callback"


@router.get("/setup", response_class=HTMLResponse)
async def auth_setup(request: Request):
    """Página principal de configuración."""
    token_exists = os.path.exists(TOKEN_PATH)
    creds_exist = os.path.exists(CREDENTIALS_PATH)

    status_token = "✅ Token activo" if token_exists else "❌ Sin token"
    status_creds = "✅ Credenciales cargadas" if creds_exist else "❌ Sin credenciales"

    connect_btn = ""
    if creds_exist and not token_exists:
        connect_btn = '<a href="/auth/start" class="btn">🔗 Conectar con Google</a>'
    elif creds_exist and token_exists:
        connect_btn = '<a href="/auth/start" class="btn secondary">🔄 Reconectar Google</a>'
    else:
        connect_btn = '<p class="warn">⚠️ Primero sube el archivo <code>google_credentials.json</code> a la carpeta <code>config/</code> del servidor.</p>'

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Setup — CRM Servicio Técnico</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: system-ui, sans-serif; background: #0f172a; color: #e2e8f0; display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 2rem; }}
    .card {{ background: #1e293b; border-radius: 16px; padding: 2.5rem; max-width: 480px; width: 100%; border: 1px solid #334155; }}
    h1 {{ font-size: 1.5rem; margin-bottom: 0.5rem; color: #f8fafc; }}
    p.sub {{ color: #94a3b8; margin-bottom: 2rem; font-size: 0.9rem; }}
    .status-row {{ display: flex; align-items: center; gap: 0.75rem; padding: 0.85rem 1rem; background: #0f172a; border-radius: 8px; margin-bottom: 0.75rem; font-size: 0.9rem; border: 1px solid #1e3a5f; }}
    .btn {{ display: block; text-align: center; background: #3b82f6; color: white; padding: 0.85rem 1.5rem; border-radius: 8px; text-decoration: none; font-weight: 600; margin-top: 1.5rem; transition: background 0.2s; }}
    .btn:hover {{ background: #2563eb; }}
    .btn.secondary {{ background: #475569; }}
    .btn.secondary:hover {{ background: #334155; }}
    .warn {{ background: #451a03; border: 1px solid #92400e; color: #fcd34d; padding: 1rem; border-radius: 8px; margin-top: 1.5rem; font-size: 0.85rem; line-height: 1.5; }}
    code {{ background: #0f172a; padding: 2px 6px; border-radius: 4px; font-size: 0.8rem; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>🔧 Setup del CRM</h1>
    <p class="sub">Configuración de conexión con Google</p>
    <div class="status-row">{status_creds}</div>
    <div class="status-row">{status_token}</div>
    {connect_btn}
  </div>
</body>
</html>"""
    return HTMLResponse(content=html)


@router.get("/start")
async def auth_start(request: Request):
    """Inicia el flujo OAuth2 — redirige a Google."""
    if not os.path.exists(CREDENTIALS_PATH):
        return HTMLResponse("<h2>Error: No se encontró google_credentials.json en config/</h2>", status_code=400)

    redirect_uri = get_redirect_uri(request)

    flow = Flow.from_client_secrets_file(
        CREDENTIALS_PATH,
        scopes=SCOPES,
        redirect_uri=redirect_uri,
    )

    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",  # Fuerza a mostrar pantalla de permisos para obtener refresh_token
    )

    # Guardar state en cookie simple
    response = RedirectResponse(url=auth_url)
    response.set_cookie("oauth_state", state, max_age=600, httponly=True)
    return response


@router.get("/callback")
async def auth_callback(request: Request, code: str = None, state: str = None, error: str = None):
    """Google redirige aquí con el código de autorización."""
    if error:
        return HTMLResponse(f"<h2>❌ Error: {error}</h2>", status_code=400)

    if not code:
        return HTMLResponse("<h2>❌ No se recibió código de autorización.</h2>", status_code=400)

    redirect_uri = get_redirect_uri(request)

    try:
        flow = Flow.from_client_secrets_file(
            CREDENTIALS_PATH,
            scopes=SCOPES,
            redirect_uri=redirect_uri,
        )
        flow.fetch_token(code=code)
        creds = flow.credentials

        # Guardar token
        os.makedirs("config", exist_ok=True)
        token_data = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": list(creds.scopes) if creds.scopes else SCOPES,
        }
        with open(TOKEN_PATH, "w") as f:
            json.dump(token_data, f, indent=2)

        logger.success("✅ Token de Google guardado correctamente")

        return HTMLResponse("""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Conectado — CRM</title>
  <style>
    body { font-family: system-ui, sans-serif; background: #0f172a; color: #e2e8f0; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
    .card { background: #1e293b; border-radius: 16px; padding: 2.5rem; max-width: 420px; text-align: center; border: 1px solid #334155; }
    h1 { font-size: 2rem; margin-bottom: 1rem; }
    p { color: #94a3b8; margin-bottom: 1.5rem; }
    a { color: #3b82f6; text-decoration: none; font-weight: 600; }
  </style>
</head>
<body>
  <div class="card">
    <h1>✅</h1>
    <h2>¡Google conectado!</h2>
    <p>El CRM ya puede leer y enviar correos de Gmail y acceder a Google Sheets.</p>
    <a href="/auth/setup">← Volver al setup</a>
  </div>
</body>
</html>""")

    except Exception as e:
        logger.error(f"Error en callback OAuth: {e}")
        return HTMLResponse(f"""
<h2>❌ Error al obtener el token</h2>
<pre>{str(e)}</pre>
<p><a href="/auth/setup">← Volver</a></p>
""", status_code=500)
