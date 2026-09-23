param(
    [ValidateSet('Debug', 'Release')][string]$Variant = 'Debug',
    [string]$JavaHome
)
$ErrorActionPreference = 'Stop'
if (-not $JavaHome) {
    $studio = Get-ItemProperty 'HKCU:/Software/Microsoft/Windows/CurrentVersion/Uninstall/*','HKLM:/Software/Microsoft/Windows/CurrentVersion/Uninstall/*' -ErrorAction SilentlyContinue |
        Where-Object { $_.DisplayName -eq 'Android Studio' } | Select-Object -First 1
    if ($studio.DisplayIcon) {
        $icon = ($studio.DisplayIcon -replace ',\d+$','').Trim('"')
        $candidate = Join-Path (Split-Path (Split-Path $icon -Parent) -Parent) 'jbr'
        if (Test-Path (Join-Path $candidate 'bin/java.exe')) { $JavaHome = $candidate }
    }
}
if (-not $JavaHome) { $JavaHome = $env:JAVA_HOME }
if (-not $JavaHome -or -not (Test-Path (Join-Path $JavaHome 'bin/java.exe'))) {
    throw 'Java não encontrado. Passe -JavaHome com a pasta jbr do Android Studio.'
}
$previousJava = $env:JAVA_HOME
try {
    $env:JAVA_HOME = $JavaHome
    & (Join-Path $PSScriptRoot 'gradlew.bat') -p $PSScriptRoot ":app:assemble$Variant" :app:testDebugUnitTest --console=plain
    if ($LASTEXITCODE -ne 0) { throw 'Compilação ou testes falharam. Consulte os erros acima.' }
    Write-Host "APKs em: $PSScriptRoot\app\build\outputs\apk\$($Variant.ToLower())"
    if ($Variant -eq 'Release' -and -not (Test-Path (Join-Path $PSScriptRoot 'keystore.properties'))) {
        Write-Warning 'Release sem assinatura: configure seu keystore antes de instalar/distribuir.'
    }
} finally { $env:JAVA_HOME = $previousJava }
