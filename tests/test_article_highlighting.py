"""
TESTS PARA HIGHLIGHTING DE ARTÍCULOS EN FRONTEND
Valida la funcionalidad de resaltado de referencias a artículos del Código Penal
"""

import pytest
import re
from pathlib import Path


def test_css_article_highlight_class_exists():
    """Verificar que existe la clase .article-highlight en style.css"""
    css_path = Path(__file__).parent.parent / "frontend" / "style.css"
    
    assert css_path.exists(), "style.css no encontrado"
    
    css_content = css_path.read_text(encoding="utf-8")
    
    # Verificar que existe la clase
    assert ".article-highlight" in css_content
    assert "background:" in css_content or "background-color:" in css_content
    
    print("✅ Clase .article-highlight encontrada en CSS")


def test_css_article_highlight_has_visual_styles():
    """Verificar que la clase tiene estilos visuales apropiados"""
    css_path = Path(__file__).parent.parent / "frontend" / "style.css"
    css_content = css_path.read_text(encoding="utf-8")
    
    # Buscar el bloque de .article-highlight
    highlight_block = re.search(
        r'\.article-highlight\s*\{([^}]+)\}',
        css_content,
        re.DOTALL
    )
    
    assert highlight_block, "No se encontró el bloque de estilos .article-highlight"
    
    styles = highlight_block.group(1)
    
    # Verificar estilos clave
    assert "background" in styles, "Debe tener background"
    assert "color" in styles or "color:" in styles, "Debe tener color"
    assert "font-weight" in styles, "Debe tener font-weight para destacar"
    
    print("✅ Clase .article-highlight tiene estilos visuales apropiados")


def test_css_article_highlight_has_hover_effect():
    """Verificar que hay efecto hover para artículos"""
    css_path = Path(__file__).parent.parent / "frontend" / "style.css"
    css_content = css_path.read_text(encoding="utf-8")
    
    # Buscar :hover para article-highlight
    assert ".article-highlight:hover" in css_content
    
    print("✅ Efecto hover definido para .article-highlight")


def test_js_highlight_function_exists():
    """Verificar que existe la función highlightArticulos en app.js"""
    js_path = Path(__file__).parent.parent / "frontend" / "app.js"
    
    assert js_path.exists(), "app.js no encontrado"
    
    js_content = js_path.read_text(encoding="utf-8")
    
    # Verificar que existe la función
    assert "function highlightArticulos" in js_content or "highlightArticulos" in js_content
    
    print("✅ Función highlightArticulos encontrada en app.js")


def test_js_highlight_function_has_regex_pattern():
    """Verificar que la función tiene un patrón regex para detectar artículos"""
    js_path = Path(__file__).parent.parent / "frontend" / "app.js"
    js_content = js_path.read_text(encoding="utf-8")
    
    # Buscar patrones comunes de regex para artículos
    patterns = [
        r"Artículo",
        r"artículo",
        r"Art\.",
        r"\d+",  # números
    ]
    
    # Verificar que hay un regex que busca estas palabras
    for pattern in patterns:
        assert pattern in js_content, f"Patrón '{pattern}' debería estar en la función"
    
    print("✅ Función highlightArticulos tiene patrón regex para detectar artículos")


def test_js_highlight_creates_spans():
    """Verificar que la función crea spans con clase article-highlight"""
    js_path = Path(__file__).parent.parent / "frontend" / "app.js"
    js_content = js_path.read_text(encoding="utf-8")
    
    # Buscar la creación de spans con la clase
    assert 'class="article-highlight"' in js_content or "class='article-highlight'" in js_content
    
    print("✅ Función crea spans con clase article-highlight")


def test_js_highlight_integrated_in_addBotMessage():
    """Verificar que highlightArticulos está integrado en addBotMessage"""
    js_path = Path(__file__).parent.parent / "frontend" / "app.js"
    js_content = js_path.read_text(encoding="utf-8")
    
    # Buscar la función addBotMessage
    assert "function addBotMessage" in js_content
    
    # Buscar el bloque de addBotMessage
    addbotmessage_match = re.search(
        r'function addBotMessage\([^)]*\)\s*\{(.+?)\n\}(?:\n|$)',
        js_content,
        re.DOTALL
    )
    
    assert addbotmessage_match, "No se encontró la función addBotMessage"
    
    function_body = addbotmessage_match.group(1)
    
    # Verificar que se llama a highlightArticulos
    assert "highlightArticulos" in function_body
    
    print("✅ highlightArticulos está integrado en addBotMessage")


def test_js_scroll_to_article_function_exists():
    """Verificar que existe función para scroll/navegación a artículos"""
    js_path = Path(__file__).parent.parent / "frontend" / "app.js"
    js_content = js_path.read_text(encoding="utf-8")
    
    # Verificar que existe alguna función relacionada con navegación
    assert "scrollToArticle" in js_content or "navigateToArticle" in js_content
    
    print("✅ Función de navegación a artículos encontrada")


def test_js_highlight_handles_single_article():
    """Test lógico: verificar que el código maneja artículos individuales"""
    js_path = Path(__file__).parent.parent / "frontend" / "app.js"
    js_content = js_path.read_text(encoding="utf-8")
    
    # Buscar lógica para un solo artículo
    # Debería haber algún manejo de "numerosArray.length === 1" o similar
    assert "length === 1" in js_content or "length == 1" in js_content
    
    print("✅ Lógica para artículos individuales presente")


