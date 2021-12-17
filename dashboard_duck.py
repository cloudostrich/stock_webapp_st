import pandas as pd
import numpy as np
import requests
from datetime import datetime as dt

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import talib
import tweepy
import duckdb as ddb
import streamlit as st
import vectorbt as vbt

from patterns import patterns
from vbt_indicts import indicts
import config

# connect to duckdb globally
conn = ddb.connect(database=config.DB_FILE, read_only=True)

# streamlit stuff starts
st.sidebar.title("Options")
option = st.sidebar.selectbox("Which Dashboard?", ('twitter', 'wallstreetbets','stocktwits', 'chart', 'pattern', 'TA scanner', 'Backtester'),5 )
st.title(option)


def close_conn(conn):
    """Close connection to duckdb"""
    conn.close()

@st.experimental_memo
def read_stocklist():
    """get list and dict{sym:id} of all stocks"""
    # symbols = []
    # stock_dict = {}
    rows = conn.execute("SELECT symbols.symbol, symbols.id, symbols.name FROM symbols").fetchdf()
    # stock_dict = {e : rows['id'][i] for i,e in enumerate(rows['symbol'])}
    return rows

@st.experimental_memo
def get_all_prices(startday='2021-06-01'):
    start = pd.to_datetime(startday, format='%Y-%m-%d')
    lmtprices = conn.execute("SELECT * FROM prices WHERE date > (?)",[start]).fetch_df()
    return lmtprices

@st.experimental_memo
def get_data_from_duck(startday='2021-06-01'):
    symbols = read_stocklist()
    prices = get_all_prices(startday)
    return symbols, prices

@st.experimental_memo
def get_symbol_price(symbol):
    df = conn.execute("""SELECT prices.date, 
                                prices.open, 
                                prices.high,
                                prices.low, 
                                prices.close, 
                                prices.volume,
                                symbols.symbol, 
                                symbols.name, 
                                symbols.exchange 
                        FROM prices JOIN symbols ON 
                        (prices.stock_id=symbols.id)
                        WHERE symbols.id = 
                        (select id FROM symbols WHERE symbol=?) 
                        """,[symbol]).fetchdf()
    return df

def twitter_connect():
    auth = tweepy.OAuthHandler(config.TWITTER_CONSUMER_KEY, config.TWITTER_CONSUMER_SECRET)
    auth.set_access_token(config.TWITTER_ACCESS_TOKEN, config.TWITTER_ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth)
    return api

def draw_candles(df):
    fig = make_subplots(rows=2, 
                        cols=1, 
                        shared_xaxes=True, 
                        vertical_spacing=0.03, 
                        subplot_titles=('Candles', 'Volume'), 
                        row_width=[0.2, 0.7])

    # Plot OHLC on 1st row
    fig.add_trace(go.Candlestick(x=df['date'], 
                                open=df["open"], 
                                high=df["high"],
                                low=df["low"], 
                                close=df["close"], 
                                name="Candles"), 
                                row=1, col=1)

    # Bar trace for volumes on 2nd row without legend
    fig.add_trace(go.Bar(x=df['date'], y=df['volume'], showlegend=False), row=2, col=1)

    # Do not show OHLC's rangeslider plot 
    fig.update(layout_xaxis_rangeslider_visible=False)

    fig.update_layout(showlegend=False,
                        autosize=False,
                        width=1000,
                        height=700)
    return fig

@st.experimental_memo
def pivot_prices_c(prices):
    """df format needed for all indicators"""
    df = prices[['date','close','stock_id']]
    df=df.pivot(index='date', columns='stock_id', values='close')
    df.ffill(inplace=True)
    return df

@st.experimental_memo
def pivot_prices_hl(prices):
    """df format for atr, stoch"""
    h,l = (prices[['date',val,'stock_id']] for val in ['high','low'])
    dfh=h.pivot(index='date', columns='stock_id', values='high')
    dfl=l.pivot(index='date', columns='stock_id', values='low')
    dfh.ffill(inplace=True)
    dfl.ffill(inplace=True)
    return dfh,dfl

@st.experimental_memo
def pivot_prices_v(prices):
    """df format for obv"""
    df = prices[['date','volume','stock_id']]
    df=df.pivot(index='date', columns='stock_id', values='volume')
    df.ffill(inplace=True)
    return df

