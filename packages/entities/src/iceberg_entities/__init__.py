"""Modelos SQLModel de Iceberg Web.

Importar este paquete registra las cinco tablas en ``SQLModel.metadata``
(necesario para ``create_all``). Orden: la cadena Iceberg -> Level -> Entry -> Media,
más User como dueño.
"""

from iceberg_entities.entry import Entry
from iceberg_entities.iceberg import Iceberg
from iceberg_entities.level import Level
from iceberg_entities.media import Media
from iceberg_entities.user import User

__all__ = ["User", "Iceberg", "Level", "Entry", "Media"]
