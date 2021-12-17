import pandas as pd
from patterns import patterns
import config
import alpaca_trade_api as tradeapi
import duckdb as ddb


# Setup api and chunk_size
api = tradeapi.REST(config.API_KEY, config.SECRET_KEY, base_url=config.API_URL)
CHUNK_SIZE = 200


"""OPEN DUCKDB CONNECTION"""
# conn = ddb.connect(database='alpaca2duck.ddb', read_only=False)

def close_connection(conn):
    conn.close()

def create_tables(conn):
    """Create tables symbols, prices in conn's duckdb"""
    # Create symbols table --id BIGINT DEFAULT NEXTVAL('seq'), 
    conn.execute("CREATE SEQUENCE seq")
    conn.execute("""CREATE TABLE symbols( 
                    id UINTEGER DEFAULT NEXTVAL('seq') PRIMARY KEY,
                    symbol VARCHAR UNIQUE, 
                    name VARCHAR, 
                    alpaca_id VARCHAR,
                    exchange VARCHAR, 
                    easy_to_borrow BOOLEAN, 
                    fractionable BOOLEAN, 
                    marginable BOOLEAN, 
                    shortable BOOLEAN)""")
    # create prices table
    conn.execute("""CREATE TABLE prices(
                    date DATE,
                    stock_id UINTEGER,
                    open DOUBLE,
                    high DOUBLE,
                    low DOUBLE,
                    close DOUBLE,
                    volume UINTEGER)""")
    conn.execute("CREATE UNIQUE INDEX id_date_idx ON prices (stock_id, date)")
    
   
def get_stocks():
    """get list of alpaca active symbols"""
    assets = api.list_assets(status='active')
    return assets


def create_stocks_df():
    """insert stocks details into stock table"""
    assets = get_stocks()
    symbols = conn.execute("select symbol from symbols").fetchnumpy()
    df = pd.DataFrame([
            {
                'symbol'        : asset.symbol,
                'name'          : asset.name,
                'alpaca_id'     : asset.id,
                'exchange'      : asset.exchange,
                'easy_to_borrow': asset.easy_to_borrow,
                'fractionable'  : asset.fractionable,
                'marginable'    : asset.marginable,
                'shortable'     : asset.shortable,
            } for asset in assets 
            if asset.tradable and asset.symbol not in symbols
    ])
    conn.register('symbols_view', df)
    conn.execute("""INSERT INTO symbols (
                    symbol,
                    name, 
                    alpaca_id, 
                    exchange,
                    easy_to_borrow,
                    fractionable,
                    marginable,
                    shortable )SELECT 
                *
                FROM symbols_view""")


def read_stocklist():
    """get list and dict{sym:id} of all stocks"""
    symbols = []
    stock_dict = {}
    rows = conn.execute("SELECT symbols.symbol, symbols.id FROM symbols").fetchnumpy()
    stock_dict = {e : rows['id'][i] for i,e in enumerate(rows['symbol'])}
    return rows['symbol'], stock_dict


def get_date_after():
    result = conn.execute("SELECT MAX(date) FROM prices").fetchone()
    result = pd.Timestamp(result[0], tz='US/Eastern')
    result = result.isoformat()
    return result
        

def get_update_prices():
    symbols, stock_dict = read_stocklist()
#     symbols = ['AMC','GME']
    tmpls0=[]
    after = get_date_after()
    if after == 'NaT': after =None
    print(after)
    for i in range(0, len(symbols), CHUNK_SIZE):
        symbol_chunk = symbols[i:i+CHUNK_SIZE]
        barsets = api.get_barset(symbol_chunk, 'day', limit=1000, after=after)
        for symbol in barsets:
#             print(f"Processing symbol {symbol}")
            for bar in barsets[symbol]:
                tmp = {
                    'stock_id'  :stock_dict[symbol],
                    'date'      :bar.t,
                    'open'      :bar.o,
                    'high'      :bar.h,
                    'low'       :bar.l,
                    'close'     :bar.c,
                    'volume'    :bar.v }
                tmpls0.append(tmp)
    df_price = pd.DataFrame(tmpls0)
    conn.register('df_price', df_price)
    conn.execute("""INSERT INTO prices SELECT 
                    date,
                    stock_id,
                    open,
                    high,
                    low,
                    close,
                    volume 
                    FROM df_price""")
#     return df_price



def main():
    # create_stocks()
    # get_update_prices()
    print(get_date_after())

if __name__ == "__main__":
    main()