def vbt_run_indicator(df, name, params):
    vbt_fn = getattr(vbt, name)
    ranned = vbt_fn.run(df,**params)
    return ranned


#STOCKTWITS OPTION
if option == 'stocktwits':
    symbol = st.sidebar.text_input("Symbol", value='AAPL', max_chars=5)

    r = requests.get(f"https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json")

    data = r.json()

    for message in data['messages']:
        st.image(message['user']['avatar_url'])
        st.write(message['user']['username'])
        st.write(message['created_at'])
        st.write(message['body'])

# TWITTER OPTION
if option == 'twitter':
    api = twitter_connect()
    st.sidebar.subheader("Usernames")
    for username in config.TWITTER_USERNAMES:
        st.sidebar.write(username)
        user = api.get_user(screen_name=username)
        tweets = api.user_timeline(screen_name=username)

        st.subheader(username)
        st.image(user.profile_image_url)
        
        for tweet in tweets:
            if '$' in tweet.text:
                words = tweet.text.split(' ')
                for word in words:
                    if word.startswith('$') and word[1:].isalpha():
                        symbol = word[1:]
                        st.write(symbol)
                        st.write(tweet.text)
                        st.image(f"https://finviz.com/chart.ashx?t={symbol}")

# WALLSTREETBETS OPTION
if option == 'wallstreetbets':
    num_days = st.sidebar.slider('Number of days', 1, 30, 3)

    # cursor.execute("""
    #     SELECT COUNT(*) AS num_mentions, symbol
    #     FROM mention JOIN stock ON stock.id = mention.stock_id
    #     WHERE date(dt) > current_date - interval '%s day'
    #     GROUP BY stock_id, symbol   
    #     HAVING COUNT(symbol) > 10
    #     ORDER BY num_mentions DESC
    # """, (num_days,))

    # counts = cursor.fetchall()
    # for count in counts:
    #     st.write(count)
    
    # cursor.execute("""
    #     SELECT symbol, message, url, dt, username
    #     FROM mention JOIN stock ON stock.id = mention.stock_id
    #     ORDER BY dt DESC
    #     LIMIT 100
    # """)

    # mentions = cursor.fetchall()
    # for mention in mentions:
    #     st.text(mention['dt'])
    #     st.text(mention['symbol'])
    #     st.text(mention['message'])
    #     st.text(mention['url'])
    #     st.text(mention['username'])

    # rows = cursor.fetchall()

    # st.write(rows)

# CHART OPTION
if option == 'chart':
    symbol = st.sidebar.text_input("Symbol", value='TSLA', max_chars=None, key=None, type='default').upper()

    df = get_symbol_price(symbol)

    st.subheader(symbol.upper())
    st.write(df['symbol'][0], df['name'][0], df['exchange'][0])

    fig = draw_candles(df[['date','open','high','low','close','volume']][:100])
    # fig.update_xaxes(type='category')

    st.plotly_chart(fig, use_container_width=True)
    with st.expander("chart data", expanded=False):
        st.dataframe(df)

# PATTERN OPTION
if option == 'pattern':
    patvals = [p for p in patterns.keys()]
    # st.sidebar.write(patvals)
    pattern = st.sidebar.selectbox(
        "Which Pattern?",
        patvals
    )

    pattern_function = getattr(talib, pattern)
    st.sidebar.write(pattern_function)
    
    # get data from db
    symbols = read_stocklist()
    prices = get_all_prices()
    
    # scan all symbols by id with pattern
    scan=[]
    for i in symbols['id']:
        try:
            df = prices[prices["stock_id"]==i]
            results = pattern_function(df['open'], df['high'], df['low'], df['close'])
            last = results.tail(1).values[0]
            if last !=0: scan.append((last, i))
        except Exception as e:
            print('failed on: ', i, e)
    st.write("** NUMBER OF RESULTS: ",len(scan), "**")
    if not scan: st.write("NO RESULTS")
    else:
        scandf = pd.DataFrame(scan)
        scandf.columns = ['signal', 'id']
        answer = scandf.merge(symbols, how='left', on='id')

        # # display result
        st.dataframe(answer)
        for index, row in answer.iterrows():
            st.write(row['symbol'], row['signal'])
            st.image(f"https://finviz.com/chart.ashx?t={row['symbol']}&ty=c&ta=1&p=d&s=l", caption='Sunrise by the mountains')

        # fig= draw_candles(row['df'])
        # st.plotly_chart(fig) #, use_container_width=True)

