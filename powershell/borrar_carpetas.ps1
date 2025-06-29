<#
.SYNOPSIS
    Borra en lote subcarpetas de un directorio raíz interactivo.

.DESCRIPTION
    ▸ Pregunta (o recibe con -Root) la carpeta raíz.  
    ▸ Muestra las subcarpetas directas numeradas.  
    ▸ Permite seleccionar índices (“1,3,7”), un rango (“2-5”) o “all”.  
    ▸ Solicita confirmación con la palabra BORRAR (a menos que se use -Force).  
    ▸ Elimina carpeta por carpeta mostrando resultado; los errores
      no detienen el resto.

.PARAMETER Root
    Carpeta raíz donde iniciar el listado. Si no se pasa, se pide por Read-Host.

.PARAMETER Force
    Si se indica, omite la confirmación de “BORRAR”.

.EXAMPLE
    .\borrar_carpetas_lote.ps1

.EXAMPLE
    .\borrar_carpetas_lote.ps1 -Root "D:\Proyectos" -Force
#>

param (
    [string]$Root,
    [switch]$Force   # omite la confirmación BORRAR
)

$ErrorActionPreference = "Stop"

try {
    # 1) Carpeta raíz: parámetro o prompt
    if (-not $Root) {
        $Root = Read-Host "📂 Ruta de carpeta raíz para borrado en lote"
    }
    $Root = $Root.Trim('" ').TrimEnd('\')
    if (-not (Test-Path -LiteralPath $Root -PathType Container)) {
        throw "La ruta '$Root' no es una carpeta válida."
    }

    # 2) Listar subcarpetas directas
    Write-Host "`nBuscando subcarpetas en '$Root'..."
    $folders = Get-ChildItem -Path $Root -Directory -ErrorAction SilentlyContinue |
               Sort-Object Name

    if (-not $folders) {
        Write-Host "❌ No se encontraron subcarpetas en '$Root'."
        exit 0
    }

    # 3) Listado numerado
    1..$folders.Count | ForEach-Object {
        "{0,3}) {1}" -f $_, $folders[$_-1].FullName
    } | Write-Host

    # 4) Selección
    $selection = Read-Host "`nEscribe índices (ej: 1,3-5) o 'all'"
    if ($selection.Trim().ToLower() -eq 'all') {
        $indices = 0..($folders.Count - 1)
    }
    else {
        $indices = @()
        foreach ($token in $selection -split '[,\s]+') {
            if ($token -match '^\d+$') {
                $idx = [int]$token - 1
                if ($idx -ge 0 -and $idx -lt $folders.Count) { $indices += $idx }
            }
            elseif ($token -match '^(\d+)-(\d+)$') {
                $start = [int]$Matches[1] - 1
                $end   = [int]$Matches[2] - 1
                $indices += $start..$end
            }
        }
        $indices = $indices | Select-Object -Unique | Sort-Object
        if (-not $indices) { throw "Selección inválida." }
    }

    # 5) Confirmación
    if (-not $Force) {
        $ok = Read-Host "✋ Escribe 'BORRAR' para confirmar el borrado de $($indices.Count) carpeta(s)"
        if ($ok.Trim() -ne 'BORRAR') {
            Write-Host "⛔ Operación cancelada."
            exit 0
        }
    }

    # 6) Borrado en lote
    foreach ($i in $indices) {
        $path = $folders[$i].FullName
        try {
            Remove-Item -LiteralPath $path -Recurse -Force
            Write-Host "🗑️ Borrada: $path"
        }
        catch {
            Write-Warning "❌ Error borrando '$path': $_"
        }
    }

    Write-Host "`n✅ Proceso finalizado."
    exit 0
}
catch {
    Write-Error "❌ $_"
    exit 1
}
