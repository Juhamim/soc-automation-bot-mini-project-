import sys
import os
import uvicorn

# Force inject the current directory into the python path to guarantee `app` is found
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

if __name__ == "__main__":
    print(f"Booting Uvicorn with forced sys.path: {sys.path[:2]}")
    uvicorn.run("app.api.main:app", host="0.0.0.0", port=8000, log_level="info")
