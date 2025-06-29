<#
.SYNOPSIS
  Crea un usuario local habilitado, sin contraseña si se indica,
  lo añade al grupo Users/Usuarios detectado por SID,
  y marca “nunca expira” opcional.

.PARAMETER Username
  Nombre de la cuenta (obligatorio).

.PARAMETER NoPassword
  Si se pasa, crea la cuenta sin contraseña.

.PARAMETER NeverExpire
  Si se pasa, marca la contraseña como “never expires”.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)] [string] $Username,
    [Parameter(Mandatory=$false)] [switch] $NoPassword,
    [Parameter(Mandatory=$false)] [switch] $NeverExpire
)

try {
    # Crear usuario con o sin contraseña
    if ($NoPassword.IsPresent) {
        New-LocalUser -Name $Username -NoPassword -ErrorAction Stop
    }
    else {
        throw "Debe indicarse -NoPassword para crear sin contraseña"
    }

    # Habilitar
    Enable-LocalUser -Name $Username -ErrorAction Stop

    # Detectar nombre real del grupo Users/Usuarios por SID
    $sid = New-Object System.Security.Principal.SecurityIdentifier 'S-1-5-32-545'
    $nt = $sid.Translate([System.Security.Principal.NTAccount])
    $group = $nt.Value.Split('\')[-1]

    # Añadir al grupo
    Add-LocalGroupMember -Group $group -Member $Username -ErrorAction Stop

    # Never expire
    if ($NeverExpire.IsPresent) {
        Set-LocalUser -Name $Username -PasswordNeverExpires $true -ErrorAction Stop
    }

    Write-Output "Usuario '$Username' creado sin contraseña, habilitado y añadido al grupo '$group'."
    exit 0
}
catch {
    Write-Error $_.Exception.Message
    exit 1
}
