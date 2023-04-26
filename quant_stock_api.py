from flask import Flask, request, send_file
import redis
import json
import os
import matplotlib.pyplot as plt
import pandas
from datetime import datetime
import io
import yfinance as yf
import pickle

app = Flask(__name__)


## Creating Redis clienst
def get_redis_client():
    redis_ip = os.environ.get('REDIS-IP')
    if not redis_ip:
        raise Exception()
    return redis.Redis(host=redis_ip, port=6379, db=0)

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



# ROUTES

@app.route('/tickers/<ticker>', methods = ['POST'])
def post_tickers(ticker: str) -> str:
    '''
    Gets or Deletes the desired tickers stored in the redis db

    Args: None

    Returns: String stating success or failure
    '''
    ticker = str(ticker)

    method = request.method
    if method == 'POST':
        if(len(rd_tickers.keys())==0):
            tickers = []
        else:
            tickers = json.loads(rd_tickers.get("Tickers"))
        tickers.append(str(ticker))
        rd_tickers.set("Tickers", json.dumps(tickers))

        return "Ticker posted\n"


    else:
        return 'the method you tried is not supported\n'






@app.route('/tickers', methods = ['GET', 'DELETE'])
def handle_tickers():
    '''
    Gets or Deletes the desired tickers stored in the redis db

    Args: None

    Returns: Something corresponding to which method was used
        "DELETE" method: deletes all tickers in redis db
        "GET" method: returns list of all tickers listed in redis db
    '''
    method = request.method

    if method == 'GET':
        try:
            return json.loads(rd_tickers.get("Tickers"))
        except TypeError:
            return "Please add a Ticker before attempting to return the list of tickers\n"
    elif method == 'DELETE':
        rd_tickers.flushdb()
        return f'Tickers deleted, there are {len(rd_tickers.keys())} keys in the db\n'
    
    else:
        return "Method not supported\n"







@app.route('/data', methods = ['GET', 'POST', 'DELETE'])
def handle_data() -> list:
    '''
    Manipulates data wiht 3 different methods with GET, POST, and DELETE method

    Args: None

    Returns: String corresponding to which method was used
        "DELETE" method: deletes all data in redis db
        "POST" method: posts data into redis db
        "GET" method: returns ALL data from redis db
    '''

    method = request.method
    global rd

    if method == 'POST':
        ### DO TRY EXCEPT OR IF STATEMENT TO MAKE SURE THERE ARE TICKERS IN DB
        try:
            tickerList = json.loads(rd_tickers.get("Tickers"))
            for ticker in tickerList:

                df = yf.download(str(ticker))
                if(len(df) != 0):
                    data_bytes = pickle.dumps(df)
                    rd.set(str(ticker), data_bytes)
        except TypeError:
            return "Please post tickers to the ticker db first\n"

        return "Ticker data posted \n", 200    

    elif method == 'DELETE':
        rd.flushdb()
        return f'data deleted, there are {len(rd.keys())} keys in the db\n'

    elif method == 'GET':
        
        dataframes = []

        # USE THIS LINE TO GET KEYS FROM THE DB
        keys = [key.decode('utf-8') for key in rd.keys()]

        for ticker in keys:
            df = pickle.loads(rd.get(ticker))
            relevantData = {"Start": df.index[0], "End": df.index[0], "First Price": df["Open"][0], "Last Price": df["Close"][-1], "TICKER NAME": ticker}
            
            dataframes.append(relevantData)
        
        return dataframes
    else:
        return 'the method you tried is not supported\n'

    return f'Error\n'





@app.route('/data/<ticker>', methods = ['GET'])
def get_dataFrame(ticker: str):
    """
    Returns json data for a specific ticker in the data set

    Args:
        ticker (str): ticker 

    Returns:
        json_data: json data of ticker of interest
    """

    if not str(ticker).isalpha():
        return "Invalid Ticker\n"

    if len(rd.keys()) == 0:
        return "Database is empty. Please post data and make sure tickers database is populated. \n", 400
    else:

        try:
            df = pandas.read_json(rd.get(str(ticker)))
        except Exception as e:
            return f"Ticker Does not exist, error as {e}\n"

        json_data = df.to_json()
        return json_data, 200
    return "\n"

    



@app.route('/image/<tickername>', methods = ['GET', 'POST', 'DELETE'])
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

    method = request.method

    if method == 'GET':
        if(len(rd_image.keys()) == 0):
            return "No images in the Database\n"
        else:
            try:
                image = rd_image.get(tickername) # Need a way to index each image ??
            except Exception:
                return f"Plot for {tickername} not in database, please post first\n"
            buf = io.BytesIO(image)
            buf.seek(0)

            existing_images = rd_image.keys() == 0

            file_name = f'image{existing_images}.png'
            return send_file(buf, mimetype = 'image/png') #, as_attachment=True, download_name=file_name)   <--- Could potentially add, works without

    elif method =='DELETE':
        rd_image.flushdb()
        return f'Plot deleted, there are {len(rd_image.keys())} images in the db\n'

    elif method == 'POST':
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

            # Getting data
            end = datetime.now()
            start = datetime(start_year, end.month, end.day)
            try:
                dataset = pickle.loads(rd.get(tickername))
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

            rd_image.set(str(tickername), buf.getvalue())

        return "Image is posted\n", 200





if __name__ == '__main__':
    # can put debug config here
    app.run(debug=True, host='0.0.0.0')
