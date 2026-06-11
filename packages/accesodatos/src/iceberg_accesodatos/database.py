"""Engine y sesión de base de datos.

El engine se crea de forma *lazy* (perezosa): no hay conexión a la base de datos
en tiempo de import, para que el grafo de módulos sea importable sin efectos
colaterales (lo necesita import-linter y los tests).
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import Engine, event
from sqlmodel import Session, SQLModel, create_engine

from iceberg_accesodatos.config import get_settings

_engine: Engine | None = None


def _set_sqlite_pragma(dbapi_connection, _connection_record) -> None:
    """Activa la integridad referencial (ON DELETE CASCADE) en SQLite."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def get_engine() -> Engine:
    """Devuelve el engine singleton, creándolo en el primer uso."""
    global _engine
    if _engine is None:
        settings = get_settings()
        url = settings.normalized_database_url
        connect_args: dict = {}
        if url.startswith("sqlite"):
            # check_same_thread=False permite compartir la conexión entre hilos
            # (TestClient / Uvicorn workers).
            connect_args["check_same_thread"] = False
        engine = create_engine(url, connect_args=connect_args)
        if url.startswith("sqlite"):
            event.listen(engine, "connect", _set_sqlite_pragma)
        _engine = engine
    return _engine


def create_db_and_tables() -> None:
    """Crea las tablas declaradas en ``SQLModel.metadata``.

    Asume que los modelos de ``iceberg_entities`` ya fueron importados (lo hace
    la cadena api -> negocio -> repositorio -> entities al arrancar la app).
    """
    engine = get_engine()
    SQLModel.metadata.create_all(engine)
    _apply_light_migrations(engine)


def _apply_light_migrations(engine: Engine) -> None:
    """Migraciones aditivas mínimas (sin Alembic): agrega columnas nuevas si faltan."""
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    columns = {c["name"] for c in inspector.get_columns("levels")}
    if "music_url" not in columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE levels ADD COLUMN music_url VARCHAR"))


def get_session() -> Generator[Session, None, None]:
    """Generador de sesión (uso como dependencia / context manager)."""
    with Session(get_engine()) as session:
        yield session


def reset_engine() -> None:
    """Descarta el engine cacheado (útil en tests al cambiar DATABASE_URL)."""
    global _engine
    if _engine is not None:
        _engine.dispose()
    _engine = None
