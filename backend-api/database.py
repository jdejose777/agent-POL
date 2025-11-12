"""
🔧 CONFIGURACIÓN DE BASE DE DATOS - PostgreSQL
Setup de SQLAlchemy y gestión de sesiones
"""
import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from typing import Generator
import logging

from models import Base

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ====================================================================
# CONFIGURACIÓN DE POSTGRESQL
# ====================================================================

# Variables de entorno con valores por defecto
POSTGRES_USER = os.getenv("POSTGRES_USER", "agentpol")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "agentpol2025")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "conversations_db")

# Construcción de URL de conexión
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# ====================================================================
# ENGINE Y SESIÓN
# ====================================================================

try:
    # Crear engine con configuración optimizada
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Verificar conexión antes de usarla
        pool_recycle=3600,   # Reciclar conexiones cada hora
        pool_size=10,        # Tamaño del pool
        max_overflow=20,     # Conexiones extra permitidas
        echo=False,          # No mostrar SQL queries (cambiar a True para debug)
    )
    
    # Crear todas las tablas
    Base.metadata.create_all(bind=engine)
    
    # Session factory
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    logger.info(f"✅ PostgreSQL conectado - {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")
    
    # Variable para indicar que la BD está disponible
    DB_AVAILABLE = True
    
except Exception as e:
    logger.error(f"❌ Error conectando a PostgreSQL: {e}")
    logger.warning("⚠️ La aplicación continuará SIN persistencia en base de datos")
    
    # Crear engine dummy para que no falle la app
    engine = None
    SessionLocal = None
    DB_AVAILABLE = False


# ====================================================================
# DEPENDENCY INJECTION PARA FASTAPI
# ====================================================================

def get_db() -> Generator[Session, None, None]:
    """
    Dependency para obtener sesión de base de datos
    Uso en FastAPI:
        @app.get("/conversations")
        def get_conversations(db: Session = Depends(get_db)):
            ...
    """
    if not DB_AVAILABLE or SessionLocal is None:
        raise RuntimeError("Base de datos no disponible")
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ====================================================================
# FUNCIONES HELPER
# ====================================================================

def get_db_session() -> Session | None:
    """
    Obtener sesión de BD (sin dependency injection)
    Retorna None si la BD no está disponible
    """
    if not DB_AVAILABLE or SessionLocal is None:
        return None
    return SessionLocal()


def check_db_connection() -> dict:
    """
    Verificar conexión a la base de datos
    Retorna información de estado
    """
    if not DB_AVAILABLE:
        return {
            "status": "unavailable",
            "connected": False,
            "error": "PostgreSQL no está conectado"
        }
    
    try:
        from sqlalchemy import text
        db = SessionLocal()
        # Ejecutar query simple
        db.execute(text("SELECT 1"))
        db.close()
        
        return {
            "status": "connected",
            "connected": True,
            "database": POSTGRES_DB,
            "host": POSTGRES_HOST,
            "port": POSTGRES_PORT
        }
    except Exception as e:
        return {
            "status": "error",
            "connected": False,
            "error": str(e)
        }


def get_db_stats() -> dict:
    """
    Obtener estadísticas de la base de datos
    """
    if not DB_AVAILABLE:
        return {"available": False}
    
    try:
        from models import Conversation, Message, User, ArticleQuery
        
        db = SessionLocal()
        
        stats = {
            "available": True,
            "total_conversations": db.query(Conversation).count(),
            "active_conversations": db.query(Conversation).filter(Conversation.is_active == True).count(),
            "total_messages": db.query(Message).count(),
            "total_users": db.query(User).count() if db.query(User).count() else 0,
            "total_article_queries": db.query(ArticleQuery).count(),
        }
        
        db.close()
        return stats
        
    except Exception as e:
        logger.error(f"Error obteniendo stats: {e}")
        return {"available": True, "error": str(e)}


def reset_database():
    """
    ⚠️ CUIDADO: Eliminar todas las tablas y recrearlas
    Solo usar en desarrollo
    """
    if not DB_AVAILABLE or engine is None:
        logger.error("Base de datos no disponible")
        return False
    
    try:
        logger.warning("🗑️ ELIMINANDO todas las tablas...")
        Base.metadata.drop_all(bind=engine)
        
        logger.info("📊 Recreando tablas...")
        Base.metadata.create_all(bind=engine)
        
        logger.info("✅ Base de datos reseteada")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error reseteando base de datos: {e}")
        return False


# ====================================================================
# EVENTOS
# ====================================================================

if DB_AVAILABLE and engine:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        """Evento al conectar (útil para configuraciones adicionales)"""
        pass
