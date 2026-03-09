"""
Modelos de base de datos — SQLAlchemy
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean,
    ForeignKey, Enum, Float, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from .database import Base


class ClientStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"


class EmailStatus(str, enum.Enum):
    unread = "unread"
    processing = "processing"
    replied = "replied"
    ignored = "ignored"
    needs_review = "needs_review"


class BudgetStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    expired = "expired"


class ShipmentStatus(str, enum.Enum):
    pending = "pending"
    preparing = "preparing"
    shipped = "shipped"
    delivered = "delivered"


# ─────────────────────────────────────────────
# CLIENTES
# ─────────────────────────────────────────────
class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200), unique=True, index=True, nullable=False)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(Enum(ClientStatus), default=ClientStatus.active)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    emails = relationship("EmailRecord", back_populates="client")
    budgets = relationship("Budget", back_populates="client")
    shipments = relationship("Shipment", back_populates="client")


# ─────────────────────────────────────────────
# CORREOS
# ─────────────────────────────────────────────
class EmailRecord(Base):
    __tablename__ = "email_records"

    id = Column(Integer, primary_key=True, index=True)
    gmail_message_id = Column(String(200), unique=True, index=True)
    gmail_thread_id = Column(String(200), index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)

    # Datos del correo
    from_email = Column(String(200))
    from_name = Column(String(200))
    subject = Column(String(500))
    body = Column(Text)
    received_at = Column(DateTime(timezone=True))

    # Análisis IA
    ai_summary = Column(Text, nullable=True)          # Resumen del correo
    ai_intent = Column(String(100), nullable=True)    # consulta/presupuesto/envio/otro
    ai_sentiment = Column(String(50), nullable=True)  # positivo/neutro/negativo
    ai_extracted_data = Column(JSON, nullable=True)   # Datos extraídos (nombre, tel, dir)
    ai_suggested_reply = Column(Text, nullable=True)  # Respuesta sugerida por IA

    # Estado
    status = Column(Enum(EmailStatus), default=EmailStatus.unread)
    replied_at = Column(DateTime(timezone=True), nullable=True)
    reply_body = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    client = relationship("Client", back_populates="emails")


# ─────────────────────────────────────────────
# PRESUPUESTOS
# ─────────────────────────────────────────────
class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    email_record_id = Column(Integer, ForeignKey("email_records.id"), nullable=True)

    # Datos del presupuesto
    description = Column(Text)
    amount = Column(Float, nullable=True)
    currency = Column(String(10), default="CLP")
    items = Column(JSON, nullable=True)  # Lista de ítems detallados

    # Estado
    status = Column(Enum(BudgetStatus), default=BudgetStatus.pending)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    responded_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    client = relationship("Client", back_populates="budgets")


# ─────────────────────────────────────────────
# DATOS DE ENVÍO
# ─────────────────────────────────────────────
class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    email_record_id = Column(Integer, ForeignKey("email_records.id"), nullable=True)

    # Datos extraídos por IA del correo
    recipient_name = Column(String(200))
    recipient_email = Column(String(200))
    recipient_phone = Column(String(50), nullable=True)
    recipient_address = Column(Text)
    recipient_city = Column(String(100), nullable=True)
    recipient_region = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)

    # Descripción del envío
    package_description = Column(Text, nullable=True)
    tracking_number = Column(String(200), nullable=True)

    status = Column(Enum(ShipmentStatus), default=ShipmentStatus.pending)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    client = relationship("Client", back_populates="shipments")
