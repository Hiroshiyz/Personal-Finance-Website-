import os
from flask import Flask, render_template, request, g, redirect
# Flask 框架 #render_template render web page #requset http request #g SQL一個method #redirect導回
import sqlite3
import requests
import math
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('agg')
app = Flask(__name__)
DATABASE = 'datafile.db'

# 使用sqlite3 in Flask


def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = sqlite3.connect(DATABASE)
    return g.sqlite_db


@app.teardown_appcontext
def close_connection(exception):  # 任何http request都會執行
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

# render homepage


@app.route('/')
def home():
    conn = get_db()
    cursor = conn.cursor()
    # 取得所有現今資訊
    result = cursor.execute("select * from cash")
    cash_result = result.fetchall()
    # print(cash_result)  # list of tuple
    # 計算台幣和美金
    taiwanese_dollars = 0
    us_dollars = 0
    # 將每筆金額都加總起來
    for data in cash_result:
        taiwanese_dollars += data[1]
        us_dollars += data[2]
    r = requests.get('https://tw.rter.info/capi.php')  # http response API
    currency = r.json()
    # print(currency['USDTWD']['Exrate'])#j.son內部dict的key對應的value就是美金轉台幣 現價...

    # 另外將自己輸入的台幣和美金和匯率轉換後加總的等於總額
    total = math.floor(taiwanese_dollars + us_dollars *
                       currency['USDTWD']['Exrate'])
# -------------------------------------------------------------------------------------------------
    # 取得所有股票資訊
    result_2 = cursor.execute("select * from stock")
    stock_reult = result_2.fetchall()
    # print(stock_reult)debug用

    # 為了避免購買的股票分開來算例如2330買了三次都在不同價位
    unique_stock_list = []
    for data in stock_reult:
        if data[1] not in unique_stock_list:
            unique_stock_list.append(data[1])
    # 計算股票總市值
    total_stock_vlaue = 0
    # 計算單一股票資訊
    # cursor.execute("delete from stock")

    stock_info = []
    for stock in unique_stock_list:
        result = cursor.execute(
            "select * from stock where stock_id=?", (stock,))

        result = result.fetchall()
        stock_cost = 0  # 單一股票總花費
        shares = 0  # 單一股票股數

        for d in result:
            shares += d[2]
            stock_cost += d[2] * d[3] + d[4] + d[5]
            print(d[3])
        # 取得目前股價 API
        url = "https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&stockNo=" + stock
        response = requests.get(url)
        data = response.json()
        price_array = data['data']  # 抓取API內的keuword data
        # 最後一個通常代表最靠近現在的股價 [6]是現在股價 其他位置則是開盤...諸如此類 (都是string)
        current_price = float(
            price_array[len(price_array)-1][6].replace(',', ''))
        # 單一股票總市值  股價*股數
        total_value = int(current_price * shares)
        # 所有股票總市值
        total_stock_vlaue += total_value
        # 單一股票平均成本
        average_cost = round(stock_cost / shares, 2)
        # 單一股票報酬率 總市值-總花費 / 花費 等於報酬率 分母*100轉成 %
        rate_of_return = round((total_value - stock_cost)*100 / stock_cost, 2)
        # 單一股票獲利金額
        stock_profit = int(total_value - stock_cost)
        stock_info.append({'stock_id': stock, 'stock_cost': stock_cost,
                          'total_value': total_value, 'average_cost': average_cost, 'shares': shares, 'current_price': current_price, 'rate_of_return': rate_of_return, "stock_profit": stock_profit})
    # 股票資產占比
    for stock in stock_info:
        # 單一股票總市值*100 / 所有股票總市值
        stock['value_percenatge'] = round(
            stock['total_value'] * 100 / total_stock_vlaue, 2)
    # 繪製股票圓餅圖
    if len(unique_stock_list) != 0:
        labels = tuple(unique_stock_list)
        sizes = [d['total_value'] for d in stock_info]
        fig, ax = plt.subplots(figsize=(6, 5))
        ax.pie(sizes, labels=labels, autopct=None, shadow=None)
        fig.subplots_adjust(top=1, bottom=0, right=1,
                            left=0, hspace=0, wspace=0)
        plt.savefig("static/piechart.jpg", dpi=200)
    else:
        # 如果所有資料都被刪除就remove
        try:
            os.remove("static/piechart.jpg")
        except:
            pass
    # 繪製股票現金圓餅圖
    if us_dollars != 0 and taiwanese_dollars != 0 and total_stock_vlaue != 0:
        labels = ('USD', "TWD", "Stock")
        sizes = (us_dollars *
                 currency['USDTWD']['Exrate'], taiwanese_dollars, total_stock_vlaue)
        fig, ax = plt.subplots(figsize=(6, 5))
        ax.pie(sizes, labels=labels, autopct=None, shadow=None)
        fig.subplots_adjust(top=1, bottom=0, right=1,
                            left=0, hspace=0, wspace=0)
        plt.savefig("static/piechart2.jpg", dpi=200)
        # 如果所有資料都被刪除就remove
    else:
        try:
            os.remove("static/piechart2.jpg")
        except:
            pass
    #  用一個dict 給html讀取資料
    data = {'show_pic_1': os.path.exists('static/piechart.jpg'), 'show_pic_2': os.path.exists('static/piechart2.jpg'),
            'total': total, 'currency': currency['USDTWD']
            ['Exrate'], 'ud': us_dollars, 'td': taiwanese_dollars, 'cash_result': cash_result, 'stock_info': stock_info}
    return render_template('index.html', data=data)

# render cashpage


@app.route('/cash')
def cash_form():
    return render_template('cash.html')

# 更新金融帳戶


@app.route('/cash', methods=['POST'])
def submit_cash():
    # get the data
    taiwanese_dollars = 0
    us_dollars = 0
    # 抓取html name的data
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

# 刪除的功能


@app.route('/cash-delete', methods=['POST'])
def cash_delete():
    # 抓到html的id name這格並向sqlitedb內的 transaction_id抓到該筆資料並刪除
    transaction_id = request.values['id']
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """delete from cash where transaction_id=?""", (transaction_id,))
    conn.commit()
    return redirect("/")

# render /stock


@app.route('/stock')
def stock_form():
    return render_template('stock.html')


@app.route('/stock', methods=['POST'])
def submit_stock():
    # 抓取html取得股票資訊 日期資料
    stock_id = request.values['stock-id']
    stock_num = request.values['stock-num']
    stock_price = request.values['stock-pirce']
    # 有可能有人沒有手續費 and tax等問題所以要改成 = 0
    processing_fee = 0
    tax = 0
    if request.values['processing-fee'] != "":
        processing_fee = request.values['processing-fee']
    if request.values['tax'] != "":
        tax = request.values['tax']
    date = request.values['date']
    # 更新資料庫
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""insert into stock(stock_id, stock_num, stock_price, processing_fee, tax, date_info) values(?, ?, ?, ?, ?, ?)""",
                   (stock_id, stock_num, stock_price, processing_fee, tax, date))
    conn.commit()
    # 將使用者導回
    return redirect('/')  # 302


@app.route('/stock-delete', methods=['POST'])
def stock_delete():
    # 抓到html的id name這格並向sqlitedb內的 stock_id抓到該筆資料並刪除
    stock_id = request.values['id2']
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """delete from stock where stock_id=?""", (stock_id,))
    conn.commit()
    return redirect("/")


if __name__ == '__main__':
    app.run(debug=True)
# 在 Flask 應用程式中，if __name__ == '__main__': 只有在直接執行當前 Python 文件時，才會啟動 Flask 伺服器。
