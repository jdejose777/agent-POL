"""
🗄️ MODELOS DE BASE DE DATOS - PostgreSQL
Modelos SQLAlchemy para el historial de conversaciones
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Conversation(Base):
    """
    Tabla de conversaciones
    Almacena información de cada sesión de chat
    """
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    user_id = Column(String(100), index=True, nullable=True)  # Opcional: identificador de usuario
    user_ip = Column(String(50), nullable=True)
    user_agent = Column(String(255), nullable=True)
    
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_message_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    
    total_messages = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # Relación con mensajes
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, session_id={self.session_id}, messages={self.total_messages})>"


class Message(Base):
    """
    Tabla de mensajes
    Almacena cada mensaje enviado y recibido
    """
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    
    role = Column(String(20), nullable=False)  # "user" o "assistant"
    content = Column(Text, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Metadata del mensaje
    tokens = Column(Integer, nullable=True)
    response_time_ms = Column(Float, nullable=True)
    
    # Información adicional (JSON) - Renombrado de 'metadata' a 'extra_data' para evitar conflicto con SQLAlchemy
    extra_data = Column(JSON, nullable=True)  # Artículos citados, fuentes, etc.
    
    # Relación con conversación
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self):
        preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"<Message(id={self.id}, role={self.role}, content='{preview}')>"


class User(Base):
    """
    Tabla de usuarios (opcional)
    Almacena información de usuarios registrados
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(100), unique=True, index=True, nullable=False)
    username = Column(String(100), nullable=True)
    email = Column(String(255), unique=True, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_seen = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    total_conversations = Column(Integer, default=0)
    total_messages = Column(Integer, default=0)
    
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<User(id={self.id}, user_id={self.user_id}, conversations={self.total_conversations})>"


class Analytics(Base):
    """
    Tabla de analytics (opcional)
    Almacena métricas agregadas por día/hora
    """
    __tablename__ = "analytics"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    date = Column(DateTime, nullable=False, index=True)
    
    # Métricas
    total_conversations = Column(Integer, default=0)
    total_messages = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    
    avg_response_time_ms = Column(Float, nullable=True)
    unique_users = Column(Integer, default=0)
    
    # Artículos más consultados (JSON)
    top_articles = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<Analytics(date={self.date}, conversations={self.total_conversations}, messages={self.total_messages})>"


class ArticleQuery(Base):
    """
    Tabla de consultas de artículos
    Almacena qué artículos son más consultados
    """
    __tablename__ = "article_queries"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    article_number = Column(String(20), nullable=False, index=True)
    
    query_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True)
    
    # Tipo de búsqueda
    search_type = Column(String(50), nullable=True)  # "exact", "semantic", "regex"
    search_query = Column(Text, nullable=True)  # Consulta original del usuario
    
    # Resultados
    found = Column(Boolean, default=False)
    source = Column(String(50), nullable=True)  # "redis", "memory", "pinecone", "pdf"
    response_time_ms = Column(Float, nullable=True)
    
    def __repr__(self):
        return f"<ArticleQuery(article={self.article_number}, found={self.found}, source={self.source})>"
