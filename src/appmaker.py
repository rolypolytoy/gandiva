import subprocess
import sys

def build_executable():
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--windowed",
        "--icon=Gandiva.ico", 
        "--name=Gandiva",
        "--exclude-module=tensorflow",
        "--exclude-module=pandas", 
        "--exclude-module=pytest",
        "--exclude-module=sphinx",
        "--exclude-module=numba",
        "--exclude-module=sqlalchemy",
        "--add-data=Gandiva.png;.",
        "--add-data=Gandiva.mp3;.",
        "--add-data=Gandiva.ico;.",
        "gandiva.py"
    ]
    
    subprocess.run(cmd)

if __name__ == "__main__":
    build_executable()