"""
Telegram Bot — Notificaciones y control del CRM desde Telegram
"""
import asyncio
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode
from loguru import logger
from config.settings import settings


# ─────────────────────────────────────────────
# ENVÍO DE NOTIFICACIONES (sincrónico)
# ─────────────────────────────────────────────
def send_notification(message: str):
    """Envía mensaje al admin de Telegram. Llamado desde workers."""
    async def _send():
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        await bot.send_message(
            chat_id=settings.TELEGRAM_ADMIN_CHAT_ID,
            text=message,
            parse_mode=ParseMode.MARKDOWN,
        )

    try:
        asyncio.get_event_loop().run_until_complete(_send())
    except Exception as e:
        # Si no hay event loop activo, crear uno nuevo
        try:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(_send())
            loop.close()
        except Exception as e2:
            logger.error(f"Error enviando notificación Telegram: {e2}")


# ─────────────────────────────────────────────
# COMANDOS DEL BOT
# ─────────────────────────────────────────────
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"👋 Hola! Soy el asistente de *{settings.BUSINESS_NAME}*.\n\n"
        "Comandos disponibles:\n"
        "• /clientes — Últimos clientes\n"
        "• /pendientes — Emails sin responder\n"
        "• /presupuestos — Resumen de presupuestos\n"
        "• /stats — Estadísticas del día\n"
        "• /buscar [nombre] — Buscar cliente",
        parse_mode=ParseMode.MARKDOWN,
    )


async def cmd_clientes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra los últimos 5 clientes."""
    from db.database import SessionLocal
    from db.models import Client

    db = SessionLocal()
    try:
        clients = db.query(Client).order_by(Client.created_at.desc()).limit(5).all()
        if not clients:
            await update.message.reply_text("No hay clientes registrados aún.")
            return

        text = "👥 *Últimos clientes:*\n\n"
        for c in clients:
            text += f"• *{c.name}*\n  📧 {c.email}\n  📞 {c.phone or 'Sin teléfono'}\n\n"

        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    finally:
        db.close()


async def cmd_pendientes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra correos que necesitan respuesta."""
    from db.database import SessionLocal
    from db.models import EmailRecord, EmailStatus

    db = SessionLocal()
    try:
        pendientes = db.query(EmailRecord).filter(
            EmailRecord.status == EmailStatus.processing
        ).order_by(EmailRecord.received_at.desc()).limit(10).all()

        if not pendientes:
            await update.message.reply_text("✅ No hay correos pendientes de respuesta.")
            return

        text = f"⏳ *{len(pendientes)} correos pendientes:*\n\n"
        for e in pendientes:
            urgency_emoji = "🔴" if e.ai_intent == "presupuesto" else "🟡"
            text += f"{urgency_emoji} *{e.from_name or e.from_email}*\n"
            text += f"   📌 {e.subject[:50]}...\n"
            text += f"   🏷️ {e.ai_intent or 'sin clasificar'}\n\n"

        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    finally:
        db.close()


async def cmd_presupuestos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Resumen de presupuestos."""
    from db.database import SessionLocal
    from db.models import Budget, BudgetStatus
    from sqlalchemy import func

    db = SessionLocal()
    try:
        total = db.query(Budget).count()
        pending = db.query(Budget).filter(Budget.status == BudgetStatus.pending).count()
        accepted = db.query(Budget).filter(Budget.status == BudgetStatus.accepted).count()
        rejected = db.query(Budget).filter(Budget.status == BudgetStatus.rejected).count()

        text = (
            "💰 *Resumen de Presupuestos*\n\n"
            f"📊 Total: {total}\n"
            f"⏳ Pendientes: {pending}\n"
            f"✅ Aceptados: {accepted}\n"
            f"❌ Rechazados: {rejected}\n"
        )

        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    finally:
        db.close()


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Estadísticas del día."""
    from db.database import SessionLocal
    from db.models import Client, EmailRecord
    from datetime import datetime, date

    db = SessionLocal()
    try:
        today = date.today()
        new_clients = db.query(Client).filter(
            func.date(Client.created_at) == today
        ).count()
        emails_today = db.query(EmailRecord).filter(
            func.date(EmailRecord.received_at) == today
        ).count()

        from sqlalchemy import func
        text = (
            f"📈 *Estadísticas de hoy ({today}):*\n\n"
            f"👤 Nuevos clientes: {new_clients}\n"
            f"📧 Correos recibidos: {emails_today}\n"
        )
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    finally:
        db.close()


async def cmd_buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Busca un cliente por nombre o email."""
    if not context.args:
        await update.message.reply_text("Uso: /buscar [nombre o email]")
        return

    query = " ".join(context.args).lower()
    from db.database import SessionLocal
    from db.models import Client

    db = SessionLocal()
    try:
        clients = db.query(Client).filter(
            (Client.name.ilike(f"%{query}%")) | (Client.email.ilike(f"%{query}%"))
        ).limit(5).all()

        if not clients:
            await update.message.reply_text(f"No se encontró ningún cliente con '{query}'")
            return

        text = f"🔍 *Resultados para '{query}':*\n\n"
        for c in clients:
            text += (
                f"👤 *{c.name}*\n"
                f"   📧 {c.email}\n"
                f"   📞 {c.phone or 'Sin teléfono'}\n"
                f"   📍 {c.address or 'Sin dirección'}\n\n"
            )
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    finally:
        db.close()


# ─────────────────────────────────────────────
# INICIAR BOT
# ─────────────────────────────────────────────
def run_bot():
    """Inicia el bot de Telegram (modo polling)."""
    logger.info("🤖 Iniciando bot de Telegram...")

    async def _run():
        app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

        app.add_handler(CommandHandler("start", cmd_start))
        app.add_handler(CommandHandler("clientes", cmd_clientes))
        app.add_handler(CommandHandler("pendientes", cmd_pendientes))
        app.add_handler(CommandHandler("presupuestos", cmd_presupuestos))
        app.add_handler(CommandHandler("stats", cmd_stats))
        app.add_handler(CommandHandler("buscar", cmd_buscar))

        logger.info("✅ Bot de Telegram listo")
        async with app:
            await app.initialize()
            await app.start()
            await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
            await asyncio.Event().wait()

    asyncio.run(_run())
