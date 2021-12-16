from flask import Flask, render_template, send_file, request
from W209_final_midterm_viz import *
import time
app = Flask(__name__)

def reload_charts(coin="BTC", option=1):
    key = "266dbf914fd18fad344fcf6e0937362695777573"
    nomics = Nomics(key)
    markets = nomics.ExchangeRates.get_history(currency = coin, start = '2015-10-02T15:00:00.05Z')
    time.sleep(1)

    df = pd.DataFrame(markets)

    #will need to change on new year
    ytd = df[df['timestamp']>'2021']
    if option == 'YTD':
        df = ytd.copy()
    else:
        df = df.tail(int(364 * option))

    df = load_data(df)
    ytd = load_data(ytd)
    reddit = pd.read_csv('data_for_viz_project_dec052021.csv')
    currencies  = nomics.Currencies.get_currencies(coin)
    currencies = pd.DataFrame(currencies)

    candle = candlestick_chart(df).to_json()
    volatility = volatlilty_chart(df,'10-day STD:Q').to_json()
    ra1,ra2 = rolling_avg_std(df)
    ra1 = ra1.to_json()
    ra2 = ra2.to_json()
    reddit_chart = reddit_posts_and_price(ytd,reddit,coin).to_json()
    percent = percent_change(df).to_json()

    return dict(coin=coin, time=option, cdl=candle, vol=volatility, ra1=ra1, ra2=ra2, red=reddit_chart, per=percent)

@app.route("/")
def index():
    return render_template('index.html', **reload_charts())

@app.route("/<fn>")
def get_file(fn):
    text = send_file(fn)
    return text

@app.route("/request_coin", methods=["GET", "POST"])
def request_coin():
    coin = request.form['coin']
    time = float(request.form['time'])
    print(coin, time)
    
    return render_template('index.html', **reload_charts(coin, time))

if __name__ == "__main__":
    reload_charts()
    app.run()