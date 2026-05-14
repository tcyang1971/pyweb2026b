import requests
from bs4 import BeautifulSoup

from flask import Flask, render_template, request
from datetime import datetime

import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

# 判斷是在 Vercel 還是本地
if os.path.exists('serviceAccountKey.json'):
    # 本地環境：讀取檔案
    cred = credentials.Certificate('serviceAccountKey.json')
else:
    # 雲端環境：從環境變數讀取 JSON 字串
    firebase_config = os.getenv('FIREBASE_CONFIG')
    cred_dict = json.loads(firebase_config)
    cred = credentials.Certificate(cred_dict)

firebase_admin.initialize_app(cred)



app = Flask(__name__)

@app.route("/")
def index():
    link = "<h1>歡迎進入楊子青的網站20260409</h1>"
    link += "<a href=/mis>課程</a><hr>"
    link += "<a href=/today>現在日期時間</a><hr>"
    link += "<a href=/me>關於我</a><hr>"
    link += "<a href=/welcome?u=子青&d=靜宜資管&c=資訊管理導論>Get傳值</a><hr>"
    link += "<a href=/account>POST傳值</a><hr>"
    link += "<a href=/read>讀取Firestore資料</a><hr>"
    link += "<a href=/read2>讀取Firestore資料(根據姓名關鍵字:楊)</a><hr>"
    link += "<a href=/spider1>爬取子青老師課程資料</a><hr>"
    link += "<a href=/spiderMovie>爬取即將上映電影</a><hr>"
    link += "<a href=/road>台中市十大肇事路口</a><hr>"
    link += "<a href=/rate>本週新片進DB</a><hr>"
    return link


@app.route("/rate")
def rate():
    #本週新片
    url = "https://www.atmovies.com.tw/movie/new/"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    sp = BeautifulSoup(Data.text, "html.parser")
    lastUpdate = sp.find(class_="smaller09").text[5:]
    print(lastUpdate)
    print()

    result=sp.select(".filmList")

    for x in result:
        title = x.find("a").text
        introduce = x.find("p").text

        movie_id = x.find("a").get("href").replace("/", "").replace("movie", "")
        hyperlink = "http://www.atmovies.com.tw/movie/" + movie_id
        picture = "https://www.atmovies.com.tw/photo101/" + movie_id + "/pm_" + movie_id + ".jpg"

        r = x.find(class_="runtime").find("img")
        rate = ""
        if r != None:
            rr = r.get("src").replace("/images/cer_", "").replace(".gif", "")
            if rr == "G":
                rate = "普遍級"
            elif rr == "P":
                rate = "保護級"
            elif rr == "F2":
                rate = "輔12級"
            elif rr == "F5":
                rate = "輔15級"
            else:
                rate = "限制級"

        t = x.find(class_="runtime").text

        t1 = t.find("片長")
        t2 = t.find("分")
        showLength = t[t1+3:t2]

        t1 = t.find("上映日期")
        t2 = t.find("上映廳數")
        showDate = t[t1+5:t2-8]

        doc = {
            "title": title,
            "introduce": introduce,
            "picture": picture,
            "hyperlink": hyperlink,
            "showDate": showDate,
            "showLength": int(showLength),
            "rate": rate,
            "lastUpdate": lastUpdate
        }

        db = firestore.client()
        doc_ref = db.collection("本週新片含分級B班").document(movie_id)
        doc_ref.set(doc)
    return "本週新片已爬蟲及存檔完畢，網站最近更新日期為：" + lastUpdate




@app.route("/road")
def road():
    R = "<h1>台中市十大肇事路口(113年10月) 作者:楊子青</h1><br>"

    url = "https://datacenter.taichung.gov.tw/swagger/OpenData/a1b899c0-511f-4e3d-b22b-814982a97e41"

    # 1. 準備帽子 (Headers)
    headers = {'User-Agent': 'Mozilla/5.0'}

    # 設定 Header，讓伺服器以為是正常的瀏覽器在訪問
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    # 2. 把參數加進去
    Data = requests.get(url, headers=headers, timeout=10)
    #print(Data.text)

    JsonData = json.loads(Data.text)
    for item in JsonData:
        R += item["路口名稱"] + ",原因:" + item["主要肇因"] + ",件數:" + item["總件數"] + "<br>"

    return R



@app.route("/spiderMovie")
def spiderMovie():
    R = ""

    db = firestore.client()
    url = "http://www.atmovies.com.tw/movie/next/"
    Data = requests.get(url)
    Data.encoding = "utf-8"

    sp = BeautifulSoup(Data.text, "html.parser")
    lastUpdate = sp.find(class_="smaller09").text.replace("更新時間：", "")


    result=sp.select(".filmListAllX li")
    total = 0
    for item in result:
      total += 1
      movie_id = item.find("a").get("href").replace("/movie/", "").replace("/", "")
      title = item.find(class_="filmtitle").text
      picture = "https://www.atmovies.com.tw" + item.find("img").get("src")
      hyperlink = "https://www.atmovies.com.tw" + item.find("a").get("href")

      showDate = item.find(class_="runtime").text[5:15]

      doc = {
          "title": title,
          "picture": picture,
          "hyperlink": hyperlink,
          "showDate": showDate,
          "lastUpdate": lastUpdate
      }

      doc_ref = db.collection("電影2B").document(movie_id)
      doc_ref.set(doc)

    R += "網站最近更新日期:" + lastUpdate + "<br>"
    R += "總共爬取" + str(total) + "部電影到資料庫"

    return R

@app.route("/spider1")
def spider1():
    R = ""
    url = "https://www1.pu.edu.tw/~tcyang/course.html"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    sp = BeautifulSoup(Data.text, "html.parser")
    result=sp.select(".team-box a")

    for i in result:
        R += i.text + i.get("href") + "<br>" 
    return R

@app.route("/read2")
def read2():
    Result = ""
    keyword = "楊"
    db = firestore.client()
    collection_ref = db.collection("靜宜資管2026B")    
    docs = collection_ref.get()
    for doc in docs: 
        teacher = doc.to_dict()
        if keyword in teacher["name"]:        
            Result += str(teacher) + "<br>"

    if Result == "":
        Result = "抱歉,查無此關鍵字姓名之老師資料"    
    return Result

@app.route("/read")
def read():
    Result = ""
    db = firestore.client()
    collection_ref = db.collection("靜宜資管2026B")    
    docs = collection_ref.get()
    docs = collection_ref.order_by("lab", direction=firestore.Query.DESCENDING).get()
    for doc in docs:         
        Result += str(doc.to_dict()) + "<br>"    
    return Result

@app.route("/mis")
def course():
    return "<h1>資訊管理導論</h1><a href=/>返回首頁</a>"

@app.route("/today")
def today():
    now = datetime.now()
    return render_template("today.html", datetime=str(now))

@app.route("/me")
def me():
    return render_template("mis2026b.html")

@app.route("/welcome", methods=["GET"])
def welcome():
    user = request.values.get("u")
    d = request.values.get("d")
    c = request.values.get("c")    
    return render_template("welcome.html", name= user, dep = d, course = c)


@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        user = request.form["user"]
        pwd = request.form["pwd"]
        result = "您輸入的帳號是：" + user + "; 密碼為：" + pwd 
        return result
    else:
        return render_template("account.html")


if __name__ == "__main__":
    app.run(debug=True)
