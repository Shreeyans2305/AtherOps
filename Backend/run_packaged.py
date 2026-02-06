import sys
import os
import webbrowser
import uvicorn
import multiprocessing
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import Request

# Add the current directory to sys.path so we can import modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Load environment variables explicitly from the executable's directory
# This ensures it works even if CWD is different
from dotenv import load_dotenv

if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

dotenv_path = os.path.join(application_path, '.env')
if os.path.exists(dotenv_path):
    print(f"Loading .env from: {dotenv_path}")
    load_dotenv(dotenv_path)
else:
    print(f"Warning: .env file not found at {dotenv_path}")

# Import the main FastAPI app
# Note: We import after setting up paths and loading env
from main import app

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def configure_app():
    # Path to the frontend build directory (bundled inside the xe)
    # We expect 'dist' to be at the root level of the bundle or in a specific location
    # When packaged, we will bundle Frontend/dist into the root of the temp dir as 'static'
    # or similar. Let's decide on 'static' for simplicity in the spec file.
    static_dir = resource_path("static")
    
    if not os.path.exists(static_dir):
        print(f"Warning: Static directory not found at {static_dir}. Frontend will not be served.")
        return

    # Mount static files (assets, etc.)
    # We mount it at /assets if your vite build puts assets there, 
    # but usually Vite puts assets in dist/assets. 
    # Let's mount the root 'dist' folder to specific path if needed, 
    # or check how we want to serve.
    
    # Typically:
    # /assets -> static/assets
    # / -> index.html
    
    app.mount("/assets", StaticFiles(directory=os.path.join(static_dir, "assets")), name="assets")

    # Catch-all route for SPA (React Router)
    # This must be defined LAST (creation order matches matching order? No, explicit routes match first usually)
    # But to be safe, we add a route that captures everything else not matched.
    # However, FastAPI mounts take precedence over "catch-all" path parameters if defined correctly?
    # Actually, Starlette routing logic: explicit routes first, then mounts?
    # No, usually order matters.
    # But since we have many API routes defined in main.py, they are already attached to 'app'.
    # We are adding this NEW route now.
    
    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        # Check if file exists in static folder (e.g. favicon.ico)
        # If so, serve it.
        file_path = os.path.join(static_dir, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
            
        # Otherwise serve index.html
        index_path = os.path.join(static_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return "Frontend not found", 404

def start_browser():
    """Open the browser after a short delay"""
    webbrowser.open("http://localhost:8000")

if __name__ == "__main__":
    # On Windows, multiprocessing.freeze_support() is needed for PyInstaller
    multiprocessing.freeze_support()
    
    # Configure the app to serve frontend
    configure_app()
    
    # Start the server
    # We don't use reload=True in production
    # Workers=1 is fine for desktop app
    print("Starting AtherOps...")
    
    # Launch browser (optional, maybe configurable?)
    # We'll launch it.
    start_browser()
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
