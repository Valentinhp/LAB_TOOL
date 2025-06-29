<#
.SYNOPSIS
    Cierra todas las sesiones activas del usuario especificado.

.DESCRIPTION
    Pasos:
      1. Comprueba que el script se ejecute con privilegios de administrador.
      2. Obtiene la lista de sesiones mediante  QUERY SESSION.
      3. Filtra las que pertenecen al usuario (Username exacto, sin distinguir mayús/minús).
      4. Ejecuta LOGOFF en cada SessionID encontrado (o muestra la acción con -WhatIf).
      5. Informa el total de sesiones cerradas (o que se cerrarían).

.PARAMETER Username
    Nombre exacto de la cuenta local / de dominio a cerrar.

.PARAMETER WhatIf
    Simula la operación: solo muestra qué se haría, no cierra nada.

.EXAMPLE
    .\cerrar_sesion.ps1 -Username alumno2025

.EXAMPLE
    .\cerrar_sesion.ps1 -Username Profesor -WhatIf
#>

[CmdletBinding(SupportsShouldProcess = $true)]
param (
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$Username
)

# ─── Verificar que corremos como administrador ───
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
          ).IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)) {
    Write-Error "❌ Debes ejecutar este script como administrador."
    exit 1
}

# ─── Obtener sesiones ───────────────────────────
try {
    $sessions = & query session 2>$null
}
catch {
    Write-Error "❌ No se pudo ejecutar 'query session'. $_"
    exit 1
}

if (-not $sessions) {
    Write-Output "ℹ️ No se encontraron sesiones en el sistema."
    exit 0
}

$regex = "^\s*$Username\s+"     # Username exacto al principio de línea
$closed = 0

foreach ($line in $sessions) {
    if ($line -match $regex) {
        # Ejemplo de línea:
        # > alumno2025       rdp-tcp#8         3  Est.             12/06/2025 10:05
        $cols = $line -split '\s+'
        if ($cols.Count -ge 3 -and $cols[2] -match '^\d+$') {
            $id = $cols[2]

            if ($PSCmdlet.ShouldProcess("ID $id", "Cerrar sesión de '$Username'")) {
                try {
                    logoff $id 2>$null
                    Write-Host "✔ Sesión $id cerrada." -ForegroundColor Green
                }
                catch {
                    Write-Warning "✖ No se pudo cerrar sesión $id → $_"
                }
            }

            $closed++
        }
    }
}

# ─── Resultado ──────────────────────────────────
if ($closed -eq 0) {
    Write-Output "ℹ️ No había sesiones activas para '$Username'."
}
else {
    if ($WhatIf) {
        Write-Output "✅ (WhatIf) $closed sesión(es) se cerrarían."
    }
    else {
        Write-Output "✅ $closed sesión(es) de '$Username' cerradas."
    }
}

exit 0
