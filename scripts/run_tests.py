"""
Script para ejecutar todos los tests del proyecto agent-POL
Uso: python run_tests.py [opciones]

Opciones:
    --quick       Solo tests rápidos (sin slow)
    --unit        Solo tests unitarios
    --integration Solo tests de integración
    --backend     Solo tests del backend
    --frontend    Solo tests del frontend
    --coverage    Generar reporte de cobertura
    --verbose     Modo verbose
"""

import sys
import subprocess
from pathlib import Path

def run_tests(args=None):
    """Ejecuta los tests con pytest"""
    
    # Comando base
    cmd = [sys.executable, "-m", "pytest"]
    
    # Parsear argumentos
    if args:
        if "--quick" in args:
            cmd.extend(["-m", "not slow"])
        elif "--unit" in args:
            cmd.extend(["-m", "unit"])
        elif "--integration" in args:
            cmd.extend(["-m", "integration"])
        elif "--backend" in args:
            cmd.extend(["-m", "backend"])
        elif "--frontend" in args:
            cmd.extend(["-m", "frontend"])
        
        if "--verbose" in args:
            cmd.append("-vv")
        
        if "--coverage" in args:
            cmd.extend([
                "--cov=backend-api",
                "--cov-report=html:test-results/coverage",
                "--cov-report=term"
            ])
    
    # Ejecutar pytest
    print("\n" + "="*80)
    print("🧪 EJECUTANDO TESTS")
    print("="*80)
    print(f"Comando: {' '.join(cmd)}")
    print("="*80 + "\n")
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    
    print("\n" + "="*80)
    if result.returncode == 0:
        print("✅ TODOS LOS TESTS PASARON")
    else:
        print("❌ ALGUNOS TESTS FALLARON")
    print("="*80 + "\n")
    
    if "--coverage" in (args or []):
        coverage_path = Path(__file__).parent / "test-results" / "coverage" / "index.html"
        print(f"📊 Reporte de cobertura: {coverage_path}")
    
    report_path = Path(__file__).parent / "test-results" / "report.html"
    print(f"📋 Reporte HTML: {report_path}")
    print()
    
    return result.returncode


if __name__ == "__main__":
    sys.exit(run_tests(sys.argv[1:]))
