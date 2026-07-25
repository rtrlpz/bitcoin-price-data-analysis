import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()
VENV_DIR = PROJECT_ROOT / "price-analysis"
REQUIREMENTS = PROJECT_ROOT / "requirements.txt"

# Prefer Anaconda Python if available (it has most packages pre-cached)
_ANACONDA_PYTHON = r"C:\ProgramData\anaconda3\python.exe"


def _python():
    if os.path.isfile(_ANACONDA_PYTHON):
        return _ANACONDA_PYTHON
    return sys.executable


def _venv_python():
    if sys.platform == "win32":
        return str(VENV_DIR / "Scripts" / "python.exe")
    return str(VENV_DIR / "bin" / "python")


def _venv_exists():
    py = _venv_python()
    return os.path.isfile(py)


def _prompt_yes_no(question: str) -> bool:
    while True:
        answer = input(f"{question} [Y/n] ").strip().lower()
        if answer in ("", "y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("Please answer 'y' or 'n'.")


def _create_venv():
    py = _python()
    print(f"\nCreating virtual environment using {py}...")
    result = subprocess.run(
        [py, "-m", "venv", str(VENV_DIR)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"Error creating venv: {result.stderr}")
        sys.exit(1)
    print("Virtual environment created.")


def _install_deps():
    print("Installing dependencies (this may take a few minutes)...")
    result = subprocess.run(
        [_venv_python(), "-m", "pip", "install", "-r", str(REQUIREMENTS)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"Error installing dependencies: {result.stderr}")
        sys.exit(1)
    print("Dependencies installed.")


def _nltk_download():
    print("Downloading NLTK sentiment lexicon...")
    result = subprocess.run(
        [_venv_python(), "-c", (
            "import nltk; "
            "nltk.download('vader_lexicon', quiet=True); "
            "print('OK')"
        )],
        capture_output=True, text=True,
    )
    if result.returncode != 0 or "OK" not in result.stdout:
        print("Warning: NLTK lexicon download failed — sentiment scoring will be disabled.")


def _launch():
    print("\nStarting Quant Trading Dashboard...")
    cmd = [_venv_python(), "-m", "streamlit", "run", "quant_tool/app.py"]
    subprocess.run(cmd)


def main():
    os.chdir(PROJECT_ROOT)

    if not REQUIREMENTS.exists():
        print(f"Error: {REQUIREMENTS} not found.")
        sys.exit(1)

    if not _venv_exists():
        print("No virtual environment found.")
        if _prompt_yes_no("Create one and install all dependencies?"):
            _create_venv()
            _install_deps()
            _nltk_download()
            _launch()
        else:
            print("\nManual setup instructions:")
            print(f"  python -m venv price-analysis")
            if sys.platform == "win32":
                print("  price-analysis\\Scripts\\activate")
            else:
                print("  source price-analysis/bin/activate")
            print("  pip install -r requirements.txt")
            print("  streamlit run quant_tool/app.py")
    else:
        _launch()


if __name__ == "__main__":
    main()
