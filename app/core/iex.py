import random
from typing import List

class IEXPriceService:
    """
    Mock service for IEX (India Energy Exchange) Real-Time Market prices.
    In production, this would fetch from a real API or scrape IEX website.
    """
    def get_market_prices(self, days: int = 1) -> List[float]:
        """
        Returns electricity prices in ₹/kWh for 96 * days intervals.
        Typically prices are lower at night and higher during peak hours.
        """
        prices = []
        for d in range(days):
            day_prices = []
            for t in range(96):
                hour = (t // 4) % 24
                
                # Base price ₹4 - ₹6
                base = 4.5 + random.uniform(-0.5, 0.5)
                
                # Morning peak (9-12)
                if 9 <= hour <= 12:
                    base += random.uniform(2, 4)
                # Evening peak (18-22)
                elif 18 <= hour <= 22:
                    base += random.uniform(3, 6)
                # Night low (0-5)
                elif 0 <= hour <= 5:
                    base -= random.uniform(1, 2)
                    
                day_prices.append(max(2.5, base))
            prices.extend(day_prices)
        return prices
