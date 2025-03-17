Write-Output "Starting Backend and Frontend Setup..."

Start-Process powershell -ArgumentList "-NoExit", "-Command cd 'C:\documents\masters\elg6131-medical-diagnostics-engineering\marine-envenomation-es\backend'; .\env\Scripts\activate; pip install -r requirements.txt; python server.py"

Start-Sleep -Seconds 5  # Wait for backend to start

Start-Process powershell -ArgumentList "-NoExit", "-Command cd 'C:\documents\masters\elg6131-medical-diagnostics-engineering\marine-envenomation-es\frontend'; npm install; npm start"

Write-Output "Backend and Frontend have been started!"