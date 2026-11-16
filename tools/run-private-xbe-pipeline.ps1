# Run the MOH European Assault XBE recompilation pipeline locally.
# The XBE, generated C, and analysis outputs stay on this machine and are not uploaded.
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$XbePath,
    [string]$PythonLauncher = "py"
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Toolkit = Join-Path $RepoRoot "source/xboxrecomp-0.16.0"
$GameSource = Join-Path $RepoRoot "source/mygame"
$GenDir = Join-Path $GameSource "src/recomp/gen"
$ManualSource = Join-Path $GameSource "src/recomp_manual.c"

$XbePath = (Resolve-Path $XbePath).Path
if (-not (Test-Path (Join-Path $Toolkit "tools/xbe_parser/__main__.py"))) {
    throw "xboxrecomp tools were not found at: $Toolkit"
}
if (-not (Test-Path $ManualSource)) {
    throw "Manual override source was not found: $ManualSource"
}

Push-Location $Toolkit
try {
    # Validate Python and Capstone before starting the expensive stages.
    & $PythonLauncher -3 -c "import sys; assert sys.version_info >= (3,10), 'Python 3.10+ is required'; import capstone; print('Python', sys.version.split()[0], '| Capstone', capstone.__version__)"
    if ($LASTEXITCODE -ne 0) {
        throw "Python 3.10+ and Capstone are required. Install with: py -3 -m pip install capstone"
    }

    $XbeDir = Split-Path -Parent $XbePath
    $XbeBase = [IO.Path]::GetFileNameWithoutExtension($XbePath)
    $AnalysisJson = Join-Path $XbeDir ($XbeBase + "_analysis.json")
    $DisasmDir = Join-Path $Toolkit "tools/disasm/output"
    $FuncIdDir = Join-Path $Toolkit "tools/func_id/output"
    $AbiDir = Join-Path $Toolkit "tools/abi_analysis/output"
    $RecompReportDir = Join-Path $Toolkit "tools/recomp/output"

    New-Item -ItemType Directory -Force -Path $GenDir | Out-Null

    Write-Host "[1/5] Parse XBE"
    & $PythonLauncher -3 -m tools.xbe_parser $XbePath --json $AnalysisJson
    if ($LASTEXITCODE -ne 0) { throw "XBE parsing failed." }

    Write-Host "[2/5] Disassemble executable sections"
    & $PythonLauncher -3 -m tools.disasm $XbePath --analysis-json $AnalysisJson --text-only --output $DisasmDir --force -v
    if ($LASTEXITCODE -ne 0) { throw "XBE disassembly failed." }

    Write-Host "[3/5] Identify library and game functions"
    & $PythonLauncher -3 -m tools.func_id $XbePath --output $FuncIdDir --verbose
    if ($LASTEXITCODE -ne 0) { throw "Function identification failed." }

    Write-Host "[4/5] Recover calling conventions and signatures"
    & $PythonLauncher -3 -m tools.abi_analysis $XbePath --disasm-dir $DisasmDir --func-id-dir $FuncIdDir --output-dir $AbiDir -v
    if ($LASTEXITCODE -ne 0) { throw "ABI analysis failed." }

    Write-Host "[5/5] Recompile all functions (250 functions per C file)"
    & $PythonLauncher -3 -m tools.recomp $XbePath --all --split 250 --game-name "Medal of Honor European Assault" --gen-dir $GenDir --disasm-dir $DisasmDir --func-id-dir $FuncIdDir --abi-dir $AbiDir --output-dir $RecompReportDir --exclude-manual $ManualSource -v
    if ($LASTEXITCODE -ne 0) { throw "C recompilation failed." }

    $Generated = @(Get-ChildItem -Path $GenDir -Filter "recomp_*.c" -File)
    if ($Generated.Count -eq 0) {
        throw "The recompiler returned success but no generated C files were found."
    }

    Write-Host ""
    Write-Host "Pipeline completed. Generated C files: $($Generated.Count)"
    Write-Host "Private output directory: $GenDir"
    Write-Warning "The entries in source/gen_hand_edits.txt have NOT been reapplied automatically. Do not build or publish this generated tree until those edits have been reviewed and safely reapplied."
    Write-Warning "No UWP package or Xbox runtime test is performed by this script."
}
finally {
    Pop-Location
}
