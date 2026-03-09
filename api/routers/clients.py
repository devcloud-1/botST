"""
Router: Clientes
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from db.database import get_db
from db.models import Client, ClientStatus

router = APIRouter()


@router.get("/")
def list_clients(
    search: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(Client)
    if search:
        query = query.filter(
            or_(
                Client.name.ilike(f"%{search}%"),
                Client.email.ilike(f"%{search}%"),
                Client.phone.ilike(f"%{search}%"),
            )
        )
    total = query.count()
    clients = query.order_by(Client.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "items": clients}


@router.get("/{client_id}")
def get_client(client_id: int, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    # Incluir historial
    return {
        "client": client,
        "emails": client.emails,
        "budgets": client.budgets,
        "shipments": client.shipments,
    }


@router.patch("/{client_id}")
def update_client(client_id: int, data: dict, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    allowed = ["name", "phone", "address", "city", "notes"]
    for key, value in data.items():
        if key in allowed:
            setattr(client, key, value)
    db.commit()
    db.refresh(client)
    return client
