from flask import Flask, request, send_file
import redis
import requests
import json
import os
import matplotlib.pyplot as plt
from datetime import datetime
import io
import yfinance as yf

app = Flask(__name__)

def get_redis_client():
    redis_ip = os.environ.get('REDIS-IP')
    if not redis_ip:
        raise Exception()
    return redis.Redis(host=redis_ip, port=6379, db=0, decode_responses=True)

def get_redis_image_db():
    redis_ip = os.environ.get('REDIS-IP')
    if not redis_ip:
        raise Exception()
    return redis.Redis(host=redis_ip, port=6379, db=1)

def get_ticker_db():
    redis_ip = os.environ.get('REDIS-IP')
    if not redis_ip:
        raise Exception()
    return redis.Redis(host=redis_ip, port=6379, db=2, decode_responses=True)

rd = get_redis_client()

rd_image = get_redis_image_db()

rd_tickers = get_ticker_db()

@app.route('/tickers/<ticker>', methods = ['POST'])
def post_tickers(ticker: str) -> str:
    '''
    Gets or Deletes the desired tickers stored in the redis db

    Args: None

    Returns: String stating success or failure
    '''
    if(len(rd_tickers.keys())==0):
        tickers = []
    else:
        tickers = rd_tickers.get("Tickers")
    tickers.append(yf.download(ticker))
    rd_tickers.set("Tickers", tickers)

    return "Tickers posted"
        


@app.route('/tickers', methods = ['GET', 'DELETE'])
def handle_tickers():
    '''
    Gets or Deletes the desired tickers stored in the redis db

    Args: None

    Returns: Something corresponding to which method was used
        "DELETE" method: deletes all tickers in redis db
        "GET" method: returns list of all tickers listed in redis db
    '''


@app.route('/data', methods = ['GET', 'POST', 'DELETE'])
def handle_data() -> list:
    '''
    Manipulates data wiht 3 different methods with GET, POST, and DELETE method

    Args: None

    Returns: String corresponding to which method was used
        "DELETE" method: deletes all data in redis db
        "POST" method: posts data into redis db
        "GET" method: returns data from redis db
    '''

    method = request.method
    global rd

    if method == 'POST':
         return "Data posted"
    
    elif method == 'GET':
        return "Here is your data"
        

    elif method == 'DELETE':
        rd.flushdb()
        return f'data deleted, there are {len(rd.keys())} keys in the db\n'

    else:
        return 'the method you tried is not supported\n'

    return f'method completed \n'




@app.route('/image/<tickername>', methods = ['POST'])
def make_image(tickername):
    '''
    Takes in a stock ticker and (optionally) a time frame.
    Returns an plot of the stock price throughout the time frame
    If a time frame is not specified, the current time and 5 years prior are used. 

    *Sets the plot in a redis database*
        To retrieve image use "base_url/image -X GET >> file_name.png"

    Args:
        tickername: the stock-of-interest's ticker symbol ex) 'AAPL'

    Returns:
        Success method and a image in a redis data base


    '''



    try:
        start_year = int(request.args.get('start_year', int(datetime.now().year) - 5)) #2000 is default year
    except ValueError:
        return "Error: query parameter 'start_year' must be an integer\n", 400

    try:
        end_year = int(request.args.get('end_year', int(datetime.now().year))) #2000 is default year
    except ValueError:
        return "Error: query parameter 'end_year' must be an integer\n", 400

    if tickername.isalpha() == False:
        return f"Error: the ticker must be alphabetical.\n Ex) '/image/AAPL' \n NOT '/image/{tickername}'\n"   

    elif start_year > end_year:
        return "Error: Start year greater than end year\n", 400

    else:

        rd_image.flushdb() ## NEED TO REMOVE (CLEARS DATA BASE BF POSTING AN IMAGE)

        # Getting data
        end = datetime.now()
        start = datetime(start_year, end.month, end.day)
        try:
            dataset = yf.download(tickername, start, end)
        except Exception:
            return f"{tickername} is not a valid/supported stock ticker"
            
        # Selecting data
        data_to_plot = dataset.loc[f"{start_year}":f"{end_year}", "Close"]   
        curr_plot = data_to_plot.plot(figsize=(12,4), legend = True)            
        plt.legend([f"{tickername}"])
        plt.title(f"{tickername} Stock Price History")
        plt.ylabel("$ USD")
            
        buf = io.BytesIO()
        plt.savefig(buf, format = 'png')
        buf.seek(0)

        rd_image.set('image', buf.getvalue())

    return "Image is posted\n", 200



@app.route('/image', methods = ['GET', 'DELETE'])
def image_manip():
    '''
    '''

    method = request.method

    if method == 'GET':
        if(len(rd_image.keys()) == 0):
            return "No images in the Database\n"
        else:
            image = rd_image.get('image') # Need a way to index each image ??
            buf = io.BytesIO(image)
            buf.seek(0)

            existing_images = rd_image.keys() == 0

            file_name = f'image{existing_images}.png'
            return send_file(buf, mimetype = 'image/png') #, as_attachment=True, download_name=file_name)   <--- Could potentially add, works without

    elif method =='DELETE':
        rd_image.flushdb()
        return f'Plot deleted, there are {len(rd_image.keys())} images in the db\n'






if __name__ == '__main__':
    # can put debug config here
    app.run(debug=True, host='0.0.0.0')
