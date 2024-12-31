#Felipe Dabbah, dabbah@usc.edu
# ITP 216, Fall 2024 
# Section 20243
#Final Project
#Description: This program is a web application that allows users to search for the closing price of Google stock and the volume of stocks traded.

import datetime
import io
import os
import sqlite3 as sl

import pandas as pd
from flask import Flask, redirect, render_template, request, session, url_for, send_file
from matplotlib.figure import Figure
from sklearn.linear_model import LinearRegression

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
db = "google_stock.db"


@app.route("/")
def home():
    options = {
        "close": "Closing price of the stock",
        "volume": "Volume of stocks traded",
    }
    return render_template("home.html", choices=db_get_choices(), message="Please enter a stock metric to search for.",
                           options=options)


@app.route("/submit_option", methods=["POST"])
def submit_choice():

    session["choice"] = request.form["choice"]
    if 'choice' not in session or session["choice"] == "":
        print("choice not in session")
        return redirect(url_for("home"))
    if "data_request" not in request.form:
        print("data_request not in request.form")
        return redirect(url_for("home"))
    
    session["data_request"] = request.form["data_request"]
    return redirect(url_for("choice_current", data_request=session["data_request"], choice=session["choice"]))


@app.route("/api/google/<data_request>/<choice>")
def choice_current(data_request, choice):
    return render_template("choice.html", data_request=data_request, choice=choice, project=False)


@app.route("/submit_projection", methods=["POST"])
def submit_projection():
    if 'choice' not in session:
        return redirect(url_for("home"))
    session["date"] = request.form["date"]
    # THESE NEED TO BE BACK IN!
    if session["choice"] == "" or session["data_request"] == "" or session["date"] == "":
        return redirect(url_for("home"))
    return redirect(url_for("choice_projection", data_request=session["data_request"], choice=session["choice"]))


@app.route("/api/google/<data_request>/projection/<choice>")
def choice_projection(data_request, choice):
    return render_template("choice.html", data_request=data_request, choice=choice, project=True, date=session["date"])


@app.route("/fig/<data_request>/<choice>")
def fig(data_request, choice):
    fig = create_figure(data_request, choice)

    # img = io.BytesIO()
    # fig.savefig(img, format='png')
    # img.seek(0)
    # w = FileWrapper(img)
    # # w = werkzeug.wsgi.wrap_file(img)
    # return Response(w, mimetype="text/plain", direct_passthrough=True)

    img = io.BytesIO()
    fig.savefig(img, format='png')
    img.seek(0)
    return send_file(img, mimetype="image/png")


def create_figure(data_request, choice):
    df = db_create_dataframe(data_request, choice)
    if 'date' not in session:
        # df["date"] = pd.to_datetime(df["date"])
        # df = df.set_index("date")
        # df = df.resample("M").mean().reset_index()
        fig = Figure()
        ax = fig.add_subplot(1, 1, 1)
        if data_request == 'volume':
            fig.suptitle("Volume of Google Stock Traded")
            ax.set(ylabel="Volume of stock traded")

        else:
            fig.suptitle("Closing price of Google Stock")
            ax.set(ylabel="Price of stock ($)")

        ax.plot(df["date"], df["price"])

        ax.set(xlabel="Date")  # , xticks=range(0, len(df), 31))
        return fig
    
    else:
        # With the submitted date, make the prediction to that current data using linear regression and set new figure 
        df['datemod'] = df['date'].map(datetime.datetime.toordinal)
        y = df['price'][-30:].values

        X = df['datemod'][-30:].values.reshape(-1,1)
        
        dt = [[datetime.datetime.strptime(session['date'], '%Y/%m/%d')]]
        # print('dt:', dt)

        draw = datetime.datetime.toordinal(dt[0][0])
        dord = datetime.datetime.fromordinal(int(draw))
        regr = LinearRegression(fit_intercept=True, copy_X=True, n_jobs=2)
        regr.fit(X, y)
        pred = int(regr.predict([[draw]])[0])
        new_row = pd.DataFrame({'date': [dord], 'price': [pred], 'datemod': [draw]})
        df = pd.concat([df, new_row], ignore_index=True)
        
        fig = Figure()
        ax = fig.add_subplot(1,1, 1)
        ax.plot(df["date"], df["price"])
        if data_request == 'volume':
            fig.suptitle('By ' + session['date'] + ', the volume traded daily will be ' + str(pred) + '.')
            ax.set(ylabel="Volume of stock traded")
        else:
            fig.suptitle('By ' + session['date'] + ', the price will be $' + str(pred) + '.')
            ax.set(ylabel="Price of stock ($)")

        ax.set(xlabel="date")

        return fig


def db_create_dataframe(data_request, choice):
    conn = sl.connect(db)
    curs = conn.cursor()

    df = pd.DataFrame()
    table = "google_stock"
    # print(f'{table=}')
    #
    # print(f'{locale=}')

    index = 4

    if data_request == "volume":
        index = 6

    stmt = "SELECT Date FROM " + table
    curs.execute(stmt)
    dates = curs.fetchall()

    stmt = "SELECT * FROM " + table + " `" + choice + "`"
    curs.execute(stmt)
    data = curs.fetchall()
    item = [float(row[index]) for row in data]
    print("item 1" + str(item[0]) + " type: " + str(type(item[0])))


    df["date"] = [row[0] for row in dates]
    df["date"] = pd.to_datetime(df["date"])

    df["price"] = item
    print(df)

    conn.close()
    return df


def db_get_choices():
    # conn = sl.connect(db)
    # curs = conn.cursor()
    #
    # table = "google_stock"
    # stmt = "SELECT  from " + table
    # data = curs.execute(stmt)
    # # sort a set comprehension for unique values
    # locales = sorted({result[0] for result in data})
    # conn.close()

    choices = ["Google"]

    return choices


# m = "SELECT * FROM time_series_confirmed WHERE `Country/Region`='France'"
# result = conn.execute(m)

@app.route('/<path:path>')
def catch_all(path):
    return redirect(url_for("home"))


if __name__ == "__main__":
    # print(db_get_locales())
    app.secret_key = os.urandom(12)
    app.run(debug=True)