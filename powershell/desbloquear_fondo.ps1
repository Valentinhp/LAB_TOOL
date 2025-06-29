<#
.SYNOPSIS
    Elimina las políticas que bloquean el Active Desktop y refresca el Explorador.

.DESCRIPTION
    • Borra las claves de registro en HKCU y HKLM que impiden cambiar el fondo.  
    • Fuerza la recarga de políticas de usuario.  
    • Refresca el escritorio y reinicia Explorer para aplicar los cambios en caliente.
#>

# 1) Eliminar claves de bloqueo en registro

Write-Host "🔓 Quitando bloqueo de Active Desktop en HKCU..." -ForegroundColor Cyan
Remove-Item -Path "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\ActiveDesktop" `
    -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "🔓 Quitando bloqueo de Active Desktop en HKLM..." -ForegroundColor Cyan
Remove-Item -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\ActiveDesktop" `
    -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "🔓 Quitando bloqueo de Active Desktop (Wow6432Node)..." -ForegroundColor Cyan
Remove-Item -Path "HKLM:\SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Policies\ActiveDesktop" `
    -Recurse -Force -ErrorAction SilentlyContinue

# 2) Forzar recarga de políticas de usuario

Write-Host "⏳ Forzando gpupdate /target:user /force..." -ForegroundColor Cyan
Start-Process -FilePath gpupdate -ArgumentList '/target:user','/force' -NoNewWindow -Wait

# 3) Refrescar parámetros de usuario (fondo, Active Desktop)

Write-Host "🔄 Actualizando parámetros de usuario..." -ForegroundColor Cyan
Start-Process -FilePath RUNDLL32.EXE -ArgumentList 'user32.dll,UpdatePerUserSystemParameters' -NoNewWindow -Wait

# 4) Reiniciar Explorer para garantizar aplicación

Write-Host "🔄 Reiniciando explorer.exe..." -ForegroundColor Cyan
Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue
Start-Process -FilePath explorer.exe

Write-Host "✅ ¡Desbloqueo completado! Ahora deberías poder cambiar el fondo." -ForegroundColor Green