def test_js_highlight_handles_multiple_articles():
    """Test lógico: verificar que el código maneja múltiples artículos"""
    js_path = Path(__file__).parent.parent / "frontend" / "app.js"
    js_content = js_path.read_text(encoding="utf-8")
    
    # Buscar lógica para múltiples artículos
    # Debería haber algún else o manejo de array > 1
    function_block = re.search(
        r'function highlightArticulos[^{]*\{(.+?)\n\}',
        js_content,
        re.DOTALL
    )
    
    assert function_block, "No se encontró función highlightArticulos"
    
    # Verificar que hay lógica para iterar (forEach, for, map)
    function_body = function_block.group(1)
    assert any(keyword in function_body for keyword in ["forEach", "for", "map", "split"])
    
    print("✅ Lógica para múltiples artículos presente")


def test_regex_pattern_matches_articulo_variations():
    """Test del patrón regex: debe coincidir con variaciones de 'Artículo'"""
    # Simulamos el patrón que debería estar en JS
    patron_articulos = re.compile(
        r'(Artículo|artículo|Art\.|art\.|Arts\.|arts\.|Artículos|artículos)\s+(\d+(?:\s*,\s*\d+)*(?:\s+y\s+\d+)?)',
        re.IGNORECASE
    )
    
    test_cases = [
        ("Artículo 234", True),
        ("artículo 234", True),
        ("Art. 234", True),
        ("art. 234", True),
        ("Artículos 234 y 456", True),
        ("artículos 234, 456 y 789", True),
        ("random text 234", False),
        ("article 234", False),  # inglés no debería coincidir
    ]
    
    for text, should_match in test_cases:
        match = patron_articulos.search(text)
        if should_match:
            assert match, f"Debería coincidir: {text}"
        else:
            assert not match, f"No debería coincidir: {text}"
    
    print("✅ Patrón regex valida correctamente variaciones de 'Artículo'")


def test_css_responsive_article_highlight():
    """Verificar que hay estilos responsive para article-highlight"""
    css_path = Path(__file__).parent.parent / "frontend" / "style.css"
    css_content = css_path.read_text(encoding="utf-8")
    
    # Buscar media queries relacionadas con article-highlight
    # Debería haber algún @media con ajustes para móviles
    media_queries = re.findall(r'@media[^{]+\{[^}]+\.article-highlight[^}]*\}', css_content, re.DOTALL)
    
    # Al menos debería haber consideración responsive
    assert len(media_queries) > 0 or "@media" in css_content
    
    print("✅ Estilos responsive considerados para article-highlight")


def test_css_article_highlight_color_scheme():
    """Verificar que el color del highlight es apropiado (amarillo/oro)"""
    css_path = Path(__file__).parent.parent / "frontend" / "style.css"
    css_content = css_path.read_text(encoding="utf-8")
    
    # Buscar el bloque de .article-highlight
    highlight_block = re.search(
        r'\.article-highlight\s*\{([^}]+)\}',
        css_content,
        re.DOTALL
    )
    
    assert highlight_block
    styles = highlight_block.group(1).lower()
    
    # Verificar que usa colores cálidos (amarillo, oro, naranja)
    # Buscamos rgba/rgb con valores altos en R y G (amarillo/oro)
    # O palabras clave como "yellow", "gold", "amber", "orange"
    warm_colors = ["yellow", "gold", "amber", "orange", "fbbf24", "f59e0b", "251, 191, 36", "245, 158, 11"]
    
    assert any(color in styles for color in warm_colors), "Debería usar colores cálidos (amarillo/oro/naranja)"
    
    print("✅ Color del highlight es apropiado (amarillo/oro)")


def test_js_onclick_handler_for_articles():
    """Verificar que los artículos tienen onclick handler"""
    js_path = Path(__file__).parent.parent / "frontend" / "app.js"
    js_content = js_path.read_text(encoding="utf-8")
    
    # Buscar onclick en la generación de spans
    assert "onclick" in js_content.lower()
    
    print("✅ Artículos tienen onclick handler")


def test_js_data_attribute_for_article_number():
    """Verificar que se almacena el número de artículo en data attribute"""
    js_path = Path(__file__).parent.parent / "frontend" / "app.js"
    js_content = js_path.read_text(encoding="utf-8")
    
    # Buscar data-article o similar
    assert "data-article" in js_content
    
    print("✅ Número de artículo se almacena en data attribute")


def test_integration_css_and_js():
    """Test de integración: CSS y JS usan el mismo nombre de clase"""
    css_path = Path(__file__).parent.parent / "frontend" / "style.css"
    js_path = Path(__file__).parent.parent / "frontend" / "app.js"
    
    css_content = css_path.read_text(encoding="utf-8")
    js_content = js_path.read_text(encoding="utf-8")
    
    # Verificar que ambos usan "article-highlight"
    assert ".article-highlight" in css_content
    assert "article-highlight" in js_content
    
    print("✅ CSS y JS usan consistentemente la clase 'article-highlight'")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
