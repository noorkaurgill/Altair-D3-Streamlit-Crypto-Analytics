# -*- coding: utf-8 -*-

# -- Sheet --

from nomics import Nomics
import pandas as pd
from datetime import timezone
from datetime import datetime
import numpy as np
import altair as alt

# from fbprophet import Prophet
import matplotlib.pyplot as plt


key = "266dbf914fd18fad344fcf6e0937362695777573"
nomics = Nomics(key)



"""
Functions included:

 - load_data: returns data in a standardized format
 - candlestick_chart: creates our candlestick chart
 - get_mape: i have no clue tbh
 - create_forecasting_chart: supposed to create  (you gessued it) a forecasting chart.
    currently doesn't work. not deployed.
 - volatility_chart: creates out volatility chart
 - percent_change: creates our percent change chart
 - rolling_avg_std: returns two charts. rolling average and stdev against time
 - reddit_posts_and_price: returns the reddit viz
 """



def load_data(df):

    #gets the 10 day real volatlilty variance swap and classical ways, and 10-day STD
    def getvol(df, window):
        df = df.sort_values(by=['Date'], ascending=True)
        df[str(window) + '-day STD'] = df['rate'].rolling(10).std()

        df['log_rtn'] = np.log(df['rate']).diff()

        ann_factor = 365/window
        window = window
        # Var Swap (returns are not demeaned)
        df[str(window) + 'real_var'] = np.square(df['log_rtn']).rolling(window).sum() * ann_factor
        df[str(window) + 'real_vol'] = np.sqrt(df[str(window) + 'real_var'])

        # Classical (returns are demeaned, dof=1)
        df[str(window) + 'real_var'] = df['log_rtn'].rolling(window).var() * ann_factor
        df[str(window) + 'real_vol'] = np.sqrt(df[str(window) + 'real_var'])
        df = df.sort_values(by=['Date'], ascending=False)
        return df

    df['rate'] = df['rate'].astype(float)
    df['close'] = df['rate'][1:].shift(-1)
    df['Date'] = pd.to_datetime(pd.to_datetime(df['timestamp']).dt.date)
    df = getvol(df, 10)
    df = df.rename(columns={'rate': 'open'})
    df['percent_change'] = (df['open'] - df['close']) / df['close']
    df['Low'] = df.loc[:,'open':'close'].min(axis=1)
    df['High'] = df.loc[:,'open':'close'].max(axis=1)
    df = df.fillna(method="pad")
    df = df.fillna(method="bfill")

    return df


def candlestick_chart(df):
    """

    Creates the Candle stick chart

    """
    open_close_color = alt.condition("datum.open <= datum.close",
                                    alt.value("#06982d"),
                                    alt.value("#ae1325"))

    base = alt.Chart(df).encode(
            alt.X('Date:T',
                axis=alt.Axis(
                    title='Date',
                    grid = False
                )
            ),
            color=open_close_color,
            tooltip=[alt.Tooltip('Date:T'), alt.Tooltip('open:Q', format='$'),
                    alt.Tooltip('close:Q', format='$')]
        ).properties(width=800)

    rule = base.mark_rule().encode(
            alt.Y(
                'Low:Q',
                title='Price',
                scale=alt.Scale(zero=False),
            ),
            alt.Y2('High:Q')
        )

    bar = base.mark_bar().encode(
            alt.Y('open:Q'),
            alt.Y2('close:Q')
        )

    all = rule + bar
    return all.properties(title='Price of Currency over Time', height=500).interactive()


# Prophet Time series forcasting


def get_mape(actuals, forecasts):
    MAPE = np.mean(np.abs(forecasts - actuals) / (actuals))
    return MAPE


def volatlilty_chart(df, vol):
    vol_chart = alt.Chart(df).mark_line(tooltip=True).encode(
            x=alt.X('Date:T', title='Date', axis=alt.Axis( grid = False)),
            y=alt.Y(vol, title='Volatlilty', axis=alt.Axis(labels=True, tickSize=0))
            )

    total = vol_chart
    return total.properties(title="Volatility Over Time", height=500).interactive()


def percent_change(df):
    chart = alt.Chart(df).mark_bar().encode(
        alt.X("Date:T"),
        alt.Y("percent_change:Q", title='Percentage Change'),
        color=alt.condition("datum.percent_change < 0",
                                    alt.value("#ae1325"),
                                    alt.value("#06982d")),
        tooltip= ['Date:T', 'percent_change']
    ).properties(height=500)

    return chart.properties(title='Percentage Change of Currency Over Time', height=500).interactive()

#percent_change(sample_df)

# Rolling avg and std chart:
def rolling_avg_std(df):
    chart1 = alt.Chart(df).mark_line().encode(
        alt.X("Date:T"),
        alt.Y("close:Q", title='Close'),
        tooltip= ['Date:T', 'close:Q']
    ).properties(height=500, title='Closing Price Over Time with Moving Average')

    moving_avg = alt.Chart(df).mark_line(
        color='red',
        size=3
    ).transform_window(
        rolling_mean='mean(close)'
    ).encode(
        x='Date:T',
        y='rolling_mean:Q',
        tooltip = ['Date:T','mean(close)']
    )

    chart2 = alt.Chart(df).mark_line().encode(
        alt.X("Date:T"),
        alt.Y("close:Q", title='Close'),
        tooltip= ['Date:T', 'close:Q']
    ).properties(height=500, title='Closing Price Volatility Based on Moving Standard Deviation')

    moving_std = alt.Chart(df).mark_line(
        color='lightblue',
        size=3
    ).transform_window(
        rolling_std='stdev(close)'
    ).encode(
        x='Date:T',
        y='rolling_std:Q',
        tooltip = ['Date:T', 'rolling_std:Q']
    )

    return (chart1 + moving_avg).interactive(), (chart2 + moving_std).interactive()



def reddit_posts_and_price(price, reddit, token):

    def load_reddit(df, token):
        red = df
        red['date'] = pd.to_datetime(red['datetime_hour']).dt.date #get the date
        red = red[red['ticker'] == token]
        red = red.groupby(by=['signal', 'date', 'ticker']).agg({'value_day': 'sum'}) #aggregate by day
        return red.filter(like='reddit_submission_num_posts', axis=0).reset_index() #filter to get submission numbers

    reddit = load_reddit(reddit, token)
    base1 = alt.Chart(price).encode(x=alt.X('Date:T', title='Date'))

    bar = base1.mark_bar(color = 'lightblue').encode(
        alt.Y('close:Q'))

    reddit['date'] = reddit['date'].astype(str)
    base2 = alt.Chart(reddit).encode(x=alt.X('date:T', title=''))

    line = base2.mark_line(color = 'red').encode(
        alt.Y('value_day:Q', title='Posts per day'))

    chart = alt.layer(bar, line).resolve_scale(y='independent').encode(
            tooltip=['Date:T', 'close:Q']
        )

    return chart.properties(height=500, title='Currency Price in Relation to Number of Reddit Posts Over Time. NOTE: Only YTD Data').interactive()
