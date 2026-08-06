# Startet den Node-Server gegen den Raspberry Pi an der Direktverbindung.
#
#   .\start-pi.ps1
#
# Hintergrund: $env:... gilt immer nur fuer das aktuelle PowerShell-Fenster.
# Nach jedem Neustart oder in jedem neuen Fenster waere die Variable sonst
# wieder leer und der Server liefe im Demobetrieb.

$PiIp     = "192.168.10.1"
$PiUrl    = "http://${PiIp}:5000"
$Adapter  = "Ethernet 2"
$LocalIp  = "192.168.10.2"

# --- 1. Eigene Adresse am Kabel -----------------------------------
# Bei USB-Netzwerkadaptern geht die feste Adresse nach dem Ab- und
# Anstecken gern verloren. Ohne sie kennt Windows keine Route zum Pi
# und schickt die Pakete ueber die Standardroute ins WLAN.
$eigene = Get-NetIPAddress -InterfaceAlias $Adapter -AddressFamily IPv4 -ErrorAction SilentlyContinue |
          Where-Object { $_.IPAddress -eq $LocalIp }

if (-not $eigene) {
    Write-Host "Dem Adapter '$Adapter' fehlt die Adresse $LocalIp." -ForegroundColor Red
    Write-Host "In einem PowerShell-Fenster ALS ADMINISTRATOR ausfuehren:" -ForegroundColor Yellow
    Write-Host "  Set-NetIPInterface -InterfaceAlias '$Adapter' -Dhcp Disabled"
    Write-Host "  New-NetIPAddress -InterfaceAlias '$Adapter' -IPAddress $LocalIp -PrefixLength 24"
    Write-Host ""
}

# --- 2. Erreichbarkeit des Pi -------------------------------------
Write-Host "Pruefe Pi-API unter $PiUrl ..." -ForegroundColor Cyan
$test = Test-NetConnection -ComputerName $PiIp -Port 5000 -WarningAction SilentlyContinue

if ($test.TcpTestSucceeded) {
    Write-Host "Pi erreichbar." -ForegroundColor Green
    $env:PI_API_BASE_URL = $PiUrl
} else {
    Write-Host "Pi nicht erreichbar (Route lief ueber: $($test.InterfaceAlias))." -ForegroundColor Red
    Write-Host ""
    Write-Host "Steht dort 'WiFi' statt '$Adapter', fehlt die Adresse aus Schritt 1." -ForegroundColor Yellow
    Write-Host "Sonst auf dem Pi pruefen:" -ForegroundColor Yellow
    Write-Host "  hostname -I              -> muss $PiIp enthalten"
    Write-Host "  ps aux | grep hydroponik -> laeuft das Messprogramm?"
    Write-Host ""
    $weiter = Read-Host "Trotzdem im Demobetrieb starten? (j/n)"
    if ($weiter -ne "j") { exit 1 }
    Write-Host "Starte ohne Pi - Daten per Simulator erwartet." -ForegroundColor Yellow
}

npm start
