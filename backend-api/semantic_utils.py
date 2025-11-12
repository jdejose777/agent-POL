"""
MÓDULO DE UTILIDADES PARA EXPANSIÓN SEMÁNTICA
Contiene solo las funciones y datos necesarios para expansión de queries
"""

# --- DICCIONARIO DE SINÓNIMOS LEGALES ---
# 🔍 MEJORA #7: Expansión semántica para consultas coloquiales
SINONIMOS_LEGALES = {
    # Delitos contra las personas
    "matar": ["homicidio", "asesinato", "muerte", "fallecimiento", "privación de vida"],
    "robar": ["robo", "hurto", "apropiación", "sustracción", "apoderamiento"],
    "pegar": ["lesiones", "agresión", "golpes", "violencia física", "maltrato"],
    "violar": ["violación", "agresión sexual", "abuso sexual", "delito sexual"],
    "secuestrar": ["secuestro", "detención ilegal", "privación de libertad"],
    "estafar": ["estafa", "fraude", "engaño", "timo", "defraudación"],
    "amenazar": ["amenazas", "coacción", "intimidación"],
    "insultar": ["injurias", "calumnias", "difamación", "ofensas"],
    
    # Delitos contra la propiedad
    "coger": ["apropiación", "sustracción", "tomar", "apoderamiento"],
    "entrar": ["allanamiento", "escalamiento", "entrada ilegal"],
    "quemar": ["incendio", "daños por fuego", "piromanía"],
    "romper": ["daños", "destrucción", "deterioro"],
    
    # Términos coloquiales
    "chocar": ["accidente", "colisión", "atropello", "siniestro vial"],
    "atropellar": ["atropello", "lesiones por vehículo", "homicidio imprudente vehículo"],
    "empujar": ["lesiones", "agresión", "violencia"],
    "drogas": ["estupefacientes", "sustancias prohibidas", "tráfico de drogas"],
    "arma": ["armas", "instrumento peligroso", "medio violento"],
    
    # Circunstancias
    "borracho": ["embriaguez", "estado de ebriedad", "bajo efectos alcohol"],
    "sin querer": ["imprudencia", "negligencia", "culpa", "imprudente"],
    "adrede": ["dolo", "intención", "premeditación", "doloso"],
    "niño": ["menor", "menor de edad", "víctima menor"],
    "casa": ["domicilio", "morada", "vivienda"],
    "noche": ["nocturnidad", "horas nocturnas"],
    
    # Resultados
    "herida": ["lesión", "daño corporal", "menoscabo físico"],
    "muerte": ["fallecimiento", "homicidio", "defunción", "óbito"],
    "dinero": ["patrimonio", "bienes", "efectos", "caudal"],
    "herir": ["lesionar", "dañar", "causar lesiones", "agredir"],
}


def expandir_query_con_sinonimos(query: str) -> str:
    """
    🔍 MEJORA #7: Expansión semántica de consultas
    
    Expande la query original añadiendo sinónimos legales de términos coloquiales.
    Esto mejora la búsqueda vectorial para consultas informales.
    
    Ejemplo:
    - Input: "robar un coche"
    - Output: "robar hurto sustracción apropiación un coche vehículo"
    
    Args:
        query (str): La consulta original del usuario
        
    Returns:
        str: Query expandida con sinónimos legales
    """
    query_lower = query.lower()
    terminos_expandidos = [query]  # Mantener query original
    
    for termino_coloquial, sinonimos in SINONIMOS_LEGALES.items():
        if termino_coloquial in query_lower:
            # Añadir 2-3 sinónimos más relevantes
            terminos_expandidos.extend(sinonimos[:3])
    
    # Unir todos los términos sin repetir query completa
    query_expandida = query + " " + " ".join(terminos_expandidos[1:])
    
    if terminos_expandidos[1:]:  # Si se añadieron sinónimos
        print(f"🔍 Query expandida con {len(terminos_expandidos)-1} términos legales")
    
    return query_expandida
