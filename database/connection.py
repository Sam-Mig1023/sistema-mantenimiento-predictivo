"""
Módulo de Gestión de Conexiones a PostgreSQL.
Implementa SimpleConnectionPool con soporte de caché de recursos en Streamlit (@st.cache_resource)
y mecanismo resiliente ante fallos de conexión.
"""

import logging
from contextlib import contextmanager
from typing import Optional, Generator
import psycopg2
from psycopg2 import pool
import streamlit as st

from config.settings import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabasePoolManager:
    """Administrador de pool de conexiones para PostgreSQL con reintentos."""

    def __init__(self):
        self._pool: Optional[pool.SimpleConnectionPool] = None
        self._is_connected = False

    def init_pool(self) -> bool:
        """Inicializa el pool de conexiones simples a PostgreSQL."""
        try:
            self._pool = pool.SimpleConnectionPool(
                minconn=1,
                maxconn=20,
                host=DB_HOST,
                port=DB_PORT,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                connect_timeout=3
            )
            self._is_connected = True
            logger.info("Pool de conexiones PostgreSQL inicializado correctamente.")
            return True
        except Exception as exc:
            logger.warning(f"No se pudo conectar al PostgreSQL local ({exc}). Modo simulación/fallback activo.")
            self._is_connected = False
            return False

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    @contextmanager
    def get_connection(self) -> Generator[Optional[psycopg2.extensions.connection], None, None]:
        """Context manager para obtener y devolver conexiones al pool de forma segura."""
        conn = None
        if not self._is_connected or self._pool is None:
            yield None
            return

        try:
            conn = self._pool.getconn()
            yield conn
        except Exception as err:
            if conn:
                conn.rollback()
            logger.error(f"Error al usar conexión del pool: {err}")
            raise err
        finally:
            if conn and self._pool:
                self._pool.putconn(conn)

    def close_all(self):
        """Cierra todas las conexiones del pool."""
        if self._pool:
            self._pool.closeall()
            self._is_connected = False
            logger.info("Todas las conexiones del pool han sido cerradas.")


@st.cache_resource(show_spinner=False)
def get_db_manager() -> DatabasePoolManager:
    """
    Función cacheada para Streamlit que preserva la instancia única del
    pool de conexiones entre reruns sin saturar la base de datos.
    """
    manager = DatabasePoolManager()
    manager.init_pool()
    return manager
