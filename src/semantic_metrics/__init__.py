"""Synthetic semantic-metric governance reference implementation."""

from .catalog import Catalog
from .compiler import QueryRequest, SqlCompiler
from .validator import ContractValidationError, validate_catalog

__all__ = [
    "Catalog",
    "ContractValidationError",
    "QueryRequest",
    "SqlCompiler",
    "validate_catalog",
]

__version__ = "0.1.0"

