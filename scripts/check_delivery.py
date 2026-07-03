import subprocess
import sys

COMMANDS = [
    [sys.executable, "-m", "pytest", "-q"],
    [sys.executable, "-m", "ruff", "check", "."],
    [sys.executable, "-m", "mypy", "app"],
    [sys.executable, "-m", "alembic", "history"],
]


def main() -> None:
    for command in COMMANDS:
        print(f"$ {' '.join(command)}")
        subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
