"""
Router: Dashboard — Estadísticas y métricas
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date
from datetime import date, datetime, timedelta, timezone
from db.database import get_db
from db.models import Client, EmailRecord, Budget, Shipment, BudgetStatus, EmailStatus

router = APIRouter()


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """Estadísticas generales para el dashboard."""
    today = date.today()
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)

    # Totales generales
    total_clients = db.query(Client).count()
    total_emails = db.query(EmailRecord).count()
    total_budgets = db.query(Budget).count()

    # Hoy
    emails_today = db.query(EmailRecord).filter(
        func.date(EmailRecord.received_at) == today
    ).count()
    new_clients_today = db.query(Client).filter(
        func.date(Client.created_at) == today
    ).count()

    # Pendientes
    emails_pending = db.query(EmailRecord).filter(
        EmailRecord.status == EmailStatus.processing
    ).count()
    emails_unread = db.query(EmailRecord).filter(
        EmailRecord.status == EmailStatus.unread
    ).count()

    # Presupuestos
    budgets_pending = db.query(Budget).filter(Budget.status == BudgetStatus.pending).count()
    budgets_accepted = db.query(Budget).filter(Budget.status == BudgetStatus.accepted).count()
    budgets_rejected = db.query(Budget).filter(Budget.status == BudgetStatus.rejected).count()

    # Últimos 7 días — emails por día
    emails_by_day = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = db.query(EmailRecord).filter(
            func.date(EmailRecord.received_at) == day
        ).count()
        emails_by_day.append({"date": str(day), "count": count})

    # Distribución de intents
    intent_counts = (
        db.query(EmailRecord.ai_intent, func.count(EmailRecord.id))
        .group_by(EmailRecord.ai_intent)
        .all()
    )

    return {
        "summary": {
            "total_clients": total_clients,
            "total_emails": total_emails,
            "total_budgets": total_budgets,
            "emails_today": emails_today,
            "new_clients_today": new_clients_today,
            "emails_pending": emails_pending,
            "emails_unread": emails_unread,
        },
        "budgets": {
            "pending": budgets_pending,
            "accepted": budgets_accepted,
            "rejected": budgets_rejected,
        },
        "charts": {
            "emails_by_day": emails_by_day,
            "email_intents": [
                {"intent": intent or "sin clasificar", "count": count}
                for intent, count in intent_counts
            ],
        },
        "recent_emails": [
            {
                "id": e.id,
                "from_email": e.from_email,
                "from_name": e.from_name,
                "subject": e.subject,
                "intent": e.ai_intent,
                "status": e.status,
                "received_at": e.received_at,
            }
            for e in db.query(EmailRecord)
            .order_by(EmailRecord.received_at.desc())
            .limit(5)
            .all()
        ],
    }
