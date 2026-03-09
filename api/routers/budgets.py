"""
Router: Presupuestos
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from db.database import get_db
from db.models import Budget, BudgetStatus

router = APIRouter()


@router.get("/")
def list_budgets(status: str = None, skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    query = db.query(Budget)
    if status:
        query = query.filter(Budget.status == status)
    total = query.count()
    items = query.order_by(Budget.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "items": items}


@router.post("/")
def create_budget(data: dict, db: Session = Depends(get_db)):
    budget = Budget(
        client_id=data["client_id"],
        description=data.get("description", ""),
        amount=data.get("amount"),
        currency=data.get("currency", "CLP"),
        items=data.get("items"),
        notes=data.get("notes"),
        expires_at=datetime.now(timezone.utc) + timedelta(days=15),
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget


@router.patch("/{budget_id}/status")
def update_budget_status(budget_id: int, data: dict, db: Session = Depends(get_db)):
    budget = db.query(Budget).filter(Budget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")

    new_status = data.get("status")
    if new_status in [s.value for s in BudgetStatus]:
        budget.status = new_status
        budget.responded_at = datetime.now(timezone.utc)
        db.commit()
    return budget
