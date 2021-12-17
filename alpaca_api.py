from sqlmodel import Session, select, func
import alpaca_trade_api as tradeapi

from createdb import Stock, engine, Stock_Price
import config
import pandas as pd


# Setup api and chunk_size
api = tradeapi.REST(config.API_KEY, config.SECRET_KEY, base_url=config.API_URL)
CHUNK_SIZE = 200


def get_stocks():
    """get list of alpaca active symbols"""
    assets = api.list_assets(status='active')
    return assets


def create_stocks():
    """insert stocks details into stock table"""
    assets = get_stocks()
    with Session(engine) as session:
        symbols = session.exec(select(Stock.symbol)).all()
        for asset in assets:
            try:
                if asset.tradable and asset.symbol not in symbols:
                    print(f"new stock: {asset.symbol}, {asset.name}")
                    asset = Stock( 
                            symbol=asset.symbol,
                            name=asset.name,
                            alpaca_id=asset.id,
                            exchange=asset.exchange,
                            easy_to_borrow=asset.easy_to_borrow,
                            fractionable=asset.fractionable,
                            marginable=asset.marginable,
                            shortable=asset.shortable)
                    session.add(asset)
            except Exception as e:
                print(f"{e} : for : {asset.symbol}")
        session.commit()


def read_stocklist():
    """get list and dict{sym:id} of all stocks"""
    symbols = []
    stock_dict = {}
    with Session(engine) as session:
        rows = session.exec(select(Stock.symbol, Stock.id)).all()
        for row in rows:
            symbol = row['symbol']
            symbols.append(symbol)
            stock_dict[symbol] = row['id']
    return symbols, stock_dict


def get_date_after():
    with Session(engine) as session:
        result = session.exec(select(func.max(Stock_Price.date))).first()
        result = pd.Timestamp(result, tz='US/Eastern')
        result = result.isoformat()
    return result
        

def get_update_prices():
    symbols, stock_dict = read_stocklist()
    # symbols = ['AMC','GME']
    after = get_date_after()
    # print(after, type(after))
    # if after != 'NaT': print("**** GOT SOMETHING")
    # else: print("***** NOTHNIG*****")

    with Session(engine) as session:
        if after == 'NaT': after =None
        for i in range(0, len(symbols), CHUNK_SIZE):
            symbol_chunk = symbols[i:i+CHUNK_SIZE]
            barsets = api.get_barset(symbol_chunk, 'day', limit=1000, after=after)
            for symbol in barsets:
                print(f"Processing symbol {symbol} after--{after}")
                for bar in barsets[symbol]:
                    price = Stock_Price(
                            stock_id=stock_dict[symbol],
                            date=bar.t,
                            open=bar.o,
                            high=bar.h,
                            low=bar.l,
                            close=bar.c,
                            volume=bar.v)  
                    session.add(price)
        session.commit()    # tab 1 over for less ram



def main():
    # create_stocks()
    # get_update_prices()
    print(get_date_after())

if __name__ == "__main__":
    main()
