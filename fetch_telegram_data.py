import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from src.agent.telegram_agent import TelegramAgent

def main():
    print("=" * 60)
    print("OBTENIENDO DATOS DE TELEGRAM")
    print("=" * 60)
    agent = TelegramAgent()
    agent.run_once()
    print("\nVerifica: http://localhost:5000")

if __name__ == "__main__":
    main()