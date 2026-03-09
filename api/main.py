"""
CRM Servicio Técnico — FastAPI Main
"""
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger

from config.settings import settings
from db.database import engine
from db.models import Base
from api.routers import clients, emails, budgets, shipments, dashboard, auth


# ─────────────────────────────────────────────
# STARTUP / SHUTDOWN
# ─────────────────────────────────────────────
scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"🚀 Iniciando {settings.BUSINESS_NAME} CRM...")

    # Reconstruir credenciales Google desde variable de entorno (Railway)
    try:
        from scripts.credentials_to_env import load_credentials_from_env
        load_credentials_from_env()
        logger.info("✅ Credenciales Google cargadas")
    except Exception as e:
        logger.warning(f"⚠️  No se pudieron cargar credenciales Google: {e}")

    # Crear tablas si no existen
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Base de datos lista")
    except Exception as e:
        logger.error(f"❌ Error conectando a la base de datos: {e}")

    # Iniciar polling de Gmail (solo si el token existe)
    try:
        import os
        from workers.gmail_poller import process_new_emails
        if os.path.exists("config/gmail_token.json"):
            scheduler.add_job(
                process_new_emails,
                "interval",
                seconds=settings.GMAIL_POLL_INTERVAL,
                id="gmail_poller",
            )
            scheduler.start()
            logger.info(f"✅ Gmail poller iniciado (cada {settings.GMAIL_POLL_INTERVAL}s)")
        else:
            logger.warning("⚠️  Gmail no autenticado aún. Ve a /auth/setup para conectar Google.")
    except Exception as e:
        logger.warning(f"⚠️  Gmail poller no iniciado: {e}")

    # Iniciar bot de Telegram en hilo separado
    try:
        from telegram.bot import run_bot
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        logger.info("✅ Bot de Telegram iniciado")
    except Exception as e:
        logger.warning(f"⚠️  Bot de Telegram no iniciado: {e}")

    yield

    # Shutdown
    try:
        if scheduler.running:
            scheduler.shutdown()
    except Exception:
        pass
    logger.info("👋 CRM detenido")


# ─────────────────────────────────────────────
# APP
# ─────────────────────────────────────────────
app = FastAPI(
    title=f"{settings.BUSINESS_NAME} — CRM",
    description="CRM con IA para servicio técnico",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(clients.router, prefix="/api/clients", tags=["Clientes"])
app.include_router(emails.router, prefix="/api/emails", tags=["Correos"])
app.include_router(budgets.router, prefix="/api/budgets", tags=["Presupuestos"])
app.include_router(shipments.router, prefix="/api/shipments", tags=["Envíos"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(auth.router, prefix="/auth", tags=["Autenticación"])


@app.get("/")
async def root():
    return {
        "status": "ok",
        "app": f"{settings.BUSINESS_NAME} CRM",
        "version": "1.0.0",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=settings.APP_PORT, reload=True)
