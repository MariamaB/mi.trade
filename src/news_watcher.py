import threading
import time
from datetime import datetime

from helper.finbert_utils import estimate_sentiment


class NewsWatcher(threading.Thread):
    def __init__(self, trader, interval=300):  # 5 Minuten
        super().__init__()
        self.trader = trader
        self.interval = interval
        self.running = True
        self.last_headlines = set()

    def run(self):
        while self.running:
            try:
                headlines = set(self.trader.get_newsapi_headlines("Tesla"))
                if headlines != self.last_headlines:
                    print(f"[🔔] Neue News erkannt!")
                    prob, sentiment = estimate_sentiment(list(headlines))
                    self.trader.cached_sentiment = (prob.item(), sentiment)
                    self.trader.last_news_update = datetime.utcnow()
                    self.last_headlines = headlines
            except Exception as e:
                print(f"[ERROR] NewsWatcher: {e}")
            time.sleep(self.interval)

    def stop(self):
        self.running = False
