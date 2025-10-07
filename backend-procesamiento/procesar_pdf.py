"""
Script para procesar archivos PDF y cargarlos en Pinecone para sistemas RAG
Autor: Sistema de procesamiento de documentos
Fecha: 2025
"""

import os
import sys
import argparse
from typing import List, Dict
from dotenv import load_dotenv
import pdfplumber
from langchain.text_splitter import RecursiveCharacterTextSplitter
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec


def cargar_variables_entorno() -> Dict[str, str]:
    """
    Carga las variables de entorno necesarias desde el archivo .env
    
    Returns:
        Dict con las claves de API y configuraciones necesarias
    """
    print("📋 Cargando variables de entorno...")
    load_dotenv()
    
    # Validar que todas las variables necesarias estén presentes
    variables_requeridas = {
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'PINECONE_API_KEY': os.getenv('PINECONE_API_KEY'),
        'PINECONE_ENVIRONMENT': os.getenv('PINECONE_ENVIRONMENT'),
        'PINECONE_INDEX_NAME': os.getenv('PINECONE_INDEX_NAME')
    }
    
    # Verificar que todas las variables estén configuradas
    variables_faltantes = [k for k, v in variables_requeridas.items() if not v]
    if variables_faltantes:
        raise ValueError(f"❌ Variables de entorno faltantes: {', '.join(variables_faltantes)}")
    
    print("✅ Variables de entorno cargadas correctamente")
    return variables_requeridas


def extraer_texto_pdf(ruta_pdf: str) -> str:
    """
    Extrae todo el texto de un archivo PDF usando pdfplumber
    
    Args:
        ruta_pdf: Ruta al archivo PDF a procesar
        
    Returns:
        String con todo el texto extraído del PDF
    """
    print(f"📄 Abriendo archivo PDF: {ruta_pdf}")
    
    if not os.path.exists(ruta_pdf):
        raise FileNotFoundError(f"❌ El archivo no existe: {ruta_pdf}")
    
    texto_completo = ""
    
    try:
        with pdfplumber.open(ruta_pdf) as pdf:
            print(f"📖 Procesando {len(pdf.pages)} páginas...")
            
            for i, pagina in enumerate(pdf.pages, 1):
                texto_pagina = pagina.extract_text()
                if texto_pagina:
                    texto_completo += texto_pagina + "\n"
                
                # Mostrar progreso cada 10 páginas
                if i % 10 == 0:
                    print(f"   Procesadas {i}/{len(pdf.pages)} páginas...")
        
        print(f"✅ Texto extraído correctamente ({len(texto_completo)} caracteres)")
        return texto_completo
    
    except Exception as e:
        raise Exception(f"❌ Error al extraer texto del PDF: {str(e)}")


