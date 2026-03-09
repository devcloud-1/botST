"""
Router: Envíos
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import Shipment, ShipmentStatus

router = APIRouter()


@router.get("/")
def list_shipments(status: str = None, skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    query = db.query(Shipment)
    if status:
        query = query.filter(Shipment.status == status)
    total = query.count()
    items = query.order_by(Shipment.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "items": items}


@router.patch("/{shipment_id}")
def update_shipment(shipment_id: int, data: dict, db: Session = Depends(get_db)):
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        raise HTTPException(status_code=404, detail="Envío no encontrado")

    allowed = ["recipient_name", "recipient_phone", "recipient_address",
               "recipient_city", "tracking_number", "status", "notes"]
    for key, value in data.items():
        if key in allowed:
            setattr(shipment, key, value)
    db.commit()
    db.refresh(shipment)
    return shipment
