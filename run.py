from flask import Flask, render_template, session, request, redirect, jsonify 
import tweepy, requests, json, datetime
import pandas as pd
from pandas_datareader import data as pdr
import yfinance as yf
from yfinance import shared

import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_
from pytz import timezone

db = SQLAlchemy()
app = Flask(__name__)
app.config["SECRET_KEY"] = '1234567'
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///tweets.db'

db.init_app(app)
app.run(debug=True)

class Positive(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    stock = db.Column(db.String(15), nullable=False)
    twitterUser = db.Column(db.String(50), nullable=False)
    twitterURL = db.Column(db.String(150), nullable=False)
    openPrice = db.Column(db.String(10), nullable=False)
    closePrice = db.Column(db.String(10), nullable=False)
    margin = db.Column(db.String(10), nullable=False)
    percentage = db.Column(db.String(10), nullable=False)
    validated = db.Column(db.String(10), nullable=False, default='False')

class Negative(db.Model):
	id = db.Column(db.Integer, primary_key=True, nullable=False)
	stock = db.Column(db.String(15), nullable=False)
	twitterUser = db.Column(db.String(50), nullable=False)
	twitterURL = db.Column(db.String(150), nullable=False)
	openPrice = db.Column(db.String(10), nullable=False)
	closePrice = db.Column(db.String(10), nullable=False)
	margin = db.Column(db.String(10), nullable=False)
	percentage = db.Column(db.String(10), nullable=False)
	validated = db.Column(db.String(10), nullable=False, default='False')

@app.route('/',  methods=['GET', 'POST'])
def index():
	positiveTable = Positive.query.order_by(Positive.percentage.desc())
	negativeTable = Negative.query.order_by(Negative.percentage.desc())
	searchTweet = request.args.get('twt', '')
	searchStock = request.args.get('stc', '')

	return render_template('home.html', posTable=positiveTable, negTable=negativeTable, searchTweet=searchTweet, searchStock=searchStock)

@app.route('/process', methods=['POST'])
def process():

	if request.form.get('tweet'):
		#Setting up the Tweepy
		tweet = request.form['tweet']
		stock = request.form['stock']

		if tweet:
			auth = tweepy.OAuthHandler('123', '123')
			auth.set_access_token('123-123', '123')
			api = tweepy.API(auth)

			url = 'https://publish.twitter.com/oembed?url=' + tweet
			r = requests.get(url = url) 
			data = r.json()
			html = data['html'] 

			split_string = tweet.split('/status/', 1)
			public_tweets = api.get_status(split_string[1])

			date = public_tweets.created_at
			start_date = datetime.datetime.strptime(str(date), "%Y-%m-%d %H:%M:%S")
			end_date = start_date + datetime.timedelta(days=7)

			account = public_tweets.author._json['name']

		if stock:
			symbol = stock
			interval = "1d"
			start = start_date.date()
			end = end_date.date() 
			weekno = start.weekday()

			#pull the quote
			quote = yf.Ticker(symbol)	
			#use the quote to pull the historical data from Yahoo finance
			hist = quote.history(interval=interval, start=start, end=end)
			if not hist.empty:
				#convert the historical data to JSON
				stockData = hist.to_json()
				stockInfo = quote.info
				#return the JSON in the HTTP response 

				df = hist
				dates =[]
				for x in range(len(df)):
					newdate = str(df.index[x])
					newdate = newdate[0:10]
					dates.append(newdate)

				df['dates'] = dates
				if weekno < 5:
					dayDay = df.loc[df['dates'] == df.dates[1]]
				else:
					dayDay = df.loc[df['dates'] == df.dates[0]]
				dOpen = dayDay.Open.to_string(index=False, header=False)
				dHigh = dayDay.High.to_string(index=False, header=False)
				dLow = dayDay.Low.to_string(index=False, header=False)
				dClose = dayDay.Close.to_string(index=False, header=False)
				dImpact= float(dClose) - float(dOpen)
			
			#Negative impact
			if float(dClose) < float(dOpen):
				print("Thats Rough buddy")
				p = float(dClose) / float(dOpen) * 100
				d = round(100 - p, 2)
				f = 'loss of ' + str(d) + '%'
				print(f)
				outcome = "text-danger"

				dataCheck = Negative.query.filter_by(stock=stock, twitterURL=tweet)
				results = len(dataCheck.all())
				if results == 0:
					new_data = Negative(stock=stock, twitterUser=account, twitterURL=tweet,
									openPrice=dOpen, closePrice=dClose, margin=dImpact, percentage=d)
					db.session.add(new_data)
					db.session.commit()

			#Positive impact
			else:
				print('You made a buck')
				p = round(float(dClose) / float(dOpen) * 100 - 100, 2)
				f = 'growth of ' + str(p) + '%'
				print(f)
				outcome = "text-success"

				dataCheck = Positive.query.filter_by(stock=stock, twitterURL=tweet)
				results = len(dataCheck.all())
				if results == 0:
					new_data = Positive(stock=stock, twitterUser=account, twitterURL=tweet,
									openPrice=dOpen, closePrice=dClose, margin=dImpact, percentage=p)
					db.session.add(new_data)
					db.session.commit()

		return jsonify({'outcome': outcome , 'dPercent': f,'dImpact': dImpact, 'dOpen' : dOpen, 'dHigh' : dHigh, 'dLow' : dLow, 'dClose' : dClose, 'stockData' : stockData, 'stockInfo' : stockInfo, 'tweetDate': start, 'account' : account, 'date' : start, 'html': html})

	return jsonify({'error' : 'Some data is missing or incorrect, please try again!'})
