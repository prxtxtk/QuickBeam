@echo off
setlocal EnableExtensions

rem --- Re-launch elevated if we are not already administrator ---
net session >nul 2>&1
if not "%errorlevel%"=="0" (
    echo Requesting administrator permission...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

echo Adding Windows Firewall rule for QuickBeam (TCP 8080-8090, any profile)...
netsh advfirewall firewall delete rule name="QuickBeam Bridge" >nul 2>&1
netsh advfirewall firewall add rule name="QuickBeam Bridge" dir=in action=allow protocol=TCP localport=8080-8090 profile=any
if errorlevel 1 (
    echo [X] Could not add the firewall rule.
    pause
    exit /b 1
)

rem Remove any leftover block rules that Windows created for the QuickBeam EXEs.
powershell -NoProfile -Command "Get-NetFirewallRule -ErrorAction SilentlyContinue | Where-Object { $_.DisplayName -like '*quickbeam*' -and $_.DisplayName -ne 'QuickBeam Bridge' -and $_.Action -eq 'Block' } | Remove-NetFirewallRule -ErrorAction SilentlyContinue"

echo.
echo Done. Now restart QuickBeam (QuickBeam.cmd) and reload the page on your phone.
echo If it still fails, disable any VPN on the phone and check the hotspot's client isolation.
echo.
pause
