Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.IO.Compression.FileSystem

$installPath = "$env:USERPROFILE\Gandiva"

Write-Host "Gandiva Installer - RHEED Growth Analysis" -ForegroundColor Cyan
Write-Host "by Hume Nano" -ForegroundColor Gray
Write-Host ""

try {
    Write-Host "Downloading Gandiva from GitHub..." -ForegroundColor Yellow
    
    $zipUrl = "https://github.com/rolypolytoy/gandiva/archive/refs/heads/main.zip"
    $zipPath = "$env:TEMP\gandiva.zip"
    $extractPath = "$env:TEMP\gandiva_extract"
    
    Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath -UseBasicParsing
    
    if (Test-Path $installPath) {
        Write-Host "Removing existing installation..." -ForegroundColor Yellow
        Remove-Item $installPath -Recurse -Force
    }
    
    Write-Host "Extracting files..." -ForegroundColor Yellow
    
    if (Test-Path $extractPath) {
        Remove-Item $extractPath -Recurse -Force
    }
    
    [System.IO.Compression.ZipFile]::ExtractToDirectory($zipPath, $extractPath)
    
    $sourceFolder = Get-ChildItem $extractPath | Where-Object { $_.Name -like "gandiva-*" } | Select-Object -First 1
    
    if ($sourceFolder) {
        Move-Item $sourceFolder.FullName $installPath
    } else {
        throw "Could not find extracted folder"
    }
    
    Write-Host "Creating desktop shortcut..." -ForegroundColor Yellow
    
    $desktopPath = [Environment]::GetFolderPath("Desktop")
    $shortcutPath = "$desktopPath\Gandiva.lnk"
    $targetPath = "$installPath\Gandiva.bat"
    $iconPath = "$installPath\Gandiva.ico"
    
    $WshShell = New-Object -comObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut($shortcutPath)
    $Shortcut.TargetPath = $targetPath
    $Shortcut.WorkingDirectory = $installPath
    $Shortcut.Description = "Gandiva - RHEED Growth Analysis"
    
    if (Test-Path $iconPath) {
        $Shortcut.IconLocation = $iconPath
    }
    
    $Shortcut.Save()
    
    Write-Host "Creating Start Menu shortcut..." -ForegroundColor Yellow
    
    $startMenuPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs"
    $startShortcutPath = "$startMenuPath\Gandiva.lnk"
    
    $StartShortcut = $WshShell.CreateShortcut($startShortcutPath)
    $StartShortcut.TargetPath = $targetPath
    $StartShortcut.WorkingDirectory = $installPath
    $StartShortcut.Description = "Gandiva - RHEED Growth Analysis"
    
    if (Test-Path $iconPath) {
        $StartShortcut.IconLocation = $iconPath
    }
    
    $StartShortcut.Save()
    
    Write-Host "Cleaning up..." -ForegroundColor Yellow
    Remove-Item $zipPath -Force -ErrorAction SilentlyContinue
    Remove-Item $extractPath -Recurse -Force -ErrorAction SilentlyContinue
    
    Write-Host ""
    Write-Host "Installation Complete!" -ForegroundColor Green
    Write-Host "Gandiva has been installed to: $installPath" -ForegroundColor White
    Write-Host "Desktop shortcut created: Gandiva" -ForegroundColor White
    Write-Host "Start Menu shortcut created" -ForegroundColor White
    Write-Host ""
    Write-Host "Launching Gandiva..." -ForegroundColor Cyan
    
    Start-Process $targetPath -WorkingDirectory $installPath
    
} catch {
    Write-Host ""
    Write-Host "Installation failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Please check your internet connection and try again." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")