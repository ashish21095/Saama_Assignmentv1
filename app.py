#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import logging
import tweepy
from flask import Flask, session, redirect, render_template, request, url_for,jsonify
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, current_user, LoginManager, login_required, login_user, logout_user 
from sqlalchemy.inspection import inspect
import json
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import desc 
import sys

load_dotenv()

# Consumer Key
CONSUMER_KEY = os.getenv('API_KEY')
# Consumer Secret
CONSUMER_SECRET = os.getenv('API_SECRET')



logging.basicConfig(filename='error.log',level=logging.DEBUG)
logging.warning('app start!')


app = Flask(__name__)
app.debug = True

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')



login_manager = LoginManager(app)

db = SQLAlchemy(app)


class load_data:
    def twitter_auth(self):
        try:
            consumer_key = os.getenv('API_KEY')
            consumer_secret = os.getenv('API_SECRET')
            access_token = os.getenv('ACCESS_TOKEN')
            access_secret = os.getenv('ACCESS_SECRET')
        except KeyError:
            sys.stderr.write("Twitter environment variable not set")
            sys.exit(1)
        auth = tweepy.OAuthHandler(consumer_key,consumer_secret)
        auth.set_access_token(access_token,access_secret)
        return auth

    def get_twitter_client(self):
        auth = self.twitter_auth()
        client = tweepy.API(auth, wait_on_rate_limit=True)
        return client

    ## function that loads data into sqlite database 
    def load_twitter_dat(self):
        client = self.get_twitter_client()
        user_name = client.me().screen_name
        for status in tweepy.Cursor(client.user_timeline).items():
            user = User(id = status.id,tweet=status.text,created_date=status.created_at)
            db.session.add(user)
        db.session.commit()
        return user_name


class Serializer(object):

    def serialize(self):
        return {c: getattr(self, c) for c in inspect(self).attrs.keys()}

    @staticmethod
    def serialize_list(l):
        return [m.serialize() for m in l]


class Username(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True)


@login_manager.user_loader
def load_user(user_id):
    return Username.query.get(int(user_id))

class User(db.Model, Serializer):
    id = db.Column(db.Integer, primary_key=True)
    tweet = db.Column(db.Text)
    created_date = db.Column(db.DateTime)

    def to_dict(self):
        return {
            'id': self.id,
            'tweet': self.tweet,
            'created_date': self.created_date
        }

db.drop_all()
db.create_all()
app.logger.info('All db tables created')

@app.route('/')
def index():
    return redirect(url_for('twitter_auth'))




@app.route('/twitter_auth', methods=['GET'])
def twitter_auth():
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)

    try:
        redirect_url = auth.get_authorization_url()
        session['request_token'] = auth.request_token
    except tweepy.TweepError:
        return f"{CONSUMER_KEY} and {CONSUMER_SECRET}"
    app.logger.info(redirect_url)
    return redirect(redirect_url)

@app.route('/app')
def twitter():
    oauth_tok = request.args.get('oauth_token')
    oauth_ver = request.args.get('oauth_verifier')
    if oauth_tok and oauth_ver:
        app.logger.info("oauth_tok=%s oauth_ver=%s" % (oauth_tok, oauth_ver))
        get_data = load_data()
        app.logger.info('Tweets loaded in the database')
        user_name=get_data.load_twitter_dat()
        app.logger.info(f'The User:{user_name} is Authorized')
        query = Username.query.filter_by(username=user_name)
        try:
            user = query.one()
        except NoResultFound:
            user = Username(username=user_name)
            db.session.add(user)
            db.session.commit()
        login_user(user)
        return redirect(url_for('data'))

    else:
        app.logger.info('The User is not Authorized')
        return redirect(url_for('twitter_auth'))


@app.route('/data')
@login_required
def data():
    app.logger.info('All user timeline tweets fetched')
    return {'data': [user.to_dict() for user in User.query]}


@app.route('/search', methods=['GET'])
@login_required
def search():   
    tweet = request.args.get('search')
    query = User.query.filter_by(tweet=tweet).first_or_404()
    return jsonify({"id":query.id,"tweet":query.tweet,"created_date":query.created_date})


@app.route('/sort', methods=['GET'])
@login_required
def sort():
    try:
        column_name=request.args.get('column_name')
        sort_order=request.args.get('sort')
        if sort_order == 'desc':
            app.logger.info('User data sorted in descending order')
            result = User.query.order_by(User.__getattribute__(User,column_name).desc()).all()
            return json.dumps(User.serialize_list(result),default=str)
        if sort_order =='asc':
            app.logger.info('User data sorted in ascending order')
            result = User.query.order_by(User.__getattribute__(User,column_name)).all()
            return json.dumps(User.serialize_list(result),default=str)
    except:
        app.logger.info('Wrong arguments passed')
        return "Record not found", 400
       


if __name__ == '__main__':
    app.run(host="0.0.0.0",port=4455)
