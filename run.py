import os
import sys
import subprocess

def log(msg):
    print(f"\033[94m[*] {msg}\033[0m")

def log_success(msg):
    print(f"\033[92m[+] {msg}\033[0m")

def log_error(msg):
    print(f"\033[91m[-] {msg}\033[0m", file=sys.stderr)

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    venv_dir = os.path.join(base_dir, "venv")
    requirements_file = os.path.join(base_dir, "backend", "requirements.txt")
    
    # Check if virtualenv exists, if not, create it
    if not os.path.exists(venv_dir):
        log("Creating virtual environment...")
        try:
            subprocess.run([sys.executable, "-m", "venv", "venv"], cwd=base_dir, check=True)
            log_success("Virtual environment created.")
        except subprocess.CalledProcessError as e:
            log_error(f"Failed to create virtual environment: {e}")
            sys.exit(1)

    # Determine executable paths
    if sys.platform == "win32":
        pip_path = os.path.join(venv_dir, "Scripts", "pip.exe")
        python_path = os.path.join(venv_dir, "Scripts", "python.exe")
    else:
        pip_path = os.path.join(venv_dir, "bin", "pip")
        python_path = os.path.join(venv_dir, "bin", "python")

    # Install requirements
    log("Checking & installing backend dependencies...")
    try:
        subprocess.run([pip_path, "install", "-r", requirements_file], cwd=base_dir, check=True)
        log_success("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        log_error(f"Failed to install dependencies: {e}")
        sys.exit(1)

    # Seed Database or initialize app structure (if setup command or script exists)
    # We will implement database migrations inside FastAPI startup or via a direct python script.
    
    # Launch uvicorn server
    log("Starting FastAPI server at http://127.0.0.1:8000...")
    try:
        # We run uvicorn through python -m uvicorn so it is cleanly resolved
        subprocess.run([
            python_path, "-m", "uvicorn", 
            "backend.app.main:app", 
            "--reload", 
            "--host", "127.0.0.1", 
            "--port", os.environ.get("PORT", "8000")
        ], cwd=base_dir)
    except KeyboardInterrupt:
        log("\nServer stopped by user.")
    except Exception as e:
        log_error(f"Error starting server: {e}")

if __name__ == "__main__":
    main()
