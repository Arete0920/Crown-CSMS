from pathlib import Path
import runpy

if __name__ == "__main__":
    target = Path(__file__).with_name("print_shell_backend_contract.py")
    runpy.run_path(str(target), run_name="__main__")
