import os
from flask import Flask,request,jsonify, json, Response, make_response, render_template
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_cors import CORS
import tweepy
import re
from textblob import TextBlob
import matplotlib
matplotlib.use('agg')


#import jwt

app = Flask(__name__)
bcrypt = Bcrypt(app)
CORS(app)
mongodb_client = PyMongo(app,uri=os.environ.get("MONGO_URI"))
db = mongodb_client.db
consumerKey = os.environ.get("api_key")
consumerSecret = os.environ.get("api_key_secret")
accessToken = os.environ.get("access_token")
accessTokenSecret = os.environ.get("access_token_secret")
auth = tweepy.OAuthHandler(consumerKey, consumerSecret)
auth.set_access_token(accessToken, accessTokenSecret)
api = tweepy.API(auth, wait_on_rate_limit=True)

class SentimentAnalysis:
        

    def __init__(self):
        self.tweets = []
        self.tweetText = []

    def fetch_tweets(self,keyword,tweets):
        tweets = int(tweets)
        res_tweets = tweepy.Cursor(api.search_tweets, q=keyword, lang="en",tweet_mode='extended').items(tweets)
        final_list = []
        for tweet in res_tweets:
            final_list.append(tweet.full_text)
        return final_list

    def DownloadData(self, keyword, tweets):
 
        tweets = int(tweets)
        self.tweets = tweepy.Cursor(api.search_tweets, q=keyword, lang="en").items(tweets)
        polarity = 0
        positive = 0
        wpositive = 0
        spositive = 0
        negative = 0
        wnegative = 0
        snegative = 0
        neutral = 0

        for tweet in self.tweets:

            self.tweetText.append(self.cleanTweet(tweet.text).encode('utf-8'))

            analysis = TextBlob(tweet.text)

            polarity += analysis.sentiment.polarity

            if (analysis.sentiment.polarity == 0):
                neutral += 1
            elif (analysis.sentiment.polarity > 0 and analysis.sentiment.polarity <= 0.3):
                wpositive += 1
            elif (analysis.sentiment.polarity > 0.3 and analysis.sentiment.polarity <= 0.6):
                positive += 1
            elif (analysis.sentiment.polarity > 0.6 and analysis.sentiment.polarity <= 1):
                spositive += 1
            elif (analysis.sentiment.polarity > -0.3 and analysis.sentiment.polarity <= 0):
                wnegative += 1
            elif (analysis.sentiment.polarity > -0.6 and analysis.sentiment.polarity <= -0.3):
                negative += 1
            elif (analysis.sentiment.polarity > -1 and analysis.sentiment.polarity <= -0.6):
                snegative += 1

        positive = self.percentage(positive, tweets)
        wpositive = self.percentage(wpositive, tweets)
        spositive = self.percentage(spositive, tweets)
        negative = self.percentage(negative, tweets)
        wnegative = self.percentage(wnegative, tweets)
        snegative = self.percentage(snegative, tweets)
        neutral = self.percentage(neutral, tweets)

        polarity = polarity / tweets
    
        final_positive = float(positive)+float(wpositive)+float(spositive)
        final_negative = float(negative)+float(wnegative)+float(snegative)
        neutral = float(neutral)
        
        result = final_positive if final_positive > final_negative else final_negative
        final_result = result if result > neutral else neutral

        if final_result == final_positive:
            htmlpolarity = "Positive"
        elif final_result == final_negative:
            htmlpolarity = "Negative"
        else:
            htmlpolarity = "Neutral"
        
        return htmlpolarity,final_negative,final_positive,neutral,polarity

    def cleanTweet(self, tweet):
        return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t]) | (\w +:\ / \ / \S +)", " ", tweet).split())

    def percentage(self, part, whole):
        temp = 100 * float(part) / float(whole)
        return format(temp, '.2f')

@app.route("/", methods=['GET'])
def hello_world():
    return "Working"

@app.route("/login", methods=['POST'])
def login_user():
    try:
        if request.method == 'POST':
            form_data = request.get_json()
            email = form_data['email']
            password = form_data['password']
            if(email != '' and password != ''):
                data = list(db.users.find({'email': email}))
                if(len(data) == 0):
                    return Response(status=404, response=json.dumps({'message': 'user does not exist'}), mimetype='application/json')
                else:
                    data = data[0]
                    if(bcrypt.check_password_hash(data['password'], password)):
                        #token =jwt.encode({'email': email}, app.config['SECRET_KEY'])
                        return make_response(jsonify({'message':'User logged in successfully'}), 201)
                    else:
                        return Response(status=402, response=json.dumps({'message': 'Invalid password'}), mimetype='application/json')
            else:
                return Response(status=400, response=json.dumps({'message': 'Bad request'}), mimetype='application/json')
        else:
            return Response(status=401, response=json.dumps({'message': 'invalid request type'}), mimetype='application/json')
    except Exception as Ex:
        print('\n\n\n*********************************')
        print(Ex)
        print('*********************************\n\n\n')
        return Response(response=json.dumps({'message': "Internal Server error"}), status=500, mimetype="application/json")


@app.route("/register", methods=['POST'])
def register_user():
    try:
        if request.method == "POST":
            user_details = request.get_json()
            full_name = user_details["fullName"]
            email = user_details["email"]
            password = user_details["password"]
            password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
            if (full_name != '' and email != '' and password_hash != ''):
                db.users.insert_one({'fullName':full_name,'email':email,'password':password_hash})
                return Response(response=json.dumps({'message': 'User created successfully'}), status=200, mimetype="application/json")
            else:
                return Response(status=400, response=json.dumps({'message': 'Please enter your details'}), mimetype='application/json')
        else:
            return Response(status=400, response=json.dumps({'message': 'Bad request'}), mimetype='application/json')
    except Exception as Ex:
        print('\n\n\n*********************************')
        print(Ex)
        print('*********************************\n\n\n')
        return Response(response=json.dumps({'message': "Internal Server Error"}), status=500, mimetype="application/json")        

@app.route("/getSentiment",methods=["POST"])
def sentiment_analyzer():
    tweet_info = request.get_json()
    keyword = tweet_info["keyword"]
    tweets = tweet_info["tweets"]
    sa = SentimentAnalysis()
    htmlpolarity,negative,positive,neutral,polarity = sa.DownloadData(keyword, tweets)
    analysis = {}
    analysis["final_sentiment"] = htmlpolarity
    analysis["positive"] = positive
    analysis["negative"] = negative
    analysis["neutral"] = neutral
    return jsonify(analysis)

@app.route("/getTweets",methods=["POST"])
def tweet_fetcher():
    tweet_info = request.get_json()
    keyword = tweet_info["keyword"]
    tweets = tweet_info["tweets"]
    sa = SentimentAnalysis()
    tweets = sa.fetch_tweets(keyword, tweets)
    tweets_response = {}
    tweets_response["tweets"] = list(tweets)
    return jsonify(tweets_response)

if __name__ == '__main__':
    app.run()

    