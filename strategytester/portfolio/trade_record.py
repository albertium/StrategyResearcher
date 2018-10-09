
class TradeRecord:
    def __init__(self, initial_capital, tickers):
        self.cash = initial_capital
        self.positions = {ticker: 0 for ticker in tickers}
        self.commissions = {ticker: 0 for ticker in tickers}
        self.snapshots = []
        self.position_snapshots = []

    def __str__(self):
        if len(self.snapshots) == 0:
            return f"Total: {self.cash}"
        last_rec = self.snapshots[-1]
        expr = f"Timestamp: {last_rec['timestamp']} Total: {last_rec['total']} Commissions: {last_rec['commission']}\n"
        last_rec = self.position_snapshots[-1]
        expr += "\n".join([f"{k}: {v}" for k, v in last_rec.items()])
        return expr

    def __repr__(self):
        return self.__str__()

    def __getitem__(self, item):
        return self.positions[item]

    def update(self, ticker, quantity, price, commission):
        self.positions[ticker] += quantity
        self.cash -= quantity * price
        self.commissions[ticker] += commission

    def get_total_holding(self):
        return self.snapshots[-1]["total"]

    def take_snapshot(self, timestamp, prices):
        # snapshot of market values
        record = {ticker: self.positions[ticker] * prices[ticker] for ticker in self.positions.keys()}
        record["total"] = sum(record.values()) + self.cash
        record["commission"] = sum(self.commissions.values())
        record["cash"] = self.cash - record["commission"]
        record["timestamp"] = timestamp
        self.snapshots.append(record)

        # snapshot of positions
        record = self.positions.copy()
        record["timestamp"] = timestamp
        self.position_snapshots.append(record)
