"""Run the local model API and Vite frontend together; stop both on exit."""

from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = Path(__file__).resolve().parent
WEB_PORT = 5174


def wait_for(url: str, process: subprocess.Popen, label: str) -> None:
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"{label} stopped before becoming ready (exit {process.returncode}).")
        try:
            with urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except (URLError, TimeoutError, OSError):
            time.sleep(0.25)
    raise TimeoutError(f"{label} did not become ready at {url}.")


def main() -> int:
    npm = shutil.which("npm.cmd") if sys.platform == "win32" else shutil.which("npm")
    if not npm:
        raise RuntimeError("Node.js and npm are required. Install Node.js 20 or newer.")

    processes: list[subprocess.Popen] = []
    try:
        api = subprocess.Popen(
            [sys.executable, "-B", str(FRONTEND / "api" / "server.py")],
            cwd=ROOT,
        )
        processes.append(api)
        wait_for("http://127.0.0.1:8765/api/health", api, "Python model API")

        web_command = f'"{npm}" run dev -- --port {WEB_PORT} --strictPort'
        web = subprocess.Popen(
            web_command if sys.platform == "win32" else
            [npm, "run", "dev", "--", "--port", str(WEB_PORT), "--strictPort"],
            cwd=FRONTEND,
            shell=sys.platform == "win32",
            creationflags=(
                subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
            ),
        )
        processes.append(web)
        wait_for(f"http://127.0.0.1:{WEB_PORT}/", web, "Vite frontend")
        print(f"Habitat 2050 React frontend: http://127.0.0.1:{WEB_PORT}/")
        print("Press Ctrl+C to stop the frontend and local API.")

        while all(process.poll() is None for process in processes):
            time.sleep(0.5)
        failed = [process for process in processes if process.returncode not in (None, 0)]
        if failed:
            return failed[0].returncode or 1
        return 0
    except KeyboardInterrupt:
        return 0
    finally:
        for process in reversed(processes):
            if process.poll() is None:
                if sys.platform == "win32":
                    process.send_signal(signal.CTRL_BREAK_EVENT)
                else:
                    process.terminate()
        for process in reversed(processes):
            if process.poll() is None:
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


if __name__ == "__main__":
    raise SystemExit(main())
