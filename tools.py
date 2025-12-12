import os
import requests
import subprocess
import sys
import io
import contextlib
import traceback

def download_file(url: str, filename: str = None) -> str:
    """
    Downloads a file from a URL.
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        if not filename:
            filename = url.split("/")[-1]
            
        # Ensure we don't overwrite critical files or go outside a temp dir? 
        # For now, just download to current working directory or a 'downloads' folder.
        os.makedirs("downloads", exist_ok=True)
        filepath = os.path.join("downloads", filename)
        
        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return filepath
    except Exception as e:
        return f"Error downloading file: {e}"

def execute_python_code(code: str) -> str:
    """
    Executes Python code and returns stdout/stderr.
    """
    # Create a string buffer to capture stdout
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    try:
        # We will execute the code in a restricted but useful namespace
        # We need to make sure installed packages are available
        
        # Redirect stdout and stderr
        with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
            # Execute the code
            # We use a shared dictionary for locals/globals to persist state if needed, 
            # but for this one-shot execution, a fresh dict is fine.
            # However, if we want to support imports, they work in exec.
            exec(code, {"__name__": "__main__", "download_file": download_file})
            
        output = stdout_capture.getvalue()
        error = stderr_capture.getvalue()
        
        if error:
            return f"Output:\n{output}\nErrors:\n{error}"
        return output if output else "Code executed successfully (no output)."

    except Exception as e:
        return f"Execution Error: {traceback.format_exc()}"
