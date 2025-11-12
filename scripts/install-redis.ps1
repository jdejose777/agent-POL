# GUÍA DE INSTALACIÓN DE REDIS EN WINDOWS
# Este script documenta los pasos para instalar Redis

Write-Host "🗄️  INSTALACIÓN DE REDIS EN WINDOWS" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "📋 OPCIÓN 1: Usando Chocolatey (RECOMENDADO)" -ForegroundColor Yellow
Write-Host "---------------------------------------------" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Instalar Chocolatey si no lo tienes:" -ForegroundColor White
Write-Host "   Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Instalar Redis:" -ForegroundColor White
Write-Host "   choco install redis-64 -y" -ForegroundColor Green
Write-Host ""
Write-Host "3. Iniciar Redis:" -ForegroundColor White
Write-Host "   redis-server" -ForegroundColor Green
Write-Host ""

Write-Host "📋 OPCIÓN 2: Usando Windows Subsystem for Linux (WSL)" -ForegroundColor Yellow
Write-Host "-----------------------------------------------------" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Instalar WSL si no lo tienes:" -ForegroundColor White
Write-Host "   wsl --install" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Instalar Redis en WSL:" -ForegroundColor White
Write-Host "   wsl" -ForegroundColor Gray
Write-Host "   sudo apt update" -ForegroundColor Gray
Write-Host "   sudo apt install redis-server -y" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Iniciar Redis en WSL:" -ForegroundColor White
Write-Host "   sudo service redis-server start" -ForegroundColor Green
Write-Host ""

Write-Host "📋 OPCIÓN 3: Memurai (Alternativa comercial compatible con Redis)" -ForegroundColor Yellow
Write-Host "-------------------------------------------------------------------" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Descargar desde: https://www.memurai.com/" -ForegroundColor White
Write-Host "2. Instalar el ejecutable" -ForegroundColor White
Write-Host "3. Memurai se instala como servicio de Windows" -ForegroundColor White
Write-Host ""

Write-Host "📋 OPCIÓN 4: Usar Redis en Docker" -ForegroundColor Yellow
Write-Host "----------------------------------" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Instalar Docker Desktop para Windows" -ForegroundColor White
Write-Host "2. Ejecutar Redis en contenedor:" -ForegroundColor White
Write-Host "   docker run -d -p 6379:6379 --name redis redis:latest" -ForegroundColor Green
Write-Host ""

Write-Host ""
Write-Host "🔍 VERIFICAR INSTALACIÓN" -ForegroundColor Cyan
Write-Host "========================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Verificar que Redis está corriendo:" -ForegroundColor White
Write-Host "   redis-cli ping" -ForegroundColor Green
Write-Host "   (Debería responder: PONG)" -ForegroundColor Gray
Write-Host ""

Write-Host "2. Conectar al cliente Redis:" -ForegroundColor White
Write-Host "   redis-cli" -ForegroundColor Green
Write-Host ""

Write-Host "3. Comandos básicos de prueba:" -ForegroundColor White
Write-Host "   SET test 'Hello Redis'" -ForegroundColor Gray
Write-Host "   GET test" -ForegroundColor Gray
Write-Host "   DEL test" -ForegroundColor Gray
Write-Host ""

Write-Host ""
Write-Host "⚡ INICIO RÁPIDO (Chocolatey)" -ForegroundColor Green
Write-Host "=============================" -ForegroundColor Green
Write-Host ""

$response = Read-Host "¿Quieres instalar Redis ahora usando Chocolatey? (s/n)"

if ($response -eq "s" -or $response -eq "S") {
    Write-Host ""
    Write-Host "Instalando Redis con Chocolatey..." -ForegroundColor Yellow
    
    try {
        choco install redis-64 -y
        Write-Host ""
        Write-Host "✅ Redis instalado correctamente" -ForegroundColor Green
        Write-Host ""
        Write-Host "Iniciando Redis..." -ForegroundColor Yellow
        Start-Process -FilePath "redis-server" -NoNewWindow
        Write-Host "✅ Redis iniciado en localhost:6379" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Error al instalar Redis" -ForegroundColor Red
        Write-Host "Por favor, instala Chocolatey primero o usa otra opción" -ForegroundColor Yellow
    }
}
else {
    Write-Host ""
    Write-Host "Ok, puedes instalar Redis manualmente usando una de las opciones anteriores." -ForegroundColor White
}

Write-Host ""
Write-Host "📚 Documentación:" -ForegroundColor Cyan
Write-Host "   - Redis oficial: https://redis.io/docs/" -ForegroundColor White
Write-Host "   - Redis en Windows: https://github.com/microsoftarchive/redis/releases" -ForegroundColor White
Write-Host ""
