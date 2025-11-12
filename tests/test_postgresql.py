"""
🧪 TESTS PARA POSTGRESQL
Tests unitarios para modelos, CRUD operations y endpoints
"""
import sys
sys.path.insert(0, '../backend-api')

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from models import Base, Conversation, Message, User, ArticleQuery
from crud import (
    create_conversation, get_conversation, get_or_create_conversation,
    create_message, get_messages, get_conversation_with_messages,
    create_user, get_user, update_user_stats,
    log_article_query, get_most_queried_articles,
    get_global_stats
)

# ====================================================================
# CONFIGURACIÓN DE TESTS
# ====================================================================

# Base de datos en memoria para tests
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db_session():
    """
    Fixture que crea una sesión de base de datos temporal para cada test
    """
    # Crear engine en memoria
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    
    # Crear todas las tablas
    Base.metadata.create_all(bind=engine)
    
    # Crear sesión
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    yield session
    
    # Cleanup
    session.close()
    Base.metadata.drop_all(bind=engine)


# ====================================================================
# TESTS DE MODELOS
# ====================================================================

def test_conversation_model(db_session):
    """Test 1: Crear conversación en la base de datos"""
    conversation = Conversation(
        session_id="test-session-123",
        user_id="user-456",
        user_ip="192.168.1.1",
        started_at=datetime.utcnow(),
        is_active=True
    )
    
    db_session.add(conversation)
    db_session.commit()
    db_session.refresh(conversation)
    
    assert conversation.id is not None
    assert conversation.session_id == "test-session-123"
    assert conversation.is_active is True
    print("✅ Test 1: Modelo Conversation OK")


def test_message_model(db_session):
    """Test 2: Crear mensaje asociado a conversación"""
    # Crear conversación primero
    conversation = Conversation(session_id="test-session-msg", is_active=True)
    db_session.add(conversation)
    db_session.commit()
    db_session.refresh(conversation)
    
    # Crear mensaje
    message = Message(
        conversation_id=conversation.id,
        role="user",
        content="¿Qué es el homicidio?",
        tokens=10,
        created_at=datetime.utcnow()
    )
    
    db_session.add(message)
    db_session.commit()
    db_session.refresh(message)
    
    assert message.id is not None
    assert message.conversation_id == conversation.id
    assert message.role == "user"
    assert message.content == "¿Qué es el homicidio?"
    print("✅ Test 2: Modelo Message OK")


def test_user_model(db_session):
    """Test 3: Crear usuario en la base de datos"""
    user = User(
        user_id="user-789",
        username="test_user",
        email="test@example.com",
        created_at=datetime.utcnow(),
        is_active=True
    )
    
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    assert user.id is not None
    assert user.user_id == "user-789"
    assert user.email == "test@example.com"
    print("✅ Test 3: Modelo User OK")


# ====================================================================
# TESTS DE CRUD - CONVERSACIONES
# ====================================================================

def test_create_conversation_crud(db_session):
    """Test 4: Crear conversación con función CRUD"""
    conversation = create_conversation(
        db=db_session,
        session_id="crud-session-001",
        user_id="user-001",
        user_ip="10.0.0.1"
    )
    
    assert conversation.id is not None
    assert conversation.session_id == "crud-session-001"
    assert conversation.user_id == "user-001"
    print("✅ Test 4: create_conversation() OK")


def test_get_conversation_crud(db_session):
    """Test 5: Obtener conversación por ID"""
    # Crear conversación
    conv = create_conversation(db=db_session, session_id="get-session-001")
    
    # Obtener conversación
    retrieved = get_conversation(db=db_session, conversation_id=conv.id)
    
    assert retrieved is not None
    assert retrieved.id == conv.id
    assert retrieved.session_id == "get-session-001"
    print("✅ Test 5: get_conversation() OK")


def test_get_or_create_conversation(db_session):
    """Test 6: Obtener o crear conversación (idempotencia)"""
    session_id = "idempotent-session"
    
    # Primera llamada: crea
    conv1 = get_or_create_conversation(db=db_session, session_id=session_id)
    
    # Segunda llamada: obtiene la misma
    conv2 = get_or_create_conversation(db=db_session, session_id=session_id)
    
    assert conv1.id == conv2.id
    assert conv1.session_id == conv2.session_id
    print("✅ Test 6: get_or_create_conversation() OK")


# ====================================================================
# TESTS DE CRUD - MENSAJES
# ====================================================================

def test_create_message_crud(db_session):
    """Test 7: Crear mensaje con función CRUD"""
    # Crear conversación
    conv = create_conversation(db=db_session, session_id="msg-session")
    
    # Crear mensaje
    message = create_message(
        db=db_session,
        conversation_id=conv.id,
        role="user",
        content="Test message",
        tokens=5,
        response_time_ms=100.0
    )
    
    assert message.id is not None
    assert message.conversation_id == conv.id
    assert message.role == "user"
    assert message.tokens == 5
    print("✅ Test 7: create_message() OK")


def test_get_messages_crud(db_session):
    """Test 8: Obtener mensajes de una conversación"""
    # Crear conversación
    conv = create_conversation(db=db_session, session_id="multi-msg")
    
    # Crear múltiples mensajes
    create_message(db=db_session, conversation_id=conv.id, role="user", content="Msg 1")
    create_message(db=db_session, conversation_id=conv.id, role="assistant", content="Msg 2")
    create_message(db=db_session, conversation_id=conv.id, role="user", content="Msg 3")
    
    # Obtener mensajes
    messages = get_messages(db=db_session, conversation_id=conv.id)
    
    assert len(messages) == 3
    assert messages[0].content == "Msg 1"
    assert messages[1].role == "assistant"
    print("✅ Test 8: get_messages() OK")


