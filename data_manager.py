
"""
handle data
"""

import sqlite3
import pandas_datareader.data as web
import pandas_market_calendars as mcal
import pandas as pd
from datetime import datetime
import dateutil.parser as du


def process_tiingo(df):
    df.drop(["open", "high", "low", "close", "volume", "divCash", "splitFactor"], axis=1, inplace=True)
    df.rename(lambda x: x.replace("adj", ""), axis=1, inplace=True)


sources = ["stooq", "tiingo"]

source_map = {
    "stooq": [".US", None],
    "tiingo": ["", process_tiingo],
}


class DataManager:
    def __init__(self, sqlite_file):
        self.sqlite_file = sqlite_file

    def __enter__(self):
        try:
            self.conn = sqlite3.connect(self.sqlite_file)
            self.cur = self.conn.cursor()
        except sqlite3.Error as e:
            print(e)
            raise ValueError("Failed to establish connection")

        self.initialize_calendar()
        self.initialize_source_order()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()

    def initialize_calendar(self):
        nyse = mcal.get_calendar("NYSE")
        days = nyse.valid_days(start_date="19900101", end_date=datetime.today())
        self.cur.execute("drop table if exists mcal_US")
        days.to_series(name="Date").to_sql("mcal_US", con=self.conn, index=False)

    def initialize_source_order(self):
        self.conn.execute("drop table if exists source_rank")
        pd.DataFrame({"Source": sources, "Rank": range(len(sources))}).to_sql("source_rank", con=self.conn, index=False)

    def get_data(self, tickers, start_date, end_date):
        # check time input and parse
        if start_date is None:
            raise ValueError("start date cannot be none")
        start_date = du.parse(start_date)
        end_date = datetime.today().date() if end_date is None else du.parse(end_date)

        # check data completeness and download if necessary
        for ticker in tickers:
            if not self.is_ticker_complete(ticker, start_date, end_date):
                for source in sources:
                    self.download_data(ticker, start_date, end_date, source)
                    if self.is_ticker_complete(ticker, start_date, end_date):
                        break
                else:  # no break
                    print(f"WARNING: failed to download complete series: {ticker}")

        return self.read_tickers_from_db(tickers, start_date, end_date)

    def is_ticker_complete(self, ticker, start_date, end_date):
        if not self.table_exist(ticker):
            return False

        count = self.cur.execute(f"""
            select count(*)
            from mcal_US a
            left join {ticker} b
                on a.Date = b.Date
            where a.Date between ? and ?
            and b.Date is null
        """, (start_date, end_date)).fetchone()[0]
        if count > 0:
            print(f"{ticker} missing {count} bar(s)", flush=True)
            return False
        return True

    def table_exist(self, table_name):
        res = self.cur.execute("select name from sqlite_master where type='table' AND name=?", (table_name,))
        return res.fetchone() is not None

    def download_data(self, ticker, start_date, end_date, source=None):
        """
        download and merge data into database
        """
        if source is None:
            source = sources[0]

        suffix, processor = source_map[source]
        data = web.DataReader(ticker + suffix, source, start_date, end_date)
        if processor is not None:
            processor(data)

        print(ticker, " ... downloaded %d bars via %s" % (data.shape[0], source), flush=True)
        self.insert_data(ticker, source, data)

    def insert_data(self, ticker, source, df):
        df["Source"] = source
        if self.table_exist(ticker):
            self.conn.execute("drop table if exists tmp")
            df.to_sql("tmp", con=self.conn, index=True)

            stmt = f"""
                insert into {ticker} (Date, Open, High, Low, Close, Volume, Source)
                select a.Date, a.Open, a.High, a.Low, a.Close, a.Volume, a.Source
                from tmp a left join {ticker} b
                    on a.Date = b.Date
                    and a.Source = b.Source
                where
                    b.Date is null"""
            try:
                with self.conn:
                    self.conn.execute(stmt)
            except sqlite3.IntegrityError:
                print(f"SQL: can't insert new rows to {ticker}")
        else:
            df.to_sql(ticker, con=self.conn, index=True)

    def read_ticker_from_db(self, ticker, start_date, end_date):
        if not isinstance(ticker, str):
            raise ValueError(f"ticker should be string instead of {type(ticker)}")

        stmt = f"""
        with tmp as (
            select a.*, b.rank 
            from {ticker} a inner join source_rank b 
                on a.Source = b.Source
        ) 
        select a.Date, a.Open, a.High, a.Low, a.Close, a.Volume
        from tmp a 
            inner join (
                select Date, min(Rank) as Rank 
                from tmp 
                where Date between '{start_date}' and '{end_date}' 
                group by Date
            ) b 
            on a.Date = b.Date and a.Rank = b.Rank"""
        return pd.read_sql(stmt, con=self.conn, index_col="Date", parse_dates=["Date"])

    def read_tickers_from_db(self, tickers, start_date, end_date):
        data = [self.read_ticker_from_db(ticker, start_date, end_date) for ticker in tickers]
        return pd.concat(data, axis=1, keys=tickers)