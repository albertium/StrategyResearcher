
"""
handle data
"""

import sqlite3
import pandas_datareader.data as web
from pandas_datareader.stooq import StooqDailyReader
import pandas_market_calendars as mcal
import pandas as pd
from strategytester.utils import rdate, parse_time


def process_tiingo(df):
    df.reset_index(level=0, drop=True, inplace=True)
    df.drop(["open", "high", "low", "close", "volume", "divCash", "splitFactor"], axis=1, inplace=True)
    df.rename(lambda x: x.replace("adj", ""), axis=1, inplace=True)


source_map = {
    "tiingo": ["", None, process_tiingo],
    "stooq": [".US", None, None],
    "av-daily": ["", None, None],
    "iex": ["", rdate("5y"), None]
}


class DataManager:
    def __init__(self, sqlite_file):
        self.sqlite_file = sqlite_file
        self.epoch = pd.Timestamp(1970, 2, 19)

    def __enter__(self):
        try:
            self.conn = sqlite3.connect(self.sqlite_file)
            self.cur = self.conn.cursor()
            self.sources = self._get_list_from_db("SourceRank", "source")
            if set(self.sources) != set(source_map.keys()):
                raise ValueError("sources and source_map doesn't match")

        except sqlite3.Error as e:
            print(e)
            raise ValueError("Failed to establish connection")

        self._update_calendar()
        self._ensure_trial_table()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()

    def get_data(self, tickers, start_date, end_date=None):
        # check time input and parse
        start_date = pd.Timestamp(start_date)
        end_date = pd.Timestamp.today().date() if end_date is None else pd.Timestamp(end_date)

        # create table if needed and update
        for ticker in tickers:
            self._create_ticker_table(ticker)
            for source in self.sources:
                try:
                    self._update_data_from_web(ticker, source)
                except Exception as e:
                    print(e)
                    print(f"Failed to retrieve {ticker} from {source}")
            print(f"Done updating {ticker}\n")

        return self._read_tickers_from_db(tickers, start_date, end_date)

    def _table_exists(self, table_name):
        res = self.cur.execute("select name from sqlite_master where type='table' AND name=?", (table_name,))
        return res.fetchone() is not None

    def _get_last_date_from_db(self, table, source=None):
        if source is None:
            tmp = pd.read_sql(f'select max(date) as date from {table}', con=self.conn, parse_dates=["date"]).loc[0][0]
        else:
            tmp = pd.read_sql(f"select max(date) as date from {table} where source = '{source}'",
                              con=self.conn, parse_dates=["date"]).loc[0][0]
        if tmp is pd.NaT:
            return self.epoch
        return tmp

    def _get_list_from_db(self, table, name):
        tmp = self.cur.execute(f"select {name} from {table}").fetchall()
        return [x[0] for x in tmp]

    def _create_ticker_table(self, ticker):
        self.conn.execute(f"""
            create table if not exists {ticker} (
                date timestamp,
                open real,
                high real,
                low real,
                close real,
                volume integer,
                source text,
                primary key(date, source)
            )
        """)
        self.conn.commit()

    def _update_calendar(self):
        mcal_name = 'MarketCalendarUS'

        # create if not exists
        self.conn.execute(f'create table if not exists {mcal_name} (date timestamp primary key)')
        self.conn.commit()

        last_date = self._get_last_date_from_db(mcal_name)
        if last_date is None:
            last_date = self.epoch

        # get market dates and insert if needed
        nyse = mcal.get_calendar("NYSE")
        dates = nyse.valid_days(start_date=last_date + rdate("1b"), end_date=pd.Timestamp.today())
        if len(dates) > 0:  # term
            dates.to_series(name="date").to_sql(mcal_name, con=self.conn, index=False, if_exists="append")

    def _ensure_trial_table(self):
        self.conn.execute('''
            create table if not exists trials (
                ticker text,
                source text,
                count integer default 0,
                primary key(ticker, source)
            )
        ''')
        self.conn.commit()

    def _get_number_of_trials(self, ticker, source):
        self.cur.execute(f"select count from trials where ticker = '{ticker}' and source = '{source}'")
        res = self.cur.fetchone()
        if res is None:
            self.conn.execute("insert into trials (ticker, source, count) values(?, ?, ?)", (ticker, source, 0))
            self.conn.commit()
            return 0
        return res[0]

    def _increment_trial_count(self, ticker, source):
        self.conn.execute(f"update trials set count = count + 1 where ticker = '{ticker}' and source = '{source}'")
        self.conn.commit()

    def _update_data_from_web(self, ticker, source) -> None:
        """
        download and merge data into database
        start date is the last updated date + 1 and end date is today
        """

        # check if source is available for the ticker
        if self._get_number_of_trials(ticker, source) > 3:
            print(f'{ticker} from {source} is skipped', flush=True)
            return
        suffix, relative_limit, processor = source_map[source]

        # configure start, end dates
        today = pd.Timestamp.today() - rdate("1b")
        start_date = self._get_last_date_from_db(ticker, source) + rdate("1b")
        if relative_limit is not None and start_date < today - relative_limit:
            start_date = today - relative_limit
        end_date = today

        # check date
        if start_date > end_date:
            return

        # download data and pre-process if needed
        if source == "stooq":
            data = StooqDailyReader(ticker + suffix, start_date, end_date).read()
            if data.shape[0] == 0:
                self._increment_trial_count(ticker, source)
                return
        else:
            try:
                data = web.DataReader(ticker + suffix, source, start_date, end_date)
            except KeyError:
                self._increment_trial_count(ticker, source)
                return
        if processor is not None:
            processor(data)
        data.index = data.index.astype("datetime64[ns]")  # for some sources, string can be return

        sdate, edate = parse_time(data.index.min()), parse_time(data.index.max())
        print(f"Downloaded {ticker} from {sdate.date()} to {edate.date()} totally {data.shape[0]:d} bars via {source}",
              flush=True)
        data["source"] = source
        data.to_sql(ticker, con=self.conn, index=True, index_label="date", if_exists="append")

    def _read_ticker_from_db(self, ticker, start_date, end_date):
        if not isinstance(ticker, str):
            raise ValueError(f"ticker should be string instead of {type(ticker)}")

        stmt = f"""
        with tmp as (
            select a.*, b.rank 
            from {ticker} a inner join SourceRank b 
                on a.source = b.source
        ) 
        select a.date, a.open, a.high, a.low, a.close, a.volume
        from tmp a 
            inner join (
                select date, min(rank) as rank 
                from tmp 
                where date between '{start_date}' and '{end_date}' 
                group by date
            ) b 
            on a.date = b.date and a.rank = b.rank"""
        return pd.read_sql(stmt, con=self.conn, index_col="date", parse_dates=["date"])

    def _read_tickers_from_db(self, tickers, start_date, end_date):
        data = [self._read_ticker_from_db(ticker, start_date, end_date) for ticker in tickers]
        return pd.concat(data, axis=1, keys=tickers).reorder_levels([1, 0], axis=1).sort_index(axis=1)
