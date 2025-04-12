from flask import Flask, render_template, request, g, redirect
# Flask 框架 #render_template render web page #requset http request #g SQL一個method #redirect導回
import sqlite3
import requests
import math


app = Flask(__name__)
DATABASE = 'datafile.db'


def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = sqlite3.connect(DATABASE)
    return g.sqlite_db


@app.teardown_appcontext
def close_connection(exception):  # 任何http request都會執行
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


@app.route('/')
def home():
    conn = get_db()
    cursor = conn.cursor()
    result = cursor.execute("select * from cash")
    cash_result = result.fetchall()
    # print(cash_result)  # list of tuple
    # 計算台幣和美金
    taiwanese_dollars = 0
    us_dollars = 0
    for data in cash_result:
        taiwanese_dollars += data[1]
        us_dollars += data[2]
    r = requests.get('https://tw.rter.info/capi.php')  # http response
    currency = r.json()
    # print(currency['USDTWD']['Exrate'])#j.son內部dict的key對應的value就是美金轉台幣 現價...

    # 另外將自己輸入的台幣和美金和匯率轉換後加總的等於總額
    total = math.floor(taiwanese_dollars + us_dollars *
                       currency['USDTWD']['Exrate'])
    # 用一個dict 給html讀取資料
    data = {'total': total, 'currency': currency['USDTWD']
            ['Exrate'], 'ud': us_dollars, 'td': taiwanese_dollars}
    return render_template('index.html', data=data)


@app.route('/cash')
def cash_form():
    return render_template('cash.html')


@app.route('/cash', methods=['POST'])
def submit_cash():
    # get the data
    taiwanese_dollars = 0
    us_dollars = 0
    if request.values['taiwanese-dollars'] != "":
        taiwanese_dollars = request.values['taiwanese-dollars']
    if request.values['us-dollars'] != "":
        us_dollars = request.values['us-dollars']
    note = request.values['note']
    date = request.values['date']

    # update DATABASE
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """insert into cash (taiwanese_dollars, us_dollars, note, date_info) values(?, ?, ?, ?)""", (taiwanese_dollars, us_dollars, note, date))

    conn.commit()
    # return home page
    return redirect("/")  # 302


@app.route('/stock')
def stock_form():
    return render_template('stock.html')


if __name__ == '__main__':
    app.run(debug=True)
