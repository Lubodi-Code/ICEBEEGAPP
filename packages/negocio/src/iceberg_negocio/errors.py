"""Excepciones de dominio (puras, sin dependencia de FastAPI/HTTP)."""

from __future__ import annotations


class DomainError(Exception):
    """Base de los errores de dominio."""


class NotFoundError(DomainError):
    """El recurso solicitado no existe."""


class ValidationError(DomainError):
    """Los datos de entrada no son válidos según las reglas de negocio."""
