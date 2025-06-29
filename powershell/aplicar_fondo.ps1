<#
.SYNOPSIS
    Aplica una imagen como fondo de pantalla y opcionalmente bloquea el cambio.

.PARAMETER Image
    Ruta al archivo de imagen (obligatorio).

.PARAMETER Default
    Si se pasa, también copia la imagen a %SystemRoot%\Web\Wallpaper\CustomWallpaper.png
    para que sea el fondo predeterminado de nuevos usuarios.

.PARAMETER Current
    Si se pasa, aplica el fondo al usuario actual.

.PARAMETER WhatIf
    Simula sin cambios reales.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)] [string] $Image,
    [switch]                          $Default,
    [switch]                          $Current,
    [switch]                          $WhatIf
)

function Invoke-Act {
    param($ScriptBlock, $Desc)
    if ($WhatIf) {
        Write-Host "[WhatIf] $Desc" -ForegroundColor Yellow
    } else {
        Write-Host $Desc -ForegroundColor Cyan
        & $ScriptBlock
    }
}

# Constantes para SystemParametersInfo
$SPI_SETDESKWALLPAPER = 0x0014
$SPIF_UPDATEINIFILE   = 0x0001
$SPIF_SENDCHANGE      = 0x0002

# ---- Verificar administrador ----
$pr = [Security.Principal.WindowsPrincipal]::new(
    [Security.Principal.WindowsIdentity]::GetCurrent()
)
if (-not $pr.IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)) {
    Write-Error "Debes ejecutar como administrador."
    exit 1
}

# ---- Validar imagen ----
if (-not (Test-Path $Image)) {
    Write-Error "No se encontró la imagen: $Image"
    exit 1
}
$fullImage = (Resolve-Path $Image).Path

# 1) (Opcional) Copiar al fondo por defecto
if ($Default) {
    $dest = Join-Path $Env:SystemRoot "Web\Wallpaper\CustomWallpaper.png"
    Invoke-Act { Copy-Item -Path $fullImage -Destination $dest -Force } `
        "Copiar imagen a $dest para usuarios nuevos"
}

# 2) Agrega definición COM para SystemParametersInfo si no existe
if (-not ("NativeMethods" -as [type])) {
    Add-Type -Namespace WinAPI -Name NativeMethods -MemberDefinition @'
    [DllImport("user32.dll",SetLastError=true,CharSet=CharSet.Auto)]
    public static extern bool SystemParametersInfo(
        uint uiAction, uint uiParam, string pvParam, uint fWinIni);
'@ -ErrorAction Stop
}

# 3) Aplicar al usuario actual vía API nativa
if ($Current) {
    Invoke-Act {
        [void][WinAPI.NativeMethods]::SystemParametersInfo(
            $SPI_SETDESKWALLPAPER,
            0,
            $fullImage,
            $SPIF_UPDATEINIFILE -bor $SPIF_SENDCHANGE
        )
    } "Aplicar fondo al usuario actual vía SystemParametersInfo"
}
elseif ($Default -and -not $Current) {
    # Si solo Default, también aplicamos al usuario actual
    Invoke-Act {
        [void][WinAPI.NativeMethods]::SystemParametersInfo(
            $SPI_SETDESKWALLPAPER,
            0,
            $fullImage,
            $SPIF_UPDATEINIFILE -bor $SPIF_SENDCHANGE
        )
    } "Aplicar fondo al usuario actual (por Default)"
}

# 4) Bloquear cambio de fondo en política
Invoke-Act {
    New-Item -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\ActiveDesktop" `
        -Force -ErrorAction SilentlyContinue | Out-Null
    New-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\ActiveDesktop" `
        -Name "NoChangingWallPaper" -Value 1 -PropertyType DWORD -Force
} "Bloquear cambio de fondo en políticas (NoChangingWallPaper=1)"

Write-Host "✅ Fondo aplicado y bloqueo configurado correctamente." -ForegroundColor Green
exit 0
