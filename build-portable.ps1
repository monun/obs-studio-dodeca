#Requires -Version 5.1
<#
.SYNOPSIS
Build OBS Studio Dodeca and create a verified Windows x64 portable ZIP.
.DESCRIPTION
Requires Git, CMake 4.2+, Visual Studio 2026 with Desktop development with C++,
and Windows SDK 10.0.26100.0. Reuses build_x64 and installs into a new folder
under build_x64/portable on each run. ZIPs and SHA-256 files go into artifacts.
.PARAMETER Parallel
Maximum parallel MSBuild projects and compiler processes per project.
.PARAMETER CMakePath
CMake executable. Defaults to cmake on PATH, then the existing build cache.
.EXAMPLE
.\build-portable.ps1
.EXAMPLE
.\build-portable.ps1 -Parallel 4 -CMakePath 'C:\Program Files\CMake\bin\cmake.exe'
#>
[CmdletBinding()]
param(
	[ValidateRange(1, 256)]
	[int] $Parallel = 2,
	[string] $CMakePath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Invoke-Checked {
	param([string] $FilePath, [string[]] $ArgumentList)

	# A direct pipeline also waits for GUI executables and captures their stdout.
	& $FilePath @ArgumentList | ForEach-Object { $_ }
	if ($LASTEXITCODE -ne 0) {
		throw "$FilePath failed with exit code $LASTEXITCODE."
	}
}

if ($env:OS -ne 'Windows_NT' -or -not [Environment]::Is64BitOperatingSystem) {
	throw 'This script requires 64-bit Windows.'
}

$repoRoot = $PSScriptRoot
$buildDir = Join-Path $repoRoot 'build_x64'
$obsVersion = '32.2.2-dodeca'
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
$installDir = Join-Path $buildDir "portable/$stamp"
$artifactDir = Join-Path $repoRoot 'artifacts'
$packageName = "obs-studio-$obsVersion-windows-x64-portable-$stamp"
$zipPath = Join-Path $artifactDir "$packageName.zip"
$pendingZipPath = Join-Path $artifactDir "$packageName.partial.zip"

if (-not $CMakePath) {
	$cmakeCommand = Get-Command cmake -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
	if ($cmakeCommand) {
		$CMakePath = $cmakeCommand.Source
	} else {
		$cachePath = Join-Path $buildDir 'CMakeCache.txt'
		if (Test-Path -LiteralPath $cachePath -PathType Leaf) {
			$cachedCommand = Select-String -LiteralPath $cachePath -Pattern '^CMAKE_COMMAND:INTERNAL=(.+)$'
			if ($cachedCommand) {
				$CMakePath = $cachedCommand.Matches[0].Groups[1].Value
			}
		}
	}
}
if (-not $CMakePath) {
	throw 'Install CMake 4.2+ on PATH or pass -CMakePath with its executable path.'
}
$cmake = (Get-Command $CMakePath -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source
$git = (Get-Command git -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source
$cmakeVersion = (Invoke-Checked $cmake @('--version')) -join "`n"
if ($cmakeVersion -notmatch 'cmake version (\d+\.\d+\.\d+)' -or [version] $Matches[1] -lt [version] '4.2.0') {
	throw "CMake 4.2+ is required. Found: $cmakeVersion"
}

Push-Location -LiteralPath $repoRoot
try {
	Write-Host '[1/6] Updating submodules...'
	Invoke-Checked $git @('submodule', 'update', '--init', '--recursive')

	# A new installation prevents stale plugins and user settings entering the ZIP.
	if (Test-Path -LiteralPath $installDir) {
		throw "Installation directory already exists: $installDir"
	}
	New-Item -ItemType Directory -Path $installDir | Out-Null
	New-Item -ItemType Directory -Path $artifactDir -Force | Out-Null

	Write-Host '[2/6] Configuring windows-x64...'
	$configureArgs = @(
		'--preset', 'windows-x64'
		"-DOBS_VERSION_OVERRIDE=$obsVersion"
		'-DENABLE_FRONTEND=ON'
		'-DENABLE_AUDIO_TRACK_TESTS=OFF'
		'-DENABLE_TEST_INPUT=OFF'
		"-DCMAKE_INSTALL_PREFIX=$($installDir.Replace('\', '/'))"
	)
	Invoke-Checked $cmake $configureArgs

	Write-Host '[3/6] Building RelWithDebInfo...'
	Invoke-Checked $cmake @(
		'--build', '--preset', 'windows-x64', '--parallel', "$Parallel"
		'--', '/nodeReuse:false', "/p:CL_MPCount=$Parallel"
	)

	Write-Host '[4/6] Installing portable files...'
	Invoke-Checked $cmake @('--install', $buildDir, '--config', 'RelWithDebInfo', '--prefix', $installDir)
	foreach ($directory in @('bin', 'data', 'obs-plugins')) {
		if (-not (Test-Path -LiteralPath (Join-Path $installDir $directory) -PathType Container)) {
			throw "Missing runtime directory: $directory"
		}
	}
	$obsExe = Join-Path $installDir 'bin/64bit/obs64.exe'
	if (-not (Test-Path -LiteralPath $obsExe -PathType Leaf)) {
		throw "Missing OBS executable: $obsExe"
	}
	$markerPath = Join-Path $installDir 'portable_mode.txt'
	$launcherPath = Join-Path $installDir 'Start-OBS.bat'
	[IO.File]::WriteAllText($markerPath, '', [Text.Encoding]::ASCII)
	$launcher = "@echo off`r`ncd /d `"%~dp0bin\64bit`"`r`nstart `"`" `"obs64.exe`" --portable`r`n"
	[IO.File]::WriteAllText($launcherPath, $launcher, [Text.Encoding]::ASCII)

	Write-Host '[5/6] Checking OBS portable version...'
	$savedPath = $env:PATH
	try {
		# Do not let development DLLs on PATH hide missing runtime dependencies.
		$env:PATH = "$(Split-Path -Parent $obsExe);$env:SystemRoot\System32;$env:SystemRoot"
		$obsVersionOutput = (Invoke-Checked $obsExe @('--portable', '--version')) -join "`n"
		if ($obsVersionOutput -notlike "*$obsVersion*") {
			throw "Unexpected OBS version: $obsVersionOutput"
		}
		Write-Host $obsVersionOutput
	} finally {
		$env:PATH = $savedPath
	}

	Write-Host '[6/6] Creating and verifying portable ZIP...'
	Add-Type -AssemblyName System.IO.Compression, System.IO.Compression.FileSystem
	$files = @(
		foreach ($directory in @('bin', 'data', 'obs-plugins')) {
			Get-ChildItem -LiteralPath (Join-Path $installDir $directory) -File -Recurse -Force |
				Where-Object { $_.Extension -ne '.pdb' }
		}
		Get-Item -LiteralPath $markerPath, $launcherPath
	)
	$expectedHashes = @{}
	$archive = [IO.Compression.ZipFile]::Open($pendingZipPath, [IO.Compression.ZipArchiveMode]::Create)
	try {
		foreach ($file in $files) {
			$entryName = $file.FullName.Substring($installDir.Length + 1).Replace('\', '/')
			$expectedHashes[$entryName] = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
			[IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
				$archive, $file.FullName, $entryName, [IO.Compression.CompressionLevel]::Optimal
			) | Out-Null
		}
	} finally {
		$archive.Dispose()
	}

	$archive = [IO.Compression.ZipFile]::OpenRead($pendingZipPath)
	try {
		if ($archive.Entries.Count -ne $files.Count) {
			throw 'ZIP entry count does not match the installation.'
		}
		foreach ($entry in $archive.Entries) {
			$stream = $entry.Open()
			try {
				$actualHash = (Get-FileHash -InputStream $stream -Algorithm SHA256).Hash
				if ($actualHash -ne $expectedHashes[$entry.FullName]) {
					throw "ZIP content verification failed: $($entry.FullName)"
				}
			} finally {
				$stream.Dispose()
			}
		}
	} finally {
		$archive.Dispose()
	}

	Move-Item -LiteralPath $pendingZipPath -Destination $zipPath
	$digest = (Get-FileHash -LiteralPath $zipPath -Algorithm SHA256).Hash.ToLowerInvariant()
	[IO.File]::WriteAllText("$zipPath.sha256", "$digest  $packageName.zip`n", [Text.Encoding]::ASCII)
	Write-Host "Portable folder: $installDir"
	Write-Host "ZIP: $zipPath"
	Write-Host "SHA-256: $zipPath.sha256"
	Write-Host 'ZIP contents and OBS version verified. GUI and recording checks are separate.'
} finally {
	Pop-Location
}
