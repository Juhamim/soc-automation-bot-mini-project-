import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.tasks import generate_and_send_report

if __name__ == "__main__":
    result = generate_and_send_report(timeframe="End-to-End Test", hours=48)
    print(result)
