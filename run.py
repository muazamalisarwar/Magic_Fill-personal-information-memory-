import os
import sys
import subprocess

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(root_dir, "backend")
    
    # Path to virtual environment uvicorn (venv is at project root, not backend/)
    venv_scripts = os.path.join(root_dir, ".venv", "Scripts")
    uvicorn_exe = os.path.join(venv_scripts, "uvicorn.exe")
    
    if not os.path.exists(uvicorn_exe):
        # Fallback to python in .venv
        python_exe = os.path.join(venv_scripts, "python.exe")
        cmd = [python_exe, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"]
    else:
        cmd = [uvicorn_exe, "app.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"]

    print("=" * 50)
    print("  [*] Magic Fill is starting...")
    print("  [*] Web App: http://127.0.0.1:8000/")
    print("=" * 50)
    
    try:
        subprocess.run(cmd, cwd=backend_dir)
    except KeyboardInterrupt:
        print("\nServer stopped.")

if __name__ == "__main__":
    main()
