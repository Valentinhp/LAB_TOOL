<#
.SYNOPSIS
    Bloquea el cambio de fondo de pantalla para el usuario que ejecuta el script
    y refresca el escritorio inmediatamente.

.DESCRIPTION
    ▸ Crea (si no existe) y/o modifica la clave:
          HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\ActiveDesktop  
      estableciendo el valor DWORD NoChangingWallpaper = 1.  
    ▸ Fuerza la recarga de políticas de usuario.  
    ▸ Refresca los parámetros de usuario para que el bloqueo se aplique al vuelo.
    ▸ Opcionalmente, reinicia Explorer si hiciera falta (descomentando la sección).

.PARAMETER (ninguno)
    El script no necesita parámetros.

.EXAMPLE
    .\bloquear_fondo.ps1
#>

param()   # — sin argumentos —

$ErrorActionPreference = "Stop"

try {
    # 1) Clave de políticas en HKCU
    $regPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Policies\ActiveDesktop"
    if (-not (Test-Path -LiteralPath $regPath)) {
        New-Item -Path $regPath -Force | Out-Null
    }
    Set-ItemProperty -Path $regPath `
                     -Name 'NoChangingWallpaper' `
                     -Value 1 `
                     -Type DWord `
                     -Force
    Write-Host "✔ Cambio de fondo bloqueado en registro."

    # 2) Forzar recarga de políticas de usuario
    Write-Host "⏳ Forzando gpupdate /target:user /force..." -ForegroundColor Cyan
    gpupdate /target:user /force | Out-Null

    # 3) Refrescar parámetros de usuario (fondo, Active Desktop)
    Write-Host "🔄 Actualizando parámetros de usuario..." -ForegroundColor Cyan
    RUNDLL32.EXE user32.dll,UpdatePerUserSystemParameters

    # 4) (Opcional) Reiniciar Explorer si aún no ves el cambio
    <#
    Write-Host "🔄 Reiniciando explorer.exe..." -ForegroundColor Cyan
    Stop-Process -Name explorer -Force
    Start-Process explorer.exe
    #>

    Write-Host "✅ Bloqueo aplicado y escritorio refrescado." -ForegroundColor Green
    exit 0
}
catch {
    Write-Error "❌ ERROR: $_"
    exit 1
}