# TA SCREENER
if option =='TA scanner':
    """ Scan all symbols for arbitrary set of TA indicators"""
    st.sidebar.markdown("""<hr style="height:3px;background-color:#A07E06;" /> """, unsafe_allow_html=True)

    # get data from db
    symbols, prices = get_data_from_duck()
    dfc = pivot_prices_c(prices)

    # Indicators setting    
    num_indicator = st.slider('How many indicators?', 1, 5, 1)
    # Indicators Setup
    with st.expander('Indicator Setup'):
        tmp_indi ={}
        for num_i in range(num_indicator):
            st.markdown("""<hr style="height:1px;background-color:#3B903B;" /> """, unsafe_allow_html=True)
            name_val = f"indicator_{num_i+1}"
            vbt_runame = f"vbtrun_{num_i+1}"
            select_val = st.selectbox(f"# {num_i+1} : Which Indicator?", indicts.keys(),2)#, key=f"indicator_{num_i+1}_type")
            params = indicts[select_val]['params'].copy()
            for p in params:
                if p=='short_name': 
                    params[p] = st.text_input(f'short name {num_i}', value = params[p])#,key=f'indicator_{num_i+1}_params_{p}')
                elif 'ewm' in p:
                    params[p] = st.checkbox(f'{p}_{num_i}', value = params[p])#,key=f'indicator_{num_i+1}_params_{p}')
                else:
                    params[p] = st.number_input(f'{p}_{num_i}', value = params[p])#,key=f'indicator_{num_i+1}_params_{p}')
            tmp_indi[name_val] = {'type': select_val, 'params': params, 'vbt_runame': vbt_runame, 'df_set':''}

    #List setted indicators
    with st.expander(f" You have {len(tmp_indi)} Indicators"):
        for i,kei in enumerate(tmp_indi):
            st.text(f"{i+1} : {kei}, {tmp_indi[kei]['type']}, {tmp_indi[kei]['params'][tuple(tmp_indi[kei]['params'].keys())[0]]}, short_names: {tmp_indi[kei]['params']['short_name']}")
    if len(set([tmp_indi[k]['params']['short_name'] for k in tmp_indi])) != len([tmp_indi[k]['params']['short_name'] for k in tmp_indi]):
        st.error("Please ensure all indicators short names are different")


    st.markdown("""<hr style="height:3px;background-color:#A07E06;" /> """, unsafe_allow_html=True)
    
    # Scan Conditions
    num_condition = st.slider('How many scan conditions?', 1, 5, 1)
    with st.expander('Scan conditions'):
        tmp_condi = {}
        for num_c in range(num_condition):
            st.markdown("""<hr style="height:1px;background-color:#316b31;" /> """, unsafe_allow_html=True)

            condition_a = st.selectbox(f"# {num_c+1} Condition: indicator this", tmp_indi.keys())
            st.caption(f"{tmp_indi[condition_a]['params']['short_name']}, {tmp_indi[condition_a]['params'][tuple(tmp_indi[condition_a]['params'].keys())[0]]} ")

            condition_b = st.selectbox(f"# {num_c+1} Compare method", indicts[tmp_indi[condition_a]['type']]['methods'])

            col1, col2 = st.columns([1,2])
            with col1:
                condition_c = st.radio(f"# {num_c+1} compare against what",
                                ('another indicator', 'indicator property', 'manual number'))
            with col2:
                if condition_c == 'another indicator':
                    condition_c1 = st.selectbox(f"# {num_c+1} : Other Indicator", tmp_indi.keys())
                    st.caption(f"{tmp_indi[condition_c1]['type']}, {tmp_indi[condition_c1]['params'][tuple(tmp_indi[condition_c1]['params'].keys())[0]]}")
                    condition_c2 = ''
                    condition_c3 = ''
                elif condition_c == 'manual number':
                    condition_c1 = ''
                    condition_c2 = ''
                    condition_c3 = st.number_input('give your best number')
                else:
                    condition_c1 = st.selectbox(f"# {num_c+1} : Other Indicator (proprties)", tmp_indi.keys())
                    st.caption(f"{tmp_indi[condition_c1]['type']}, {tmp_indi[condition_c1]['params'][tuple(tmp_indi[condition_c1]['params'].keys())[0]]}")
                    condition_c2 = st.selectbox(f"# {num_c+1} : properties", indicts[tmp_indi[condition_c1]['type']]['props'])
                    condition_c3 = ''
            if num_c:
                condition_andor = st.checkbox(f'AND/OR_{num_c+1}',value=True)
            else:
                condition_andor = ''

            tmp_condi[num_c] = {'a':condition_a,
                                'b':condition_b,
                                'c1': condition_c1,
                                'c2': condition_c2,
                                'c3': condition_c3,
                                'd':condition_andor} #:TODO: radio for None, And, Or??

    with st.expander(f"You have {len(tmp_condi)} scan conditions"):
        for i,c in tmp_condi.items():
            st.write(i,c['d'],c['a'], c['b'], c['c1'], c['c2'], c['c3'])

    # get unique list of indicators to set vbt run name
    chk_indilst=[]
    for i,cnd in tmp_condi.items():
        chk_indilst.extend([cnd['a'],cnd['c1']])
    chk_indiset = set(chk_indilst)
    chk_indiset.discard('')
    st.write(chk_indiset)
    # for i in chk_indiset: 
    #     ii = i[-1]
    #     tmp_indi[i]['vbt_runame']=f'vbtrun_{ii}'

    # Scan order string
    scanorder = ''
    for i,cnd in tmp_condi.items():
        if cnd['d']:
            cond0 = '&' # TODO: modify to add OR |
        else:
            cond0 = ''
        if cnd['c1']:
            if cnd['c2']:
                condc = f"{tmp_indi[cnd['c1']]['vbt_runame']}.{cnd['c2']}"
            else:
                condc = f"{tmp_indi[cnd['c1']]['vbt_runame']}"
        else:
            condc = cnd['c3']
        scanorder = scanorder + f"{cond0} {tmp_indi[cnd['a']]['vbt_runame']}.{cnd['b']}({condc}) "
        
        #({tmp_indi[cnd['c1']]['vbt_runame']}) "
    scanorder = scanorder[1:]
    
    for i in chk_indiset:
        if tmp_indi[i]['type'] in ['ATR', 'STOCH']:
            dfh,dfl= pivot_prices_hl(prices)
            tmp_indi[i]['df_set'] = 'dfh,dfl,dfc'
        elif tmp_indi[i]['type'] == 'OBV':
            dfv = pivot_prices_v(prices)
            tmp_indi[i]['df_set'] = 'dfc, dfv'
        else:
            tmp_indi[i]['df_set'] = 'dfc'

    with st.expander('last checks'):
        st.write("last check of chk_indiset: ",chk_indiset)
        st.write("last check of vbt run names: ",{tmp_indi[i]['vbt_runame'] for i in tmp_indi if tmp_indi[i]['vbt_runame']})
        st.write("last check of scanorder: ",scanorder)

    # Scan button
    submitted = st.button("Run Scan!")
    if submitted:
        st.text("""Note to Self: Get extra df if needed, 
            (eval) vbt_run the indicators, 
            eval the entry expression""")

        # vbt run ta
        for indi in chk_indiset:
            st.write(tmp_indi[indi]['vbt_runame'])
            tmp_vbt_runame = tmp_indi[indi]['vbt_runame']
            # st.write(f"{tmp_vbt_runame} = vbt.{tmp_indi[indi]['type']}.run({tmp_indi[indi]['df_set']},**{tmp_indi[indi]['params']})")
            exec(f"{tmp_vbt_runame} = vbt.{tmp_indi[indi]['type']}.run({tmp_indi[indi]['df_set']},**{tmp_indi[indi]['params']})")
        
        st.write(f"entry = {scanorder}")

        entry = eval(scanorder)
        # st.write(entry.shape)

        dropcols = list(entry.columns.names)
        st.write(dropcols)
        dropcols.remove('stock_id')
        st.write(dropcols)
        # dropcols = list(range(len(dropcols)))

        en = entry.droplevel(dropcols, axis=1).iloc[-1]
        en=pd.DataFrame(en[en].index)
        en = en.rename(columns={'stock_id': 'id'})
        st.write(en.head())

        en = en.merge(symbols, how='left', on='id')
        st.write(en.shape)
        st.dataframe(en)

        st.success('This is a success message!')
        st.balloons()


    color = st.sidebar.color_picker('Pick A Color', '#00f900')
    st.sidebar.write('The current color is', color)

