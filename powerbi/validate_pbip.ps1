param(
    [string]$DesktopBin
)

$ErrorActionPreference = "Stop"

$powerBiRoot = if ($PSScriptRoot) {
    $PSScriptRoot
} else {
    Join-Path (Get-Location).Path "powerbi"
}
$projectRoot = Split-Path -Parent $powerBiRoot
$dataRoot = Join-Path $projectRoot "portfolio_data"
$modelPath = Join-Path $powerBiRoot "AnalyticsClientes.SemanticModel\model.bim"
$pagesRoot = Join-Path $powerBiRoot "AnalyticsClientes.Report\definition\pages"

$requiredSources = @(
    "executive_monthly",
    "customer_segment_summary",
    "customer_cross_segment",
    "customer_category_affinity",
    "category_performance",
    "delivery_experience",
    "seller_performance",
    "quality_checks"
)

$jsonFiles = New-Object System.Collections.Generic.List[string]
[System.IO.Directory]::EnumerateFiles(
    $powerBiRoot,
    "*.json",
    [System.IO.SearchOption]::AllDirectories
) | ForEach-Object { $jsonFiles.Add($_) }

@(
    (Join-Path $powerBiRoot "AnalyticsClientes.pbip"),
    (Join-Path $powerBiRoot "AnalyticsClientes.Report\.platform"),
    (Join-Path $powerBiRoot "AnalyticsClientes.Report\definition.pbir"),
    (Join-Path $powerBiRoot "AnalyticsClientes.SemanticModel\.platform"),
    (Join-Path $powerBiRoot "AnalyticsClientes.SemanticModel\definition.pbism"),
    $modelPath
) | ForEach-Object { $jsonFiles.Add($_) }

foreach ($path in $jsonFiles) {
    $null = [System.IO.File]::ReadAllText($path) |
        ConvertFrom-Json -ErrorAction Stop
}

$modelText = [System.IO.File]::ReadAllText($modelPath)
if ([regex]::IsMatch($modelText, '(?i)[A-Z]:\\')) {
    throw "model.bim contiene una ruta absoluta."
}

