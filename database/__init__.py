"""Database connection and setup utilities."""

from .connection import (
    get_client,
    get_database,
    get_collection,
    test_connection,
    close_connection,
    HEALTH_LOGS_COLLECTION,
    HEALTH_ADVICE_COLLECTION,
)
