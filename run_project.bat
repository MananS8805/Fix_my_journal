# Windows (cmd) commands to run the project
# Copy/paste this entire file into a CMD prompt, or save as .bat and run.

cd /d "c:\Users\manan\Desktop\New folder"
python -m pip install -r requirements.txt

start "backend" cmd /k "cd /d c:\Users\manan\Desktop\New folder\backend && python -m uvicorn main:app --reload --port 8001"
start "frontend" cmd /k "cd /d c:\Users\manan\Desktop\New folder\frontend && npm.cmd install && npm.cmd start"
