# PowerShell script to start both the backend and frontend servers

# Function to check if a port is in use
function Test-PortInUse {
    param(
        [int]$Port
    )
    
    $connections = netstat -ano | Select-String -Pattern "TCP.*:$Port\s+.*LISTENING"
    return $connections.Count -gt 0
}

# Check if port 5000 is already in use
if (Test-PortInUse -Port 5000) {
    Write-Host "Port 5000 is already in use. The backend server may already be running." -ForegroundColor Yellow
} else {
    # Start the backend server in a new PowerShell window
    Write-Host "Starting backend server on port 5000..." -ForegroundColor Green
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; python api.py"
}

# Wait a moment for the backend to start
Start-Sleep -Seconds 2

# Check if port 3003 is already in use
if (Test-PortInUse -Port 3003) {
    Write-Host "Port 3003 is already in use. The frontend server may already be running." -ForegroundColor Yellow
} else {
    # Start the frontend server in a new PowerShell window
    Write-Host "Starting frontend server on port 3003..." -ForegroundColor Green
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\frontend'; npm start"
}

Write-Host "Servers started. You can access the application at http://localhost:3003" -ForegroundColor Cyan
Write-Host "Press Ctrl+C in the respective windows to stop the servers." -ForegroundColor Cyan 