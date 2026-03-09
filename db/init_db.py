"""
Inicializa la base de datos creando todas las tablas.
Ejecutar una sola vez: python -m db.init_db
"""
from loguru import logger
from .database import engine, Base
from .models import Client, EmailRecord, Budget, Shipment  # noqa: importa modelos


def init_db():
    logger.info("Creando tablas en la base de datos...")
    Base.metadata.create_all(bind=engine)
    logger.success("✅ Tablas creadas exitosamente.")


if __name__ == "__main__":
    init_db()
