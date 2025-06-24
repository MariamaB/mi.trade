import os
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.models import Position


load_dotenv()
# Optional: Direkt eintragen zum Debuggen
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

# Alpaca im Paper-Modus
client = TradingClient(API_KEY, API_SECRET, paper=True)

def check_all_positions():
    print("[TEST] Prüfe offene Positionen im Paper-Konto...")

    try:
        positions = client.get_all_positions()
        if positions:
            print(f"[INFO] Es wurden {len(positions)} Position(en) gefunden:")
            for p in positions:
                print(f" - {p.symbol}: {p.qty} Stück @ {p.avg_entry_price} ({p.side})")
        else:
            print("[INFO] Keine offenen Positionen gefunden.")
    except Exception as e:
        print(f"[FEHLER] Konnte Positionen nicht abrufen: {e}")

def check_single_position(symbol="TSLA"):
    print(f"\n[TEST] Prüfe Position für Symbol: {symbol}")
    try:
        position: Position = client.get_open_position(symbol)
        print(f"[INFO] {symbol}: {position.qty} Stück @ {position.avg_entry_price} ({position.side})")
    except Exception as e:
        print(f"[FEHLER] Keine offene Position für {symbol} gefunden oder Fehler: {e}")


if __name__ == "__main__":
    try:
        account = client.get_account()
        print(f"[OK] Erfolgreich verbunden mit Konto: {account.account_number}")
        print(f"- Status: {account.status}")
        print(f"- Kontostand: {account.cash} USD")
        print(f"- Buying Power: {account.buying_power} USD")
        print(f"- Equity: {account.equity} USD")
        print(f"- Kontoart: {'Paper' if client.paper else 'Live'}")
    except Exception as e:
        print(f"[FEHLER] Konnte Account-Infos nicht abrufen: {e}")
    check_all_positions()
    check_single_position("TSLA")
