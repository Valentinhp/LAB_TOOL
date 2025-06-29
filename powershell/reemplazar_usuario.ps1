<#
.SYNOPSIS
  Borra un usuario local existente y lo sustituye por uno nuevo usando net user.
.PARAMETER OldUsername
  Nombre de la cuenta que se va a borrar.
.PARAMETER NewUsername
  Nombre de la cuenta que se va a crear.
.PARAMETER Password
  Contraseña en texto plano. Si es cadena vacía (""), la crea sin contraseña.
.PARAMETER NeverExpire
  Si se pasa, desactiva la expiración de contraseña.
#>

[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][string] $OldUsername,
  [Parameter(Mandatory=$true)][string] $NewUsername,
  [Parameter(Mandatory=$true)][string] $Password,
  [switch] $NeverExpire
)

function Assert-Admin {
  $pr = [Security.Principal.WindowsPrincipal]::new(
         [Security.Principal.WindowsIdentity]::GetCurrent())
  if (-not $pr.IsInRole(
        [Security.Principal.WindowsBuiltinRole]::Administrator)) {
    Write-Error "Debes ejecutar como administrador."
    exit 1
  }
}

Assert-Admin

# 1) Eliminar cuenta antigua
Write-Host "🗑️  Borrando usuario '$OldUsername'..."
net user $OldUsername /delete 2>$null
if ($LASTEXITCODE -ne 0) {
  Write-Warning "El usuario '$OldUsername' pudo no existir."
} else {
  Write-Host "✔ Usuario '$OldUsername' eliminado."
}

# 2) Descargar y descargar hives huérfanos
$query = reg query HKU 2>$null | Where-Object { $_ -match 'S-1-5-21' }
foreach ($h in $query) {
    reg unload $h 2>$null
}

# 3) Borrar carpeta de perfil
$prof = Join-Path $Env:SystemDrive "Users\$OldUsername"
if (Test-Path $prof) {
  Remove-Item -LiteralPath $prof -Recurse -Force 2>$null
  Write-Host "✔ Carpeta de perfil borrada: $prof"
}

# 4) Crear cuenta nueva
Write-Host "➕  Creando '$NewUsername'..."
if ($Password -eq "") {
  net user $NewUsername /add /Y 2>$null
} else {
  net user $NewUsername $Password /add /Y 2>$null
}
if ($LASTEXITCODE -ne 0) {
  Write-Error "Fallo al crear '$NewUsername'."
  exit 1
}
Write-Host "✔ Cuenta '$NewUsername' creada."

# 5) Añadir a Users
net localgroup Users $NewUsername /add 2>$null
Write-Host "✔ Añadido '$NewUsername' al grupo Users."

# 6) Nunca expira la contraseña
if ($NeverExpire) {
  wmic useraccount where name^="$NewUsername" set PasswordExpires=FALSE | Out-Null
  Write-Host "✔ Desactivada expiración de contraseña."
}

# 7) Desactivar “must change password at next logon”
try {
  $adsi = [ADSI]"WinNT://$env:COMPUTERNAME/$NewUsername,user"
  $adsi.PasswordExpired = $false
  $adsi.SetInfo()
  Write-Host "✔ Quitar obligación de cambiar contraseña."
} catch {
  Write-Warning "No pude desactivar PasswordExpired: $_"
}

Write-Host "✅ Usuario '$OldUsername' reemplazado por '$NewUsername'."
exit 0
