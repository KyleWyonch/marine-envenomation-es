# Instructions
## Open Your Work Environment:
- Open two separate terminal (or command prompt) windows—one for the backend and one for the frontend.

## Backend (Python/Flask) Setup:
1. Navigate to the Backend Folder:
Open the first terminal and change the directory to your backend folder.
`cd C:\documents\masters\elg6131-medical-diagnostics-engineering\marine-envenomation-es\backend`
2. Activate the Virtual Environment
`env\Scripts\activate`
3. Install or Update Dependencies
`pip install -r requirements.txt`
4. Start the Flask Server
`python server.py`

## Frontend (React) Setup
1. Navigate to the Frontend Folder:
Open the second terminal and change to your frontend folder:
`cd C:\documents\masters\elg6131-medical-diagnostics-engineering\marine-envenomation-es\frontend`
2. Install or Update Node Dependencies
Run:
`npm install`
This installs (or updates) all the required packages according to your package.json.
3. Ensure Proxy Configuration is Correct:
Verify that your package.json contains a proxy entry (e.g., "proxy": "http://127.0.0.1:5000",) so that API calls from your React app are forwarded to your Flask backend.
4. Start the React Development Server:
Run:
`npm start`