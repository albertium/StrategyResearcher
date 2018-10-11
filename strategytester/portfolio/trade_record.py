
class Datum:
    def __init__(self, quantity, price):
        self.quantity = quantity
        self.price = price
        self.mtm = quantity * price

    def __add__(self, other):
        return self.mtm + other.mtm

    def __radd__(self, other):
        return self.mtm + other

    def __str__(self):
        return f'qty: {self.quantity}  price: {self.price: .2f}  mtm: {self.mtm: .2f}'

    def __repr__(self):
        return self.__str__()


class TradeRecord:
    def __init__(self, initial_capital, tickers):
        self.cash = initial_capital
        self.tickers = tickers
        self.positions = {ticker: 0 for ticker in tickers}
        self.commissions = {ticker: 0 for ticker in tickers}
        self.snapshots = []
        self.take_snapshot(-1, {ticker: 0 for ticker in tickers})

    def __str__(self):
        if len(self.snapshots) == 0:
            return f"Total: {self.cash}"
        last_rec = self.snapshots[-1]
        expr = "SNAPSHOT\n"
        expr += f"Timestamp: {last_rec['timestamp']} Total: {last_rec['total']} Commissions: {last_rec['commission']}\n"
        expr += "\n".join([f"{k}: {v.quantity}" for k, v in last_rec['asset'].items() if v.quantity != 0])
        return expr

    def __repr__(self):
        return self.__str__()

    def __getitem__(self, item):
        return self.positions[item]

    def update(self, ticker, quantity, price, commission):
        delta = quantity * price
        if delta > self.cash:
            raise ValueError('Cash become negative')
        self.positions[ticker] += quantity
        self.cash -= delta
        self.commissions[ticker] += commission

    def get_total_holding(self):
        return self.snapshots[-1]["total"]

    def take_snapshot(self, timestamp, prices):
        # snapshot of market values
        record = {
            'asset': {ticker: Datum(self.positions[ticker], prices[ticker]) for ticker in self.tickers},
            'commission': sum(self.commissions.values()),
            'timestamp': timestamp
        }
        record['cash'] = self.cash - record['commission']
        record['total'] = sum(record['asset'].values()) + record['cash']
        self.snapshots.append(record)
