# -*- coding:utf-8 -*-
import time
import urllib
from flask import Flask, render_template, request, redirect, flash, session, send_file
from passlib.hash import sha256_crypt
from bs4 import BeautifulSoup
from datetime import datetime
from io import BytesIO, StringIO  # 그래프를 이미지로 저장하기위한 변환 라이브러리
import pymysql
import matplotlib.pyplot as plt
import numpy as np
import requests
import pandas as pd
from pandas.io import sql
from sqlalchemy import create_engine
import tqdm

app = Flask(__name__)

app.secret_key = 'my_secret_key'

db = pymysql.connect(
            host='localhost',
            port=3306,
            user='root',
            password='1234',
            db='flasktest'
        )


# 메인 화면& 로그인
@app.route('/', methods=['GET', 'POST'])
def index():
    if session.get('is_logged') is not None:
        if session.get('is_logged') == "g":
            return render_template("index.html", user="GUEST")
        else:
            return render_template("index.html", user=session.get('is_logged'))
    elif request.method == "POST":
        cursor = db.cursor()
        sql = 'SELECT PW FROM login where ID = %s;'
        userID = request.form['Username']
        userPW = request.form['psword']
        cursor.execute(sql, userID)
        user = cursor.fetchone()
        if user is None:
            flash("없는 아이디입니다.")
        elif sha256_crypt.verify(userPW, user[0]):
            session['is_logged'] = userID
            return render_template("index.html", user=session.get('is_logged'))
        else:
            flash("틀린 비밀번호입니다.")
        return render_template("log_in.html")
    else:
        return render_template("log_in.html")


# 게스트 로그인
@app.route('/guest', methods=['GET', 'POST'])
def guest():
    session['is_logged'] = "g"
    return render_template("index.html", user="GUEST")


# 회원가입 기능
@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        cursor = db.cursor()
        name = request.form['Name']
        email = request.form['Email']
        userID = request.form['Username']
        userPW = sha256_crypt.encrypt(request.form['psword'])
        sql_insert = "INSERT INTO `login` (`name`, `email`, `ID` , `PW`) VALUES (%s, %s, %s, %s);"
        val = [name, email, userID, userPW]
        cursor.execute(sql_insert, val)
        db.commit()
        db.close()
        return redirect("/")
    else:
        return render_template("register.html")


# 로그아웃 기능
@app.route('/log_out')
def log_out():
    session.clear()
    return redirect("/")


# 오늘의 네이버 웹툰 랭킹
@app.route('/webtoons', methods=["GET", "POST"])
def webtoons():
    if session.get('is_logged') is not None:
        res = requests.get('https://comic.naver.com/webtoon/weekday.nhn')
        soup = BeautifulSoup(res.text, 'html.parser')
        title_list = soup.select('a.title')
        titles = []
        count = 1
        for i in title_list:
            if i.get('href')[-3:] == datetime.today().strftime('%A')[:3].lower():
                title = [f'{count:2d}위', i.get_text(), i.get('href')]
                print(i.get_text())
                titles.append(title)
                count += 1
            else:
                continue
        return render_template("webtoons.html", webtoons=titles,
                               today=datetime.today().strftime('%A').upper(),
                               webtoonsize=len(titles))
    else:
        return render_template("log_in.html")


# 주식 탭
@app.route('/stocks/refresh', methods=["GET", "POST"])
def stocks_refresh():
    cursor = db.cursor()
    # if request.method == "POST":
    input_df = all_upjong_list()
    # print(type(input_df))
    # cursor.execute("truncate flasktest.stock")
    # db.commit()
    db_connection_str = 'mysql+pymysql://root:1234@localhost/flasktest'
    db_connection = create_engine(db_connection_str)
    # conn = db_connection.connect()
    input_df.to_sql(name='stock', con=db_connection, if_exists='replace', index=False)
    # sql_insert = "INSERT INTO `flasktest`.`stock` (`name`, `upjong`, `upjong_no`) VALUES (%s, %s, %s);"
    # val = [title, desc, author]
    # cursor.execute(sql_insert, val)
    # db.commit()
    # db.close()
    return redirect("/stocks")
    # else:
    #     return render_template("add_notes.html", user=session.get('is_logged'))


def one_upjong_list(page, upjong):
    STOCKLIST_URL = page  # 주소설정
    response = urllib.request.urlopen(STOCKLIST_URL)
    soup = BeautifulSoup(requests.get(STOCKLIST_URL).content.decode('euc-kr', 'replace'), 'html.parser')
    STOCK_NAME_LIST = []
    STOCK_NUMBER_LIST = []
    STOCK_URL_LIST = []

    for tr in soup.findAll('tr'):
        stockName = tr.findAll('a')
        if stockName is None or stockName == []:
            pass
        else:
            STOCK_NUMBER_LIST.append(stockName[0].get('href')[-6:])
            STOCK_URL_LIST.append("https://finance.naver.com/" + stockName[0].get('href'))
            stockName = stockName[0].get_text()
            STOCK_NAME_LIST.append(stockName)
            # print(type(stockName))
    STOCK_LIST = []
    for i in range(len(STOCK_NAME_LIST)):
        stockInfo = [upjong, STOCK_NAME_LIST[i], STOCK_NUMBER_LIST[i], STOCK_URL_LIST[i]]
        STOCK_LIST.append(stockInfo)

    return pd.DataFrame(STOCK_LIST, columns=('업종', '종목명', '종목번호', 'URL'))