def dividir_texto_en_chunks(texto: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """
    Divide el texto en fragmentos usando RecursiveCharacterTextSplitter
    
    Args:
        texto: Texto completo a dividir
        chunk_size: Tamaño de cada fragmento en caracteres
        chunk_overlap: Superposición entre fragmentos en caracteres
        
    Returns:
        Lista de fragmentos de texto
    """
    print(f"✂️  Dividiendo texto en chunks (tamaño: {chunk_size}, overlap: {chunk_overlap})...")
    
    try:
        # Inicializar el splitter con los parámetros especificados
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Dividir el texto en chunks
        chunks = text_splitter.split_text(texto)
        
        print(f"✅ Texto dividido en {len(chunks)} fragmentos")
        return chunks
    
    except Exception as e:
        raise Exception(f"❌ Error al dividir el texto: {str(e)}")


def generar_embeddings(chunks: List[str], api_key: str) -> List[List[float]]:
    """
    Genera embeddings para cada fragmento de texto usando OpenAI
    
    Args:
        chunks: Lista de fragmentos de texto
        api_key: Clave de API de OpenAI
        
    Returns:
        Lista de embeddings (vectores)
    """
    print(f"🤖 Generando embeddings para {len(chunks)} fragmentos...")
    
    try:
        # Inicializar cliente de OpenAI
        client = OpenAI(api_key=api_key)
        embeddings = []
        
        # Generar embeddings por lotes para optimizar
        batch_size = 100
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            
            print(f"   Procesando fragmentos {i+1} a {min(i+batch_size, len(chunks))}...")
            
            # Llamar a la API de OpenAI para generar embeddings
            response = client.embeddings.create(
                model="text-embedding-3-small",  # Modelo recomendado por OpenAI
                input=batch
            )
            
            # Extraer los embeddings de la respuesta
            batch_embeddings = [item.embedding for item in response.data]
            embeddings.extend(batch_embeddings)
        
        print(f"✅ Embeddings generados correctamente ({len(embeddings)} vectores)")
        return embeddings
    
    except Exception as e:
        raise Exception(f"❌ Error al generar embeddings: {str(e)}")


def subir_a_pinecone(
    chunks: List[str],
    embeddings: List[List[float]],
    api_key: str,
    environment: str,
    index_name: str,
    nombre_archivo: str
) -> None:
    """
    Sube los fragmentos y sus embeddings a Pinecone
    
    Args:
        chunks: Lista de fragmentos de texto
        embeddings: Lista de embeddings correspondientes
        api_key: Clave de API de Pinecone
        environment: Entorno de Pinecone
        index_name: Nombre del índice en Pinecone
        nombre_archivo: Nombre del archivo PDF original (para metadata)
    """
    print(f"🌲 Conectando con Pinecone (índice: {index_name})...")
    
    try:
        # Inicializar cliente de Pinecone
        pc = Pinecone(api_key=api_key)
        
        # Verificar si el índice existe, si no, crearlo
        indices_existentes = [index.name for index in pc.list_indexes()]
        
        if index_name not in indices_existentes:
            print(f"⚠️  El índice '{index_name}' no existe. Creándolo...")
            pc.create_index(
                name=index_name,
                dimension=len(embeddings[0]),  # Dimensión basada en el modelo de embeddings
                metric='cosine',
                spec=ServerlessSpec(
                    cloud='aws',
                    region=environment
                )
            )
            print(f"✅ Índice '{index_name}' creado correctamente")
        
        # Conectar al índice
        index = pc.Index(index_name)
        
        print(f"📤 Subiendo {len(chunks)} vectores a Pinecone...")
        
        # Preparar los datos para upsert
        vectores_para_subir = []
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            # Crear un ID único para cada vector
            vector_id = f"{nombre_archivo}_chunk_{i}"
            
            # Preparar metadata
            metadata = {
                'text': chunk,
                'source': nombre_archivo,
                'chunk_id': i,
                'total_chunks': len(chunks)
            }
            
            # Agregar a la lista
            vectores_para_subir.append({
                'id': vector_id,
                'values': embedding,
                'metadata': metadata
            })
        
        # Hacer upsert por lotes (Pinecone recomienda lotes de 100)
        batch_size = 100
        for i in range(0, len(vectores_para_subir), batch_size):
            batch = vectores_para_subir[i:i + batch_size]
            index.upsert(vectors=batch)
            
            print(f"   Subidos {min(i+batch_size, len(vectores_para_subir))}/{len(vectores_para_subir)} vectores...")
        
        # Verificar estadísticas del índice
        stats = index.describe_index_stats()
        print(f"✅ Datos subidos correctamente a Pinecone")
        print(f"📊 Total de vectores en el índice: {stats.total_vector_count}")
    
    except Exception as e:
        raise Exception(f"❌ Error al subir datos a Pinecone: {str(e)}")


def main():
    """
    Función principal que orquesta todo el proceso
    """
    print("=" * 60)
    print("🚀 PROCESADOR DE PDFs PARA SISTEMA RAG")
    print("=" * 60)
    print()
    
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(
        description='Procesa un archivo PDF y lo carga en Pinecone para RAG'
    )
    parser.add_argument(
        'pdf_path',
        type=str,
        help='Ruta al archivo PDF a procesar'
    )
    parser.add_argument(
        '--chunk-size',
        type=int,
        default=1000,
        help='Tamaño de cada fragmento en caracteres (default: 1000)'
    )
    parser.add_argument(
        '--chunk-overlap',
        type=int,
        default=200,
        help='Superposición entre fragmentos en caracteres (default: 200)'
    )
    
    args = parser.parse_args()
    
    try:
        # Paso 1: Cargar variables de entorno
        variables = cargar_variables_entorno()
        print()
        
        # Paso 2: Extraer texto del PDF
        texto = extraer_texto_pdf(args.pdf_path)
        print()
        
        # Validar que se extrajo texto
        if not texto.strip():
            raise ValueError("❌ No se pudo extraer texto del PDF. El archivo puede estar vacío o corrupto.")
        
        # Paso 3: Dividir texto en chunks
        chunks = dividir_texto_en_chunks(texto, args.chunk_size, args.chunk_overlap)
        print()
        
        # Paso 4: Generar embeddings
        embeddings = generar_embeddings(chunks, variables['OPENAI_API_KEY'])
        print()
        
        # Paso 5 y 6: Conectar y subir a Pinecone
        nombre_archivo = os.path.basename(args.pdf_path)
        subir_a_pinecone(
            chunks=chunks,
            embeddings=embeddings,
            api_key=variables['PINECONE_API_KEY'],
            environment=variables['PINECONE_ENVIRONMENT'],
            index_name=variables['PINECONE_INDEX_NAME'],
            nombre_archivo=nombre_archivo
        )
        print()
        
        # Resumen final
        print("=" * 60)
        print("✨ PROCESO COMPLETADO EXITOSAMENTE")
        print("=" * 60)
        print(f"📄 Archivo procesado: {nombre_archivo}")
        print(f"📊 Total de fragmentos: {len(chunks)}")
        print(f"🤖 Embeddings generados: {len(embeddings)}")
        print(f"🌲 Índice Pinecone: {variables['PINECONE_INDEX_NAME']}")
        print("=" * 60)
    
    except FileNotFoundError as e:
        print(f"\n❌ ERROR: {str(e)}")
        sys.exit(1)
    
    except ValueError as e:
        print(f"\n❌ ERROR: {str(e)}")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ ERROR INESPERADO: {str(e)}")
        print("Por favor, verifica tu configuración y vuelve a intentarlo.")
        sys.exit(1)


if __name__ == "__main__":
    main()
