"""
📝 CRUD OPERATIONS - PostgreSQL
Funciones para crear, leer, actualizar y eliminar registros
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid

from models import Conversation, Message, User, Analytics, ArticleQuery


# ====================================================================
# CONVERSATIONS
# ====================================================================

def create_conversation(
    db: Session,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    user_ip: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Conversation:
    """
    Crear una nueva conversación
    """
    if not session_id:
        session_id = str(uuid.uuid4())
    
    conversation = Conversation(
        session_id=session_id,
        user_id=user_id,
        user_ip=user_ip,
        user_agent=user_agent,
        started_at=datetime.utcnow(),
        last_message_at=datetime.utcnow(),
        is_active=True
    )
    
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    
    return conversation


def get_conversation(db: Session, conversation_id: int) -> Optional[Conversation]:
    """
    Obtener una conversación por ID
    """
    return db.query(Conversation).filter(Conversation.id == conversation_id).first()


def get_conversation_by_session(db: Session, session_id: str) -> Optional[Conversation]:
    """
    Obtener una conversación por session_id
    """
    return db.query(Conversation).filter(Conversation.session_id == session_id).first()


def get_or_create_conversation(
    db: Session,
    session_id: str,
    user_id: Optional[str] = None,
    user_ip: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Conversation:
    """
    Obtener conversación existente o crear una nueva
    """
    conversation = get_conversation_by_session(db, session_id)
    
    if not conversation:
        conversation = create_conversation(db, session_id, user_id, user_ip, user_agent)
    
    return conversation


def get_conversations(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[str] = None,
    is_active: Optional[bool] = None
) -> List[Conversation]:
    """
    Obtener lista de conversaciones con filtros
    """
    query = db.query(Conversation)
    
    if user_id:
        query = query.filter(Conversation.user_id == user_id)
    
    if is_active is not None:
        query = query.filter(Conversation.is_active == is_active)
    
    return query.order_by(desc(Conversation.started_at)).offset(skip).limit(limit).all()


def update_conversation_stats(db: Session, conversation_id: int) -> bool:
    """
    Actualizar estadísticas de una conversación
    """
    conversation = get_conversation(db, conversation_id)
    if not conversation:
        return False
    
    # Contar mensajes
    message_count = db.query(Message).filter(Message.conversation_id == conversation_id).count()
    
    # Sumar tokens
    total_tokens = db.query(func.sum(Message.tokens)).filter(
        Message.conversation_id == conversation_id
    ).scalar() or 0
    
    # Actualizar
    conversation.total_messages = message_count
    conversation.total_tokens = int(total_tokens)
    conversation.last_message_at = datetime.utcnow()
    
    db.commit()
    return True


def end_conversation(db: Session, conversation_id: int) -> bool:
    """
    Marcar conversación como terminada
    """
    conversation = get_conversation(db, conversation_id)
    if not conversation:
        return False
    
    conversation.is_active = False
    conversation.ended_at = datetime.utcnow()
    
    db.commit()
    return True


# ====================================================================
# MESSAGES
# ====================================================================

def create_message(
    db: Session,
    conversation_id: int,
    role: str,
    content: str,
    tokens: Optional[int] = None,
    response_time_ms: Optional[float] = None,
    extra_data: Optional[Dict[str, Any]] = None
) -> Message:
    """
    Crear un nuevo mensaje
    """
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        tokens=tokens,
        response_time_ms=response_time_ms,
        extra_data=extra_data,
        created_at=datetime.utcnow()
    )
    
    db.add(message)
    db.commit()
    db.refresh(message)
    
    # Actualizar stats de la conversación
    update_conversation_stats(db, conversation_id)
    
    return message


def get_messages(
    db: Session,
    conversation_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[Message]:
    """
    Obtener mensajes de una conversación
    """
    return db.query(Message)\
        .filter(Message.conversation_id == conversation_id)\
        .order_by(Message.created_at)\
        .offset(skip)\
        .limit(limit)\
        .all()


def get_conversation_with_messages(db: Session, conversation_id: int) -> Optional[Dict]:
    """
    Obtener conversación completa con todos sus mensajes
    """
    conversation = get_conversation(db, conversation_id)
    if not conversation:
        return None
    
    messages = get_messages(db, conversation_id, limit=1000)
    
    return {
        "conversation": {
            "id": conversation.id,
            "session_id": conversation.session_id,
            "user_id": conversation.user_id,
            "started_at": conversation.started_at.isoformat(),
            "last_message_at": conversation.last_message_at.isoformat(),
            "ended_at": conversation.ended_at.isoformat() if conversation.ended_at else None,
            "total_messages": conversation.total_messages,
            "total_tokens": conversation.total_tokens,
            "is_active": conversation.is_active
        },
        "messages": [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat(),
                "tokens": msg.tokens,
                "response_time_ms": msg.response_time_ms,
                "extra_data": msg.extra_data
            }
            for msg in messages
        ]
    }


# ====================================================================
# USERS
# ====================================================================

def create_user(
    db: Session,
    user_id: str,
    username: Optional[str] = None,
    email: Optional[str] = None
) -> User:
    """
    Crear un nuevo usuario
    """
    user = User(
        user_id=user_id,
        username=username,
        email=email,
        created_at=datetime.utcnow(),
        last_seen=datetime.utcnow()
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


def get_user(db: Session, user_id: str) -> Optional[User]:
    """
    Obtener usuario por user_id
    """
    return db.query(User).filter(User.user_id == user_id).first()


def update_user_stats(db: Session, user_id: str) -> bool:
    """
    Actualizar estadísticas de usuario
    """
    user = get_user(db, user_id)
    if not user:
        return False
    
    # Contar conversaciones
    conversation_count = db.query(Conversation).filter(Conversation.user_id == user_id).count()
    
    # Contar mensajes
    message_count = db.query(Message).join(Conversation).filter(
        Conversation.user_id == user_id
    ).count()
    
    user.total_conversations = conversation_count
    user.total_messages = message_count
    user.last_seen = datetime.utcnow()
    
    db.commit()
    return True


# ====================================================================
# ARTICLE QUERIES
# ====================================================================

def log_article_query(
    db: Session,
    article_number: str,
    conversation_id: Optional[int] = None,
    search_type: Optional[str] = None,
    search_query: Optional[str] = None,
    found: bool = False,
    source: Optional[str] = None,
    response_time_ms: Optional[float] = None
) -> ArticleQuery:
    """
    Registrar consulta de artículo
    """
    article_query = ArticleQuery(
        article_number=article_number,
        conversation_id=conversation_id,
        search_type=search_type,
        search_query=search_query,
        found=found,
        source=source,
        response_time_ms=response_time_ms,
        query_timestamp=datetime.utcnow()
    )
    
    db.add(article_query)
    db.commit()
    db.refresh(article_query)
    
    return article_query


def get_most_queried_articles(db: Session, limit: int = 10, days: int = 30) -> List[Dict]:
    """
    Obtener artículos más consultados
    """
    since = datetime.utcnow() - timedelta(days=days)
    
    results = db.query(
        ArticleQuery.article_number,
        func.count(ArticleQuery.id).label('count')
    ).filter(
        ArticleQuery.query_timestamp >= since
    ).group_by(
        ArticleQuery.article_number
    ).order_by(
        desc('count')
    ).limit(limit).all()
    
    return [{"article": article, "queries": count} for article, count in results]


# ====================================================================
# ANALYTICS
# ====================================================================

def get_daily_analytics(db: Session, days: int = 7) -> List[Dict]:
    """
    Obtener analytics de los últimos N días
    """
    since = datetime.utcnow() - timedelta(days=days)
    
    # Agrupar por día
    results = db.query(
        func.date(Conversation.started_at).label('date'),
        func.count(Conversation.id).label('conversations'),
        func.count(Message.id).label('messages')
    ).join(
        Message, Message.conversation_id == Conversation.id, isouter=True
    ).filter(
        Conversation.started_at >= since
    ).group_by(
        func.date(Conversation.started_at)
    ).order_by(
        func.date(Conversation.started_at)
    ).all()
    
    return [
        {
            "date": str(date),
            "conversations": conversations or 0,
            "messages": messages or 0
        }
        for date, conversations, messages in results
    ]


def get_global_stats(db: Session) -> Dict:
    """
    Obtener estadísticas globales
    """
    total_conversations = db.query(Conversation).count()
    active_conversations = db.query(Conversation).filter(Conversation.is_active == True).count()
    total_messages = db.query(Message).count()
    total_users = db.query(User).count()
    total_article_queries = db.query(ArticleQuery).count()
    
    # Promedio de mensajes por conversación
    avg_messages = db.query(func.avg(Conversation.total_messages)).scalar() or 0
    
    # Promedio de tiempo de respuesta
    avg_response_time = db.query(func.avg(Message.response_time_ms)).scalar() or 0
    
    return {
        "total_conversations": total_conversations,
        "active_conversations": active_conversations,
        "total_messages": total_messages,
        "total_users": total_users,
        "total_article_queries": total_article_queries,
        "avg_messages_per_conversation": round(avg_messages, 2),
        "avg_response_time_ms": round(avg_response_time, 2)
    }