def test_conversation_with_messages(db_session):
    """Test 9: Obtener conversación completa con mensajes"""
    # Crear conversación
    conv = create_conversation(db=db_session, session_id="full-conv")
    
    # Crear mensajes
    create_message(db=db_session, conversation_id=conv.id, role="user", content="Question")
    create_message(db=db_session, conversation_id=conv.id, role="assistant", content="Answer")
    
    # Obtener conversación completa
    full_conv = get_conversation_with_messages(db=db_session, conversation_id=conv.id)
    
    assert full_conv is not None
    assert full_conv["conversation"]["session_id"] == "full-conv"
    assert len(full_conv["messages"]) == 2
    assert full_conv["messages"][0]["role"] == "user"
    print("✅ Test 9: get_conversation_with_messages() OK")


# ====================================================================
# TESTS DE CRUD - USUARIOS
# ====================================================================

def test_create_user_crud(db_session):
    """Test 10: Crear usuario con función CRUD"""
    user = create_user(
        db=db_session,
        user_id="crud-user-001",
        username="test_user",
        email="crud@test.com"
    )
    
    assert user.id is not None
    assert user.user_id == "crud-user-001"
    assert user.email == "crud@test.com"
    print("✅ Test 10: create_user() OK")


def test_get_user_crud(db_session):
    """Test 11: Obtener usuario por user_id"""
    # Crear usuario
    create_user(db=db_session, user_id="get-user-001", username="testuser")
    
    # Obtener usuario
    user = get_user(db=db_session, user_id="get-user-001")
    
    assert user is not None
    assert user.user_id == "get-user-001"
    print("✅ Test 11: get_user() OK")


def test_update_user_stats(db_session):
    """Test 12: Actualizar estadísticas de usuario"""
    # Crear usuario
    user = create_user(db=db_session, user_id="stats-user", username="statsuser")
    
    # Crear conversaciones para el usuario
    conv1 = create_conversation(db=db_session, session_id="s1", user_id="stats-user")
    conv2 = create_conversation(db=db_session, session_id="s2", user_id="stats-user")
    
    # Crear mensajes
    create_message(db=db_session, conversation_id=conv1.id, role="user", content="M1")
    create_message(db=db_session, conversation_id=conv1.id, role="assistant", content="M2")
    create_message(db=db_session, conversation_id=conv2.id, role="user", content="M3")
    
    # Actualizar stats
    success = update_user_stats(db=db_session, user_id="stats-user")
    
    # Verificar
    user = get_user(db=db_session, user_id="stats-user")
    
    assert success is True
    assert user.total_conversations == 2
    assert user.total_messages == 3
    print("✅ Test 12: update_user_stats() OK")


# ====================================================================
# TESTS DE CRUD - ARTICLE QUERIES
# ====================================================================

def test_log_article_query(db_session):
    """Test 13: Registrar consulta de artículo"""
    # Crear conversación
    conv = create_conversation(db=db_session, session_id="art-query")
    
    # Registrar consulta
    query = log_article_query(
        db=db_session,
        article_number="138",
        conversation_id=conv.id,
        search_type="exact",
        search_query="artículo 138",
        found=True,
        source="redis",
        response_time_ms=2.5
    )
    
    assert query.id is not None
    assert query.article_number == "138"
    assert query.found is True
    assert query.source == "redis"
    print("✅ Test 13: log_article_query() OK")


def test_most_queried_articles(db_session):
    """Test 14: Obtener artículos más consultados"""
    # Crear múltiples consultas
    log_article_query(db=db_session, article_number="138", found=True)
    log_article_query(db=db_session, article_number="138", found=True)
    log_article_query(db=db_session, article_number="142", found=True)
    log_article_query(db=db_session, article_number="138", found=True)
    
    # Obtener top articles
    top_articles = get_most_queried_articles(db=db_session, limit=5, days=30)
    
    assert len(top_articles) > 0
    assert top_articles[0]["article"] == "138"
    assert top_articles[0]["queries"] == 3
    print("✅ Test 14: get_most_queried_articles() OK")


# ====================================================================
# TESTS DE ANALYTICS
# ====================================================================

def test_global_stats(db_session):
    """Test 15: Obtener estadísticas globales"""
    # Crear datos
    conv1 = create_conversation(db=db_session, session_id="stats-1")
    conv2 = create_conversation(db=db_session, session_id="stats-2")
    
    create_message(db=db_session, conversation_id=conv1.id, role="user", content="Q1", tokens=10)
    create_message(db=db_session, conversation_id=conv1.id, role="assistant", content="A1", tokens=50, response_time_ms=100.0)
    create_message(db=db_session, conversation_id=conv2.id, role="user", content="Q2", tokens=15)
    
    # Obtener stats
    stats = get_global_stats(db=db_session)
    
    assert stats["total_conversations"] == 2
    assert stats["total_messages"] == 3
    assert stats["avg_response_time_ms"] == 100.0
    print("✅ Test 15: get_global_stats() OK")


# ====================================================================
# EJECUTAR TESTS
# ====================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 EJECUTANDO TESTS DE POSTGRESQL")
    print("="*60)
    
    # Ejecutar con pytest
    pytest.main([__file__, "-v", "-s"])
