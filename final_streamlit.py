import streamlit as st
import pandas as pd
from datetime import timezone
from datetime import datetime
import numpy as np
import altair as alt
import streamlit.components.v1 as components
from PIL import Image
#from nomics import Nomics
import time
import requests
from stream_helper import *
from W209_final_midterm_viz import *


#configure page_title


def startup():

    #configure page
    st.set_page_config(
         page_title='Crypto Dashboard',
         layout="wide",
         initial_sidebar_state="expanded",
    )

    #title and subheader
    st.title("Crypto Dashboard")
    st.subheader("Mickey Piekarski, Varun Dashora, Noor Gill, Marcus Manos")

    #currencies our app supports
    global currencies_name
    currencies_name = ['BTC', 'ETH', 'BNB', 'USDT', 'SOL','AVAX', 'USDC', ]


def sidebar():
    #creating the sidebar

    img = Image.open("cryptoreview_logo.jpg")
    st.sidebar.image(img, width = 100)
    st.sidebar.write("Send us some [feedback](https://docs.google.com/forms/d/e/1FAIpQLSeW1-wPirsWOBxF8VSJUxIGd1bM9BnT55cX5EXK6atmzAO3Hw/viewform?usp=sf_link)!")

    #choose coin option
    global coin
    coin = st.sidebar.selectbox(\
    'Which coin would you like to view', currencies_name)
    st.sidebar.write('You selected: ', coin)

    #choose timerame
    global option1
    option1 = st.sidebar.selectbox(\
    'Date range (years)', ['YTD',0.5,1,2,3,4,5,])
    st.sidebar.write('You selected: ', option1)

    ## goal, intended audience, data sources
    st.sidebar.markdown("""
    **Goal:** Our goal is to help users understand cryptocurrency trends relating to price and media/Reddit sentiment through visualizations in order to assist in decision-making for investment portfolios.
    **Intended Audience:** The intended audience is both professional and amateur cryptocurrency investors who wish to use these metrics and data to refine their portfolios. A secondary audience would be financial or economic researchers who wish to use this information to assist their analysis of the market.
    **Data sources:** Cryptoreview.ai and Nomics.api
    """)


#start up api
def startup_api_load_data():

    """
    df: price history of coin chosen
    reddit: reddit posts information
    currencies: metadata of coin ( volume, price, img etc)
    """
    global df
    global reddit
    global currencies
    global ytd
    # nomics api call
    key = st.secrets["nomics-key"]["key"]
    nomics = Nomics(key)
    markets = nomics.ExchangeRates.get_history(currency = coin, start = '2015-10-02T15:00:00.05Z')

    #NOTE: we must sleep for 1 sewcond after each API call bc we are only allowd one call per second

    time.sleep(1)

    df = pd.DataFrame(markets)

    #will need to change on new year
    ytd = df[df['timestamp']>'2021']
    if option1 == 'YTD':
        df = ytd.copy()
    else:
        df = df.tail(int(364 * option1))


    #hackey solution to final reddti viz

    df = load_data(df)
    ytd = load_data(ytd)
    reddit = pd.read_csv('data_for_viz_project_dec052021.csv')
    currencies  = nomics.Currencies.get_currencies(coin)
    currencies = pd.DataFrame(currencies)





def coin_metadata():

    col1, col2,col3, col4 = st.columns(4)

    #display coin logo
    with col1:
        logo = np.array(currencies['logo_url'])[0]
        st.image(logo,width = 100)

    #display price (with change)
    with col2:
        val1 = currencies['price'][0]
        val2 = currencies['1d'][0]['price_change']
        st.metric("Price",smart_num(val1), smart_num(val2))

    #display volume (with change)
    with col3:
        val1 = currencies['1d'][0]['volume']
        val2 = currencies['1d'][0]['volume_change']
        st.metric("Volume 1d",smart_num(val1),smart_num(val2))

    #display market cap (with change)
    with col4:
        val3 = currencies['market_cap'][0]
        val4 = currencies['1d'][0]['market_cap_change']
        st.metric("Market Cap", smart_num(val3),smart_num(val4))




def VIZ_TIME_BABY():

    #creating the charts
    candle = candlestick_chart(df)
    volatility = volatlilty_chart(df,'10-day STD:Q')
    ra1,ra2 = rolling_avg_std(df)
    reddit_chart = reddit_posts_and_price(ytd,reddit,coin)
    percent = percent_change(df)


    #wide candlestick_chart
    st.altair_chart(candle,use_container_width = True)

    col1b, col2b = st.columns(2)

    # first column volatility rolling average 1 and reddit
    with col1b:
        st.altair_chart(volatility,use_container_width = True)
        st.altair_chart(ra1,use_container_width = True)


    #colums 2 percent change and rolling average 2 chart
    with col2b:
        st.altair_chart(percent,use_container_width = True)
        st.altair_chart(ra2,use_container_width = True)
    st.altair_chart(reddit_chart, use_container_width = True)


if __name__ == "__main__":
    startup()
    sidebar()
    try:
        startup_api_load_data()
        coin_metadata()
        VIZ_TIME_BABY()
    except ValueError:
        st.write("OOPS! Our api only allows us one call per second.  Someone else must be using the site. Give it a moment and try again.")
