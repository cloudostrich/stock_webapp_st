indicts = {
    'ATR'   : {
        'sig': "run(high, low, close, window=14, ewm=True, short_name='atr')",
        'params': {'window':14, 'ewm':True, 'short_name':'atr'},
        'name':'ATR',
        'methods': [
            'atr_above',
            'atr_below',
            'atr_crossed_above',
            'atr_crossed_below',
            'atr_equal',
            'close_above',
            'close_below',
            'close_crossed_above',
            'close_crossed_below',
            'close_equal',
            'high_above',
            'high_below',
            'high_crossed_above',
            'high_crossed_below',
            'high_equal',
            'low_above',
            'low_below',
            'low_crossed_above',
            'low_crossed_below',
            'low_equal',
            'tr_above',
            'tr_below',
            'tr_crossed_above',
            'tr_crossed_below',
            'tr_equal'
        ],
        'props': [
            'atr',
            'close',
            'ewm_list',
            'high',
            'low',
            'tr'
        ]
    },
    
    'BBANDS': {
        'sig': "run(close, window=20, ewm=False, alpha=2, short_name='bb')",
        'params': {'window':20, 'ewm':False, 'alpha':2,'short_name':'bb'},
        'name':'BBANDS',
        'methods': [
            'bandwidth_above',
            'bandwidth_below',
            'bandwidth_crossed_above',
            'bandwidth_crossed_below',
            'bandwidth_equal',
            'close_above',
            'close_below',
            'close_crossed_above',
            'close_crossed_below',
            'close_equal',
            'lower_above',
            'lower_below',
            'lower_crossed_above',
            'lower_crossed_below',
            'lower_equal',
            'middle_above',
            'middle_below',
            'middle_crossed_above',
            'middle_crossed_below',
            'middle_equal',
            'percent_b_above',
            'percent_b_below',
            'percent_b_crossed_above',
            'percent_b_crossed_below',
            'percent_b_equal',
            'upper_above',
            'upper_below',
            'upper_crossed_above',
            'upper_crossed_below',
            'upper_equal'
        ],
        'props': [
            'alpha_list',
            'bandwidth',
            'close',
            'ewm_list',
            'lower',
            'middle',
            'percent_b',
            'upper'
        ]
    },
    
    'MA'    : {
        'sig': "run(close, window, ewm=False, short_name='ma')",
        'params': {'window':10, 'ewm':False, 'short_name':'ma'},
        'name':'MA',
        'methods': [
            'close_above',
            'close_below',
            'close_crossed_above',
            'close_crossed_below',
            'close_equal',
            'ma_above',
            'ma_below',
            'ma_crossed_above',
            'ma_crossed_below',
            'ma_equal'
        ],
        'props': [
            'close',
            'ewm_list',
            'ma'
        ]
    },

    'MACD'  : {
        'sig': "run(close, fast_window=12, slow_window=26, signal_window=9, macd_ewm=False, signal_ewm=False, short_name='macd')",
        'params': {'fast_window':12, 'slow_window':26, 'signal_window':9, 'macd_ewm':False, 'signal_ewm':False, 'short_name':'macd'},
        'name':'MACD',
        'methods': [
            'close_above',
            'close_below',
            'close_crossed_above',
            'close_crossed_below',
            'close_equal',
            'hist_above',
            'hist_below',
            'hist_crossed_above',
            'hist_crossed_below',
            'hist_equal',
            'macd_above',
            'macd_below',
            'macd_crossed_above',
            'macd_crossed_below',
            'macd_equal',
            'signal_above',
            'signal_below',
            'signal_crossed_above',
            'signal_crossed_below',
            'signal_equal'
        ],
        'props': [
            'close',
            'fast_window_list',
            'hist',
            'macd',
            'macd_ewm_list',
            'signal',
            'signal_ewm_list',
            'signal_window_list',
            'slow_window_list'
        ]
    },

    'MSTD'  : {
        'sig': "run(close, window, ewm=False, short_name='mstd')",
        'params': {'window':10, 'ewm':False, 'short_name':'mstd'},
        'name':'MSTD',
        'methods': [
            'close_above',
            'close_below',
            'close_crossed_above',
            'close_crossed_below',
            'close_equal',
            'mstd_above',
            'mstd_below',
            'mstd_crossed_above',
            'mstd_crossed_below',
            'mstd_equal',
        ],
        'props': [
            'close',
            'ewm_list',
            'mstd',
            'window_list'
        ]
    },

    'OBV'   : {
        'sig': "run(close, volume, short_name='obv')",
        'params': {'short_name':'obv'},
        'name':'OBV',
        'methods': [
            'close_above',
            'close_below',
            'close_crossed_above',
            'close_crossed_below',
            'close_equal',
            'obv_above',
            'obv_below',
            'obv_crossed_above',
            'obv_crossed_below',
            'obv_equal',
            'volume_above',
            'volume_below',
            'volume_crossed_above',
            'volume_crossed_below',
            'volume_equal'
        ],
        'props': [
            'close',
            'obv',
            'volume'
        ]
    },

    'RSI'   : {
        'sig': "run(close, window=14, ewm=False, short_name='rsi')",
        'params': {'window':14, 'ewm':False, 'short_name':'rsi'},
        'name':'RSI',
        'methods': [
            'close_above',
            'close_below',
            'close_crossed_above',
            'close_crossed_below',
            'close_equal',
            'rsi_above',
            'rsi_below',
            'rsi_crossed_above',
            'rsi_crossed_below',
            'rsi_equal'
        ],
        'props':[
            'close',
            'ewm_list',
            'rsi',
            'window_list'
        ]
    },

    'STOCH' : {
        'sig': "run(high, low, close, k_window=14, d_window=3, d_ewm=False, short_name='stoch')",
        'params': {'k_window':14, 'd_window':3, 'd_ewm':False, 'short_name':'stoch'},
        'name':'STOCH',
        'methods': [
            'close_above',
            'close_below',
            'close_crossed_above',
            'close_crossed_below',
            'close_equal',
            'high_above',
            'high_below',
            'high_crossed_above',
            'high_crossed_below',
            'high_equal',
            'low_above',
            'low_below',
            'low_crossed_above',
            'low_crossed_below',
            'low_equal',
            'percent_d_above',
            'percent_d_below',
            'percent_d_crossed_above',
            'percent_d_crossed_below',
            'percent_d_equal',
            'percent_k_above',
            'percent_k_below',
            'percent_k_crossed_above',
            'percent_k_crossed_below',
            'percent_k_equal'
        ],
        'props': [
            'close',
            'd_ewm_list',
            'd_window_list',
            'high',
            'k_window_list',
            'low',
            'percent_d',
            'percent_k'
        ]
    }
}