$modelDefinition = $modelText | ConvertFrom-Json
$dataFolder = @(
    $modelDefinition.model.expressions |
        Where-Object { $_.name -eq "DataFolder" }
)
if ($dataFolder.Count -ne 1 -or -not $dataFolder[0].expression.StartsWith('"..\portfolio_data\')) {
    throw "DataFolder no conserva el valor relativo esperado."
}

$modelTables = @{}
foreach ($table in $modelDefinition.model.tables) {
    $columns = @{}
    foreach ($column in $table.columns) {
        $columns[$column.name] = $true
    }
    $measures = @{}
    foreach ($measure in $table.measures) {
        $measures[$measure.name] = $true
    }
    $modelTables[$table.name] = @{ Columns = $columns; Measures = $measures }
}

$rowCounts = @{}
foreach ($tableName in $requiredSources) {
    $csvPath = Join-Path $dataRoot ($tableName + ".csv")
    if (-not (Test-Path -LiteralPath $csvPath)) {
        throw "Falta la fuente requerida: $tableName.csv"
    }

    $records = @(Import-Csv -LiteralPath $csvPath -Encoding UTF8)
    if ($records.Count -eq 0) {
        throw "La fuente no contiene filas: $tableName.csv"
    }
    $rowCounts[$tableName] = $records.Count

    $csvColumns = @($records[0].PSObject.Properties.Name)
    if ("coverage_status" -in $csvColumns) {
        $nonPublicRows = @(
            $records | Where-Object { $_.coverage_status -ne "PUBLISHABLE" }
        )
        if ($nonPublicRows.Count -gt 0) {
            throw "$tableName.csv contiene filas no publicables: $($nonPublicRows.Count)"
        }
    }
    $sourceColumns = @(
        $modelDefinition.model.tables |
            Where-Object { $_.name -eq $tableName } |
            ForEach-Object { $_.columns.sourceColumn }
    )
    $missing = @($sourceColumns | Where-Object { $_ -notin $csvColumns })
    if ($missing.Count -gt 0) {
        throw "Columnas ausentes en $tableName.csv: $($missing -join ', ')"
    }

    $tableDefinition = @(
        $modelDefinition.model.tables |
            Where-Object { $_.name -eq $tableName }
    )[0]
    foreach ($column in $tableDefinition.columns) {
        if ($column.dataType -eq "string") {
            continue
        }
        for ($rowIndex = 0; $rowIndex -lt $records.Count; $rowIndex++) {
            $value = [string]$records[$rowIndex].PSObject.Properties[$column.sourceColumn].Value
            if ([string]::IsNullOrWhiteSpace($value)) {
                continue
            }

            $isValid = $false
            if ($column.dataType -eq "int64") {
                $parsedInteger = 0L
                $isValid = [long]::TryParse(
                    $value,
                    [System.Globalization.NumberStyles]::Integer,
                    [System.Globalization.CultureInfo]::InvariantCulture,
                    [ref]$parsedInteger
                )
            } elseif ($column.dataType -eq "double") {
                $parsedDouble = 0.0
                $isValid = [double]::TryParse(
                    $value,
                    [System.Globalization.NumberStyles]::Float,
                    [System.Globalization.CultureInfo]::InvariantCulture,
                    [ref]$parsedDouble
                )
            } elseif ($column.dataType -eq "dateTime") {
                $parsedDate = [datetime]::MinValue
                $isValid = [datetime]::TryParseExact(
                    $value,
                    "yyyy-MM-dd",
                    [System.Globalization.CultureInfo]::InvariantCulture,
                    [System.Globalization.DateTimeStyles]::None,
                    [ref]$parsedDate
                )
            }

            if (-not $isValid) {
                throw "Tipo invalido en $tableName.$($column.sourceColumn), fila $($rowIndex + 2): $value"
            }
        }
    }
}

$visualFiles = @(
    [System.IO.Directory]::EnumerateFiles(
        $pagesRoot,
        "visual.json",
        [System.IO.SearchOption]::AllDirectories
    )
)
foreach ($path in $visualFiles) {
    $text = [System.IO.File]::ReadAllText($path)
    foreach ($match in [regex]::Matches($text, '"queryRef":"([^"]+)"')) {
        $reference = $match.Groups[1].Value
        $separator = $reference.IndexOf(".")
        if ($separator -lt 1) {
            continue
        }
        $entity = $reference.Substring(0, $separator)
        $property = $reference.Substring($separator + 1)
        if (-not $modelTables.ContainsKey($entity)) {
            throw "Visual con tabla inexistente: $reference"
        }
        if (
            -not $modelTables[$entity].Columns.ContainsKey($property) -and
            -not $modelTables[$entity].Measures.ContainsKey($property)
        ) {
            throw "Visual con campo inexistente: $reference"
        }
    }
}

$pageFiles = @(
    [System.IO.Directory]::EnumerateFiles(
        $pagesRoot,
        "page.json",
        [System.IO.SearchOption]::AllDirectories
    )
)
$pageNames = @(
    $pageFiles |
        ForEach-Object {
            ([System.IO.File]::ReadAllText($_) | ConvertFrom-Json).displayName
        }
)
$expectedPages = @(
    "Panorama ejecutivo",
    "Clientes y mix",
    "Operación y experiencia",
    "Calidad y cobertura"
)
if (@($expectedPages | Where-Object { $_ -notin $pageNames }).Count -gt 0) {
    throw "No se encontraron las cuatro paginas requeridas."
}

if (-not $DesktopBin) {
    $candidates = New-Object System.Collections.Generic.List[string]
    $candidates.Add((Join-Path $env:ProgramFiles "Microsoft Power BI Desktop\bin"))
    $desktopPackage = Get-AppxPackage -Name "Microsoft.MicrosoftPowerBIDesktop" `
        -ErrorAction SilentlyContinue |
        Sort-Object Version -Descending |
        Select-Object -First 1
    if ($desktopPackage) {
        $candidates.Add((Join-Path $desktopPackage.InstallLocation "bin"))
    }
    foreach ($candidate in $candidates) {
        if (
            (Test-Path -LiteralPath (Join-Path $candidate "Microsoft.AnalysisServices.Server.Core.dll")) -and
            (Test-Path -LiteralPath (Join-Path $candidate "Microsoft.AnalysisServices.Server.Tabular.dll"))
        ) {
            $DesktopBin = $candidate
            break
        }
    }
}

if (-not $DesktopBin) {
    throw "No se encontro Power BI Desktop para validar model.bim con TOM."
}

Add-Type -Path (Join-Path $DesktopBin "Microsoft.AnalysisServices.Server.Core.dll")
Add-Type -Path (Join-Path $DesktopBin "Microsoft.AnalysisServices.Server.Tabular.dll")
$database = [Microsoft.AnalysisServices.Tabular.JsonSerializer]::DeserializeDatabase($modelText)
$measureCount = 0
foreach ($table in $database.Model.Tables) {
    $measureCount += $table.Measures.Count
}

Write-Output "PBIP validado."
Write-Output "JSON: $($jsonFiles.Count) archivos."
Write-Output "Modelo TOM: $($database.Model.Tables.Count) tablas, $($database.Model.Relationships.Count) relaciones, $measureCount medidas."
Write-Output "Reporte PBIR: $($pageFiles.Count) paginas, $($visualFiles.Count) visuales."
Write-Output "Filas CSV: $(($requiredSources | ForEach-Object { $_ + '=' + $rowCounts[$_] }) -join '; ')."