# Backtester
if option =='Backtester':
    """ Backtest 1 symbol with TA"""
    st.sidebar.markdown("""<hr style="height:3px;background-color:#A07E06;" /> """, unsafe_allow_html=True)

    symbol_bt = st.sidebar.text_input("Symbol", value='TSLA', max_chars=None, key=None, type='default').upper()

    df_bt = get_symbol_price(symbol_bt)
    df_bt.set_index('date', inplace=True)

    st.subheader(symbol_bt.upper())
    st.write(df_bt['symbol'][0], df_bt['name'][0], df_bt['exchange'][0])

    st.markdown("""<hr style="height:3px;background-color:#A07E06;" /> """, unsafe_allow_html=True)
    # Indicators setting    
    num_indicator = st.slider('How many indicators?', 1, 5, 1)
    # Indicators Setup
    with st.expander('Indicator Setup'):
        tmp_indi ={}
        for num_i in range(num_indicator):
            st.markdown("""<hr style="height:1px;background-color:#3B903B;" /> """, unsafe_allow_html=True)
            name_val = f"indicator_{num_i+1}"
            vbt_runame = f"vbtrun_{num_i+1}"
            select_val = st.selectbox(f"# {num_i+1} : Which Indicator?", indicts.keys(),2)#, key=f"indicator_{num_i+1}_type")
            params = indicts[select_val]['params'].copy()
            for p in params:
                if p=='short_name': 
                    params[p] = st.text_input(f'short name {num_i}', value = params[p])#,key=f'indicator_{num_i+1}_params_{p}')
                elif 'ewm' in p:
                    params[p] = st.checkbox(f'{p}_{num_i}', value = params[p])#,key=f'indicator_{num_i+1}_params_{p}')
                else:
                    params[p] = st.number_input(f'{p}_{num_i}', value = params[p])#,key=f'indicator_{num_i+1}_params_{p}')
            tmp_indi[name_val] = {'type': select_val, 'params': params, 'vbt_runame': vbt_runame, 'df_set':''}

    #List setted indicators
    with st.expander(f" You have {len(tmp_indi)} Indicators"):
        for i,kei in enumerate(tmp_indi):
            st.text(f"{i+1} : {kei}, {tmp_indi[kei]['type']}, {tmp_indi[kei]['params'][tuple(tmp_indi[kei]['params'].keys())[0]]}, short_names: {tmp_indi[kei]['params']['short_name']}")
    if len(set([tmp_indi[k]['params']['short_name'] for k in tmp_indi])) != len([tmp_indi[k]['params']['short_name'] for k in tmp_indi]):
        st.error("Please ensure all indicators short names are different")

    st.markdown("""<hr style="height:3px;background-color:#A07E06;" /> """, unsafe_allow_html=True)
    
    longorshort = st.checkbox("Long or Short", value=True)
    # Entry Conditions
    num_entry = st.slider('How many entry conditions?', 1, 5, 1)

    with st.expander('Entry conditions'):
        tmp_entry = {}
        for num_c in range(num_entry):
            st.markdown("""<hr style="height:1px;background-color:#316b31;" /> """, unsafe_allow_html=True)

            condition_a = st.selectbox(f"# {num_c+1} Entry: indicator this", tmp_indi.keys())
            st.caption(f"{tmp_indi[condition_a]['params']['short_name']}, {tmp_indi[condition_a]['params'][tuple(tmp_indi[condition_a]['params'].keys())[0]]} ")
            
            condition_b = st.selectbox(f"# {num_c+1} Entry: Compare method", indicts[tmp_indi[condition_a]['type']]['methods'])
            
            col1, col2 = st.columns([1,2])
            with col1:
                condition_c = st.radio(f"# {num_c+1} Entry: compare against what",
                                ('another indicator', 'indicator property', 'manual number'))
            with col2:
                if condition_c == 'another indicator':
                    condition_c1 = st.selectbox(f"# {num_c+1} : Other Indicator", tmp_indi.keys())
                    st.caption(f"{tmp_indi[condition_c1]['params']['short_name']}, {tmp_indi[condition_c1]['params'][tuple(tmp_indi[condition_c1]['params'].keys())[0]]}")
                    condition_c2 = ''
                    condition_c3 = ''
                elif condition_c == 'manual number':
                    condition_c1 = ''
                    condition_c2 = ''
                    condition_c3 = st.number_input('give your best number')
                else:
                    condition_c1 = st.selectbox(f"# {num_c+1} Entry: Other Indicator (proprties)", tmp_indi.keys())
                    st.caption(f"{tmp_indi[condition_c1]['type']}, {tmp_indi[condition_c1]['params'][tuple(tmp_indi[condition_c1]['params'].keys())[0]]}")
                    condition_c2 = st.selectbox(f"# {num_c+1} : properties", indicts[tmp_indi[condition_c1]['type']]['props'])
                    condition_c3 = ''
            if num_c:
                condition_andor = st.checkbox(f'AND/OR_{num_c+1}',value=True)
            else:
                condition_andor = ''

            tmp_entry[num_c] = {'a':condition_a,
                                'b':condition_b,
                                'c1': condition_c1,
                                'c2': condition_c2,
                                'c3': condition_c3,
                                'd':condition_andor} #:TODO: radio for None, And, Or??

    with st.expander(f"You have {len(tmp_entry)} entry conditions"):
        for i,c in tmp_entry.items():
            # st.write(i+1,' : ',c['d'],c['a'], c['b'], c['c1'], c['c2'], c['c3'])
            st.text(f"{i+1} : {c['d']} {c['a']} {c['b']} {c['c1']} {c['c2']} {c['c3']}")

    # Exit Conditions
    num_exit = st.slider('How many exit conditions?', 1, 5, 1)
    with st.expander('Exit conditions'):
        tmp_exit = {}
        for num_c in range(num_exit):
            st.markdown("""<hr style="height:1px;background-color:#316b31;" /> """, unsafe_allow_html=True)

            condition_a = st.selectbox(f"# {num_c+1} Exit: indicator this", tmp_indi.keys())
            st.caption(f"{tmp_indi[condition_a]['params']['short_name']}, {tmp_indi[condition_a]['params'][tuple(tmp_indi[condition_a]['params'].keys())[0]]} ")
            
            condition_b = st.selectbox(f"# {num_c+1} Exit: Compare method", indicts[tmp_indi[condition_a]['type']]['methods'])
            
            col1, col2 = st.columns([1,2])
            with col1:
                condition_c = st.radio(f"# {num_c+1} Exit: compare against what",
                                ('another indicator', 'indicator property', 'manual number'))
            with col2:
                if condition_c == 'another indicator':
                    condition_c1 = st.selectbox(f"# {num_c+1} Exit: Other Indicator", tmp_indi.keys())
                    st.caption(f"{tmp_indi[condition_c1]['params']['short_name']}, {tmp_indi[condition_c1]['params'][tuple(tmp_indi[condition_c1]['params'].keys())[0]]}")
                    condition_c2 = ''
                    condition_c3 = ''
                elif condition_c == 'manual number':
                    condition_c1 = ''
                    condition_c2 = ''
                    condition_c3 = st.number_input('give your best number')
                else:
                    condition_c1 = st.selectbox(f"# {num_c+1} : Other Indicator (proprties)", tmp_indi.keys())
                    st.caption(f"{tmp_indi[condition_c1]['type']}, {tmp_indi[condition_c1]['params'][tuple(tmp_indi[condition_c1]['params'].keys())[0]]}")
                    condition_c2 = st.selectbox(f"# {num_c+1} : properties", indicts[tmp_indi[condition_c1]['type']]['props'])
                    condition_c3 = ''
            if num_c:
                condition_andor = st.checkbox(f'AND/OR_{num_c+1}',value=True)
            else:
                condition_andor = ''

            tmp_exit[num_c] = {'a':condition_a,
                                'b':condition_b,
                                'c1': condition_c1,
                                'c2': condition_c2,
                                'c3': condition_c3,
                                'd':condition_andor} #:TODO: radio for None, And, Or??

    with st.expander(f"You have {len(tmp_exit)} exit conditions"):
        for i,c in tmp_exit.items():
            # st.write(i,c['d'],c['a'], c['b'], c['c1'], c['c2'], c['c3'])
            st.text(f"{i+1} : {c['d']} {c['a']} {c['b']} {c['c1']} {c['c2']} {c['c3']}")

    # get unique list of indicators to set vbt run name,
    chk_indilst=[]
    for i,cnd in tmp_entry.items(): chk_indilst.extend([cnd['a'],cnd['c1']])
    for i,cnd in tmp_exit.items(): chk_indilst.extend([cnd['a'],cnd['c1']])
    chk_indiset = set(chk_indilst)
    chk_indiset.discard('')


    # Entry order string
    entryorder = ''
    for i,cnd in tmp_entry.items():
        if cnd['d']:
            cond0 = '&' # TODO: modify to add OR |
        else:
            cond0 = ''
        if cnd['c1']:
            if cnd['c2']:
                condc = f"{tmp_indi[cnd['c1']]['vbt_runame']}.{cnd['c2']}"
            else:
                condc = f"{tmp_indi[cnd['c1']]['vbt_runame']}"
        else:
            condc = cnd['c3']
        entryorder = entryorder + f"{cond0} {tmp_indi[cnd['a']]['vbt_runame']}.{cnd['b']}({condc}) "
    entryorder = entryorder[1:]
    
    # Exit order string
    exitorder = ''
    for i,cnd in tmp_exit.items():
        if cnd['d']:
            cond0 = '&' # TODO: modify to add OR |
        else:
            cond0 = ''
        if cnd['c1']:
            if cnd['c2']:
                condc = f"{tmp_indi[cnd['c1']]['vbt_runame']}.{cnd['c2']}"
            else:
                condc = f"{tmp_indi[cnd['c1']]['vbt_runame']}"
        else:
            condc = cnd['c3']
        exitorder = exitorder + f"{cond0} {tmp_indi[cnd['a']]['vbt_runame']}.{cnd['b']}({condc}) "
    exitorder = exitorder[1:]

    # set df form input
    dfc = df_bt['close']
    for i in chk_indiset:
        if tmp_indi[i]['type'] in ['ATR', 'STOCH']:
            dfh,dfl= df_bt['high'], df_bt['low'] #pivot_prices_hl(df)
            tmp_indi[i]['df_set'] = 'dfh,dfl,dfc'
        elif tmp_indi[i]['type'] == 'OBV':
            dfv = df_bt['volume'] #pivot_prices_v(df)
            tmp_indi[i]['df_set'] = 'dfc, dfv'
        else:
            # dfc = df_bt['close']
            tmp_indi[i]['df_set'] = 'dfc'

    with st.expander('last checks'):
        st.write("last check of chk_indiset: ",chk_indiset)
        st.write("last check of vbt run names: ",{tmp_indi[i]['vbt_runame'] for i in tmp_indi if tmp_indi[i]['vbt_runame']})
        st.write("last check of entryorder: ",entryorder)
        st.write("last check of exitorder: ",exitorder)

    # Backtest button
    submitted = st.button("Run Backtest!")
    if submitted:
        st.text("""Note to Self: 
            (eval) vbt_run the indicators, 
            eval the entry expression""")

        # vbt run ta
        for indi in chk_indiset:
            st.write(tmp_indi[indi]['vbt_runame'])
            tmp_vbt_runame = tmp_indi[indi]['vbt_runame']

            # TODO, remove check for production
            # st.write(f"{tmp_vbt_runame} = vbt.{tmp_indi[indi]['type']}.run({tmp_indi[indi]['df_set']},**{tmp_indi[indi]['params']})")

            exec(f"{tmp_vbt_runame} = vbt.{tmp_indi[indi]['type']}.run({tmp_indi[indi]['df_set']},**{tmp_indi[indi]['params']})")
        
        st.write(f"entry = {entryorder}")
        entries = eval(entryorder)

        st.write(f"exits = {exitorder}")
        exits = eval(exitorder)

        # Portfolio stuff
        if longorshort:
            Portfolio = vbt.Portfolio.from_signals(dfc, entries, exits)
        else:
            Portfolio = vbt.Portfolio.from_signals(dfc, short_entries=entries, short_exits=exits)
        # st.dataframe(pd.DataFrame(Portfolio.stats()))
        st.write(Portfolio.total_profit())
        st.write(Portfolio.final_value())
        pfstats = Portfolio.stats()
        # ts = pd.Timestamp('2020-03-14T15:32:52.192548651')
        pfstats[0] = pfstats[0].strftime('%Y-%m-%d')
        pfstats[1] = pfstats[1].strftime('%Y-%m-%d')
        # ts.strftime('%Y-%m-%d %X')
        # pfstats = pd.DataFrame(pfstats).reset_index()
        pfstats = pfstats.to_dict()

        with st.expander("Portfolio Stats"):
            for k,v in pfstats.items(): st.write(k," : ",v)


        st.text('PLots')

        closes = Portfolio.close
        buys = Portfolio.orders.records_readable[Portfolio.orders.records_readable['Side']=='Buy']
        sells = Portfolio.orders.records_readable[Portfolio.orders.records_readable['Side']=='Sell']
        fig1 = go.Figure()

        fig1.add_trace(go.Scatter(x=closes.index, y=closes.values, name='closes'))
        fig1.add_trace(go.Scatter(mode='markers',x=buys['Timestamp'], y=buys['Price'], name="buys", 
                                marker={"symbol":'triangle-up', "color":'forestgreen', "size":11}))
        fig1.add_trace(go.Scatter(mode='markers',x=sells['Timestamp'], y=sells['Price'], name="sells", 
                                marker={"symbol":'triangle-down', "color":'red', "size":11}))
        # fig1.show()

        st.plotly_chart(fig1, use_container_width=True)
        # fig1.show()

        trades = Portfolio.trades.records_readable
        fig2 = go.Figure()
        fig2.add_shape(dict(
            type= 'line',
            xref= 'paper', x0= 0, x1= 1,
            yref= 'y', y0= 0, y1= 0,
            line={'color':'gray', 'dash':'dash'}))
        fig2.add_trace(go.Scatter(mode='markers',name="Profit",
                                x=trades['Exit Timestamp'], y=trades[trades['Return']>0]['Return'],
                                marker={"symbol":'circle', 
                                        "color":'green',
                                        "size": 15}))#trades[trades['Return']>0]['Return']*15}))
        fig2.add_trace(go.Scatter(mode='markers',name="Loss",
                                x=trades['Exit Timestamp'], y=trades[trades['Return']<0]['Return'],
                                marker={"symbol":'circle', 
                                        "color":'red',
                                        'size':15}))#abs(trades[trades['Return']>0]['Return'])*15}))

        st.plotly_chart(fig2, use_container_width=True)    
        # fig2.show()

        Portfolio.cumulative_returns()
        pfcum = Portfolio.cumulative_returns()
        pfcum = pd.DataFrame(pfcum)
        pfcumpos = pfcum[pfcum>=0]
        pfcumneg = pfcum[pfcum<0]
        bench = vbt.Portfolio.from_holding(dfc) #, init_cash=100)
        bench = bench.cumulative_returns()
        fig3 = go.Figure()

        fig3.add_trace(go.Scatter(x=bench.index, y=bench.values, name='Benchmark',
                                line=dict(color='darkblue')))
        fig3.add_trace(go.Scatter(x=bench.index, y=pfcumpos[0], name="Cumulative Returns", opacity=0.5,
                                fill='tozeroy', fillcolor='rgba(51, 204, 51,0.3)',line=dict(color='darkviolet')))
        fig3.add_trace(go.Scatter(x=bench.index, y=pfcumneg[0], name="Cumulative Returns", opacity=0.5,
                                fill='tozeroy', fillcolor='rgba(255, 153, 204,0.3)', line=dict(color='darkviolet')))
        st.plotly_chart(fig3, use_container_width=True)  
        # fig3.show()

        st.success('This is a success message!')
        st.balloons()


    color = st.sidebar.color_picker('Pick A Color', '#00f900')
    st.sidebar.write('The current color is', color)

