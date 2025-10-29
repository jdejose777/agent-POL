"""
Script para procesar el Código Penal y subir a Pinecone usando Vertex AI
Genera embeddings de 1024 dimensiones con text-embedding-004
"""

import os
import sys
from dotenv import load_dotenv
import vertexai
from vertexai.language_models import TextEmbeddingModel
from pinecone import Pinecone
import PyPDF2
import time
from typing import List

# Cargar variables de entorno
load_dotenv()

# --- CONFIGURACIÓN ---
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "resolute-return-476416-g5")
REGION = os.getenv("GCP_REGION", "us-central1")
EMBEDDING_MODEL = "text-embedding-004"
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = input("Nombre del índice de Pinecone (1024 dims): ").strip()

# Ruta al PDF
PDF_PATH = "../documentos/codigo_penal.pdf"

# Configuración de chunking
CHUNK_SIZE = 800  # Caracteres por chunk
CHUNK_OVERLAP = 100  # Overlap entre chunks

print("="*70)
print("🚀 PROCESADOR DE PDF CON VERTEX AI")
print("="*70)
print(f"📄 PDF: {PDF_PATH}")
print(f"🔢 Modelo embeddings: {EMBEDDING_MODEL} (1024 dims)")
print(f"📊 Índice Pinecone: {PINECONE_INDEX_NAME}")
print(f"⚙️  Chunk size: {CHUNK_SIZE} caracteres")
print("="*70)


def extraer_texto_pdf(pdf_path: str) -> str:
    """Extrae todo el texto del PDF"""
    print("\n📖 Extrayendo texto del PDF...")
    
    texto_completo = ""
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        num_paginas = len(pdf_reader.pages)
        print(f"   Total de páginas: {num_paginas}")
        
        for i, page in enumerate(pdf_reader.pages, 1):
            texto = page.extract_text()
            texto_completo += texto + "\n"
            
            if i % 50 == 0:
                print(f"   ✓ Procesadas {i}/{num_paginas} páginas...")
    
    print(f"✅ Texto extraído: {len(texto_completo)} caracteres")
    return texto_completo


def dividir_en_chunks(texto: str, chunk_size: int, overlap: int) -> List[dict]:
    """Divide el texto en chunks con overlap"""
    print(f"\n✂️  Dividiendo texto en chunks de {chunk_size} caracteres...")
    
    chunks = []
    start = 0
    chunk_id = 0
    
    while start < len(texto):
        end = start + chunk_size
        chunk_text = texto[start:end]
        
        # Intentar cortar en un punto natural (fin de línea o espacio)
        if end < len(texto):
            ultimo_espacio = chunk_text.rfind('\n')
            if ultimo_espacio == -1:
                ultimo_espacio = chunk_text.rfind(' ')
            if ultimo_espacio > chunk_size * 0.7:  # Solo si está en el último 30%
                end = start + ultimo_espacio
                chunk_text = texto[start:end]
        
        if chunk_text.strip():  # Solo agregar chunks no vacíos
            chunks.append({
                "id": f"chunk_{chunk_id}",
                "text": chunk_text.strip()
            })
            chunk_id += 1
        
        start = end - overlap
    
    print(f"✅ Generados {len(chunks)} chunks")
    return chunks


def generar_embeddings_batch(textos: List[str], modelo) -> List[List[float]]:
    """Genera embeddings en batch usando Vertex AI"""
    embeddings_result = modelo.get_embeddings(textos)
    return [emb.values for emb in embeddings_result]


def procesar_y_subir(chunks: List[dict], modelo, pinecone_index):
    """Procesa chunks, genera embeddings y sube a Pinecone"""
    print(f"\n🔢 Generando embeddings y subiendo a Pinecone...")
    print(f"   (Procesando en lotes de 5 chunks)")
    
    BATCH_SIZE = 5
    total_chunks = len(chunks)
    
    for i in range(0, total_chunks, BATCH_SIZE):
        batch = chunks[i:i+BATCH_SIZE]
        batch_textos = [chunk["text"] for chunk in batch]
        
        # Generar embeddings
        try:
            embeddings = generar_embeddings_batch(batch_textos, modelo)
            
            # Preparar vectors para Pinecone
            vectors_to_upsert = []
            for j, chunk in enumerate(batch):
                vectors_to_upsert.append({
                    "id": chunk["id"],
                    "values": embeddings[j],
                    "metadata": {
                        "text": chunk["text"]
                    }
                })
            
            # Subir a Pinecone
            pinecone_index.upsert(vectors=vectors_to_upsert)
            
            print(f"   ✓ Procesados {min(i+BATCH_SIZE, total_chunks)}/{total_chunks} chunks")
            
            # Pequeña pausa para no saturar la API
            time.sleep(0.5)
            
        except Exception as e:
            print(f"   ❌ Error en batch {i//BATCH_SIZE + 1}: {e}")
            continue
    
    print(f"\n✅ ¡Proceso completado!")


def main():
    """Función principal"""
    try:
        # 1. Verificar que el PDF existe
        if not os.path.exists(PDF_PATH):
            print(f"❌ ERROR: No se encuentra el archivo {PDF_PATH}")
            sys.exit(1)
        
        # 2. Inicializar Vertex AI
        print("\n🔧 Inicializando Vertex AI...")
        vertexai.init(project=PROJECT_ID, location=REGION)
        embedding_model = TextEmbeddingModel.from_pretrained(EMBEDDING_MODEL)
        print("✅ Vertex AI inicializado")
        
        # 3. Conectar a Pinecone
        print("\n🔧 Conectando a Pinecone...")
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index = pc.Index(PINECONE_INDEX_NAME)
        
        # Verificar dimensiones del índice
        stats = index.describe_index_stats()
        print(f"✅ Conectado a Pinecone")
        print(f"   Índice: {PINECONE_INDEX_NAME}")
        print(f"   Vectores actuales: {stats.get('total_vector_count', 0)}")
        
        # 4. Extraer texto del PDF
        texto_completo = extraer_texto_pdf(PDF_PATH)
        
        # 5. Dividir en chunks
        chunks = dividir_en_chunks(texto_completo, CHUNK_SIZE, CHUNK_OVERLAP)
        
        # 6. Confirmar antes de proceder
        print(f"\n⚠️  ¿Estás seguro de querer procesar {len(chunks)} chunks?")
        confirmacion = input("   Escribe 'SI' para continuar: ").strip().upper()
        
        if confirmacion != "SI":
            print("❌ Proceso cancelado por el usuario")
            sys.exit(0)
        
        # 7. Procesar y subir
        procesar_y_subir(chunks, embedding_model, index)
        
        # 8. Verificar resultados
        print("\n📊 Verificando resultados...")
        stats_final = index.describe_index_stats()
        print(f"✅ Vectores en el índice: {stats_final.get('total_vector_count', 0)}")
        
        print("\n" + "="*70)
        print("🎉 ¡PROCESO COMPLETADO CON ÉXITO!")
        print("="*70)
        print(f"✅ {len(chunks)} chunks procesados y subidos a Pinecone")
        print(f"✅ Índice: {PINECONE_INDEX_NAME}")
        print(f"✅ Dimensiones: 1024")
        print("\n💡 Ahora actualiza el PINECONE_INDEX_NAME en tu .env")
        
    except Exception as e:
        print(f"\n❌ ERROR FATAL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