def all_upjong_list():
    UPJONG_URL = 'https://finance.naver.com/sise/sise_group.nhn?type=upjong'  # 주소설정
    response = urllib.request.urlopen(UPJONG_URL)
    soup = BeautifulSoup(requests.get(UPJONG_URL).content.decode('euc-kr', 'replace'), 'html.parser')
    UPJONG_NAME_LIST = []
    UPJONG_URL_LIST = []

    for tr in soup.findAll('tr'):
        upjongName = tr.findAll('a')
        if upjongName is None or upjongName == []:
            pass
        elif upjongName[0].get('class') is None:
            UPJONG_URL_LIST.append("https://finance.naver.com" + upjongName[0].get('href'))
            upjongName = upjongName[0].get_text()
            UPJONG_NAME_LIST.append(upjongName)

    FINAL_LIST = []

    for index in range(len(UPJONG_URL_LIST)):
        one_upjong_data = one_upjong_list(UPJONG_URL_LIST[index], UPJONG_NAME_LIST[index])
        print("전체 {}개 중 {} 번 째\t{} 페이지".format(len(UPJONG_URL_LIST), index + 1, UPJONG_NAME_LIST[index]))
        if one_upjong_data is None:
            break
        FINAL_LIST.append(one_upjong_data)
    return pd.concat(FINAL_LIST, ignore_index=True)


# 주식 db 목록 읽어오는 기능
@app.route('/stocks', methods=["GET", "POST"])
def stocks():
    if session.get('is_logged') is not None:
        cursor = db.cursor()
        sql = 'SELECT * FROM stock'
        cursor.execute(sql)
        topics = cursor.fetchall()
        # articles = Articles()
        # print(articles[0]['title'])
        return render_template("stocks.html", stocks=topics, stocksize=len(topics))

    else:
        return render_template("log_in.html")


# db 목록 읽어오는 기능
@app.route('/notes', methods=["GET", "POST"])
def notes():
    if session.get('is_logged') is not None:
        #print(session.get('is_logged'))
        cursor = db.cursor()
        sql = 'SELECT * FROM topic'
        cursor.execute(sql)
        topics = cursor.fetchall()
        # articles = Articles()
        # print(articles[0]['title'])
        if session.get('is_logged') == "g":
            return render_template("notes_for_guest.html", notes=topics, notesize=len(topics))
        else :
            return render_template("notes.html", notes=topics, notesize=len(topics))

    else:
        return render_template("log_in.html")


# notes 선택한 걸 자세히 표시하는 기능
@app.route('/note/<int:id>')  # <id> 를 params 라고 해서 메소드에서 써먹을 수 있다.
def note(id):
    cursor = db.cursor()
    # articles = Articles()
    # article = articles[id - 1]
    sql = 'SELECT * FROM topic WHERE id = {};'.format(id)
    cursor.execute(sql)
    topic = cursor.fetchone()
    return render_template("note.html", article=topic)


# 새로운 note 추가하는 기능
@app.route('/add_notes', methods=["GET", "POST"])
def add_notes():
    cursor = db.cursor()
    if request.method == "POST":
        desc = request.form['Desc']
        title = request.form['Title']
        author = session.get('is_logged')
        sql_insert = "INSERT INTO `flasktest`.`topic` (`title`, `body`, `author`) VALUES (%s, %s, %s);"
        val = [title, desc, author]
        cursor.execute(sql_insert, val)
        db.commit()
        # db.close()
        return redirect("/notes")
    else:
        return render_template("add_notes.html", user=session.get('is_logged'))


# article을 제거하는 기능
@app.route('/delete/<int:id>', methods=["POST"])
def delete(id):
    cursor = db.cursor()
    sql_insert = "DELETE FROM topic WHERE id = {};".format(id)
    cursor.execute(sql_insert)
    db.commit()
    topic = cursor.fetchall()
    # db.close()
    return redirect("/notes")


# article을 수정하는 기능
@app.route('/change_notes/<int:id>', methods=["GET", "POST"])
def change_articles(id):
    cursor = db.cursor()
    if request.method == "POST":
        desc = request.form['Desc']
        title = request.form['Title']
        author = request.form['Author']
        sql_change = "UPDATE topic SET title = %s, body = %s, author = %s, create_date = NOW() WHERE (id = %s);"
        val = [title, desc, author, id]
        cursor.execute(sql_change, val)
        db.commit()
        topic = cursor.fetchall()
        return redirect("/notes")
    else:
        cursor = db.cursor()
    sql = 'SELECT * FROM topic WHERE id = {};'.format(id)
    cursor.execute(sql)
    topic = cursor.fetchone()
    return render_template("change_notes.html", article=topic)


# 주식화면 - 아직 만드는 중
@app.route('/stocks')
def about():
    if session.get('is_logged') is not None:
        return render_template("stocks.html")
    else:
        return render_template("log_in.html")


@app.route('/fig/<float:mean>_<float:var>_<int:size>_<string:color>')
def fig(mean, var, size, color):
    if session.get('is_logged') is not None:
        plt.figure(figsize=(10, 10))
        xs = np.random.normal(mean, 5, size)
        ys = np.random.normal(mean, 5, size)
        plt.scatter(xs, ys, s=var, marker='o', color=color, alpha=0.4)
        img = BytesIO()
        plt.savefig(img, format='png', dpi=200)
        img.seek(0)
        # print(xs)
        return send_file(img, mimetype='image/png')
    else:
        return render_template("log_in.html")


@app.route('/graphes/', methods=["GET", "POST"])
def graphes():
    if session.get('is_logged') is not None:
        if request.method == "GET":
            m, v = 3, 50
            return render_template("graphes.html", mean=m, var=v, size=0, color='#000000', width=500, height=500)
        else:
            color = request.form['color']
            m = 3
            var = request.form['var']
            size = request.form['number']
            return render_template("graphes.html", mean=m, var=var, size=size, color=color, width=500, height=500)
    else:
        return render_template("log_in.html")


if __name__ == '__main__':
    app.run(host='0.0.0.0')
