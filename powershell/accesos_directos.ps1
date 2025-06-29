<#
.SYNOPSIS
  Copia archivos .lnk al Escritorio de un usuario o al Público.

.PARAMETER Public
  Si está presente, copia en el Escritorio Público.

.PARAMETER User
  Nombre de usuario local (sin dominio). Copia en C:\Users\<User>\Desktop.

.PARAMETER WhatIf
  Simula la acción.

.PARAMETER Programs
  Rutas completas a archivos .lnk (capturados con ValueFromRemainingArguments).
#>

[CmdletBinding()]
param(
    [switch] $Public,
    [string] $User,
    [switch] $WhatIf,

    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]] $Programs
)

# Determinar carpeta destino
if ($Public) {
    $dest = [Environment]::GetFolderPath("CommonDesktopDirectory")
}
elseif ($User) {
    $dest = Join-Path $Env:SystemDrive "Users\$User\Desktop"
}
else {
    Write-Error "Debes indicar -Public o -User <nombre>."
    exit 1
}

Write-Host "Destino: $dest"
if (-not (Test-Path $dest)) {
    Write-Error "No existe carpeta destino: $dest"
    exit 1
}

if (-not $Programs) {
    Write-Error "No se proporcionaron archivos .lnk."
    exit 1
}

function Invoke-Act {
    param($ScriptBlock, $Desc)
    Write-Host "→ $Desc"
    if ($WhatIf) { Write-Host "   [Simulando]" }
    else        {
        & $ScriptBlock
        Write-Host "   [OK]"
    }
}

foreach ($lnk in $Programs) {
    if (-not (Test-Path $lnk)) {
        Write-Warning "No existe: $lnk"
        continue
    }
    $file = Split-Path $lnk -Leaf
    $target = Join-Path $dest $file
    Invoke-Act -ScriptBlock {
        Copy-Item -Path $lnk -Destination $target -Force
    } -Desc "Copiar '$file' → '$dest'"
}

Write-Host "✅ Accesos copiados."
exit 0
