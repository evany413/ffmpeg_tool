[CmdletBinding()]
param(
    [switch]$ForceFfmpeg
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
[System.Net.ServicePointManager]::SecurityProtocol =
    [System.Net.ServicePointManager]::SecurityProtocol -bor
    [System.Net.SecurityProtocolType]::Tls12

$projectDirectory = $PSScriptRoot
$repositoryRoot = [System.IO.Path]::GetFullPath((Join-Path $projectDirectory '..'))
$ffmpegBinDirectory = Join-Path $repositoryRoot '.tools\ffmpeg\bin'
$ffmpegExecutable = Join-Path $ffmpegBinDirectory 'ffmpeg.exe'
$ffprobeExecutable = Join-Path $ffmpegBinDirectory 'ffprobe.exe'
$temporaryDirectory = Join-Path ([System.IO.Path]::GetTempPath()) (
    'addsub-ffmpeg-setup-' + [System.Guid]::NewGuid().ToString('N')
)

function Write-Step {
    param([string]$Message)
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Find-UvExecutable {
    $uvCommand = Get-Command uv.exe -ErrorAction SilentlyContinue
    if ($uvCommand) {
        return $uvCommand.Source
    }

    $candidates = @()
    if ($env:USERPROFILE) {
        $candidates += Join-Path $env:USERPROFILE '.local\bin\uv.exe'
        $candidates += Join-Path $env:USERPROFILE '.cargo\bin\uv.exe'
    }

    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            return $candidate
        }
    }
    return $null
}

function Install-Uv {
    $uvExecutable = Find-UvExecutable
    if ($uvExecutable) {
        Write-Host "uv is already available: $uvExecutable"
        return $uvExecutable
    }

    Write-Step 'Installing uv with the official Astral installer'
    $installerPath = Join-Path $temporaryDirectory 'install-uv.ps1'
    Invoke-WebRequest `
        -UseBasicParsing `
        -Uri 'https://astral.sh/uv/install.ps1' `
        -OutFile $installerPath

    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installerPath | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw "The uv installer exited with code $LASTEXITCODE."
    }

    $uvExecutable = Find-UvExecutable
    if (-not $uvExecutable) {
        throw 'uv was installed but could not be located. Open a new terminal and run setup.ps1 again.'
    }
    return $uvExecutable
}

function Find-SevenZipExecutable {
    $sevenZipCommand = Get-Command 7z.exe -ErrorAction SilentlyContinue
    if ($sevenZipCommand) {
        return $sevenZipCommand.Source
    }

    $candidates = @()
    if ($env:ProgramFiles) {
        $candidates += Join-Path $env:ProgramFiles '7-Zip\7z.exe'
    }
    $programFilesX86 = [System.Environment]::GetEnvironmentVariable('ProgramFiles(x86)')
    if ($programFilesX86) {
        $candidates += Join-Path $programFilesX86 '7-Zip\7z.exe'
    }
    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate -PathType Leaf)) {
            return $candidate
        }
    }
    return $null
}

function Install-ProjectFfmpeg {
    if (-not $ForceFfmpeg -and
        (Test-Path -LiteralPath $ffmpegExecutable -PathType Leaf) -and
        (Test-Path -LiteralPath $ffprobeExecutable -PathType Leaf)) {
        Write-Host "Project FFmpeg is already available: $ffmpegExecutable"
        return
    }

    Write-Step 'Downloading the FFmpeg full build for Windows'
    $archivePath = Join-Path $temporaryDirectory 'ffmpeg-release-full.7z'
    $extractDirectory = Join-Path $temporaryDirectory 'ffmpeg-extracted'
    New-Item -ItemType Directory -Path $extractDirectory -Force | Out-Null
    Invoke-WebRequest `
        -UseBasicParsing `
        -Uri 'https://www.gyan.dev/ffmpeg/builds/packages/ffmpeg-9.0.2-full_build.7z' `
        -OutFile $archivePath

    $expectedChecksum = 'f0e46253c70dfe902bac915dfb4224f0cf1b7c6eeab9da2ccc9a5581f9a71b13'
    $actualChecksum = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualChecksum -ne $expectedChecksum) {
        throw 'The FFmpeg archive failed SHA-256 verification.'
    }
    Write-Host 'FFmpeg archive SHA-256 verified.'

    Write-Step 'Extracting FFmpeg'
    $sevenZipExecutable = Find-SevenZipExecutable
    if ($sevenZipExecutable) {
        & $sevenZipExecutable x -y "-o$extractDirectory" $archivePath | Out-Host
    }
    else {
        $tarCommand = Get-Command tar.exe -ErrorAction SilentlyContinue
        if (-not $tarCommand) {
            throw 'FFmpeg uses a .7z archive. Install 7-Zip, then run setup.ps1 again.'
        }
        & $tarCommand.Source -xf $archivePath -C $extractDirectory
    }
    if ($LASTEXITCODE -ne 0) {
        throw "FFmpeg extraction exited with code $LASTEXITCODE. Install 7-Zip and retry if tar cannot extract .7z files."
    }

    $downloadedFfmpeg = Get-ChildItem -LiteralPath $extractDirectory -Filter ffmpeg.exe -File -Recurse |
        Select-Object -First 1
    $downloadedFfprobe = Get-ChildItem -LiteralPath $extractDirectory -Filter ffprobe.exe -File -Recurse |
        Select-Object -First 1
    if (-not $downloadedFfmpeg -or -not $downloadedFfprobe) {
        throw 'The downloaded archive did not contain ffmpeg.exe and ffprobe.exe.'
    }

    New-Item -ItemType Directory -Path $ffmpegBinDirectory -Force | Out-Null
    Copy-Item -LiteralPath $downloadedFfmpeg.FullName -Destination $ffmpegExecutable -Force
    Copy-Item -LiteralPath $downloadedFfprobe.FullName -Destination $ffprobeExecutable -Force

    & $ffmpegExecutable -version | Select-Object -First 1 | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw 'The downloaded ffmpeg.exe could not be started.'
    }
}

New-Item -ItemType Directory -Path $temporaryDirectory -Force | Out-Null
try {
    Install-ProjectFfmpeg
    $uvExecutable = Install-Uv

    Write-Step 'Installing Python dependencies'
    Push-Location $projectDirectory
    try {
        & $uvExecutable sync
        if ($LASTEXITCODE -ne 0) {
            throw "uv sync exited with code $LASTEXITCODE."
        }
    }
    finally {
        Pop-Location
    }

    Write-Step 'Setup complete'
    Write-Host "Open a new terminal, then run the program from this directory with:`n  uv run main.py"
}
finally {
    if (Test-Path -LiteralPath $temporaryDirectory) {
        Remove-Item -LiteralPath $temporaryDirectory -Recurse -Force
    }
}
