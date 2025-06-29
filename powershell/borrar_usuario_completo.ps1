<#
.SYNOPSIS
    Elimina por completo un usuario local y su perfil.

.DESCRIPTION
    Procedimiento paso a paso:
      0. Verifica que se ejecute con privilegios de administrador.
      1. Cierra sesiones activas del usuario (LOGOFF).
      2. Elimina la cuenta local  (net user <X> /delete).
      3. Descarga hives colgados en HKU.
      4. Borra la carpeta de perfil en  C:\Users\<Usuario>  (si existe).

.PARAMETER Username
    Nombre exacto de la cuenta local a eliminar.

.PARAMETER WhatIf
    Muestra las acciones que se realizarían sin efectuar cambios reales.

.PARAMETER Force
    Permite llamar al script con `-Force` desde Python sin error.
#>

param (
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[^\\/:*?"<>|]+$')]
    [string]$Username,

    [switch]$WhatIf,

    [switch]$Force
)

# ─────── Comprobación de administrador ───────
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
          ).IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)) {
    Write-Error "Debes ejecutar este script como administrador."
    exit 1
}

$Username = $Username.Trim('" ').Trim()
if (-not $Username) {
    Write-Error "Parámetro Username vacío."
    exit 1
}

Write-Host "`n*** Eliminación completa de '$Username' ***`n"

# WhatIf helper
function Invoke-Action($ScriptBlock, $Description) {
    if ($WhatIf) { 
        Write-Host "¿Qué pasaría?: $Description" -ForegroundColor Yellow 
    }
    else { 
        & $ScriptBlock 
    }
}

# 1) Cerrar sesiones activas del usuario
Invoke-Action {
    Write-Host "🔒 Cerrando sesiones activas..."
    $sessions = query session 2>$null
    foreach ($line in $sessions) {
        if ($line -match "^\s*$Username\s+") {
            $cols = $line -split '\s+'
            if ($cols.Count -ge 3 -and $cols[2] -match '^\d+$') {
                $id = $cols[2]
                try {
                    logoff $id /server:localhost
                    Write-Host "✔ Sesión $id cerrada."
                }
                catch { Write-Warning "✖ No se pudo cerrar sesión $id → $_" }
            }
        }
    }
} "Cerrar sesiones del usuario"

# 2) Eliminar la cuenta local
Invoke-Action {
    Write-Host "`n🗑️ Eliminando cuenta '$Username'..."
    try {
        net user $Username /delete | Out-Null
        Write-Host "✔ Cuenta eliminada."
    }
    catch { Write-Warning "✖ No se pudo eliminar la cuenta → $_" }
} "Eliminar cuenta local"

# 3) Descargar hives montados
Invoke-Action {
    Write-Host "`n⚙️ Descargando hives huérfanos en HKU..."
    $hives = reg query "HKU" 2>$null | Where-Object { $_ -match 'S-1-5-21' }
    foreach ($h in $hives) {
        $key = $h.Trim()
        try {
            reg unload $key 2>$null | Out-Null
            Write-Host "✔ Hive descargado: $key"
        }
        catch { Write-Warning "✖ No se pudo descargar hive $key → $_" }
    }
} "Descargar hives de HKU"

# 4) Borrar carpeta de perfil
$profilePath = Join-Path $Env:SystemDrive "Users\$Username"
Invoke-Action {
    if (Test-Path $profilePath) {
        Write-Host "`n🗑️ Borrando carpeta de perfil: $profilePath"
        try {
            Remove-Item -LiteralPath $profilePath -Recurse -Force
            Write-Host "✔ Carpeta de perfil borrada."
        }
        catch { Write-Warning "✖ Error borrando carpeta → $_" }
    }
    else {
        Write-Host "ℹ️ Carpeta de perfil no encontrada."
    }
} "Borrar carpeta de perfil ($profilePath)"

Write-Host "`n✅ Proceso finalizado." -ForegroundColor Green
exit 0
