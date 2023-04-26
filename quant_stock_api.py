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
import jobs
import math

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

@app.route('/jobs/<jid>', methods = ['GET'])
def job_status(jid):
    return jobs.get_job_by_id(jid)


@app.route('/jobs/image', methods = ['POST'])
def job_api():
    """
    API route for creating a new job to do some analysis. This route accepts a JSON payload
    describing the job to be created.
    """
    try:
        job = request.get_json(force=True)
    except Exception as e:
        return json.dumps({'status': "Error", 'message': 'Invalid JSON: {}.'.format(e)})
    return json.dumps(jobs.add_job(job['ticker'])) + "\n"


@app.route('/tickers/<ticker>', methods = ['POST'])
def post_tickers(ticker: str) -> str:
    '''
    Gets or Deletes the desired tickers stored in the redis db

    Route: <baseURL>/tickers/<ticker>
    Methods: ['POST']

    Args: None

    Returns: String stating success or failure
    '''
    ticker = str(ticker)

    method = request.method
    if method == 'POST':
        if(len(rd_tickers.keys())==0):
            tickers = []
            tickers.append(str(ticker))
            rd_tickers.set("Tickers", json.dumps(tickers))
            return "Ticker posted\n"
        else:
            tickers = json.loads(rd_tickers.get("Tickers"))
            if(ticker not in tickers):
                tickers.append(str(ticker))
                rd_tickers.set("Tickers", json.dumps(tickers))
                return "Ticker posted\n"
            else:
                return "Ticker already in ticker list\n"
        

    else:
        return 'the method you tried is not supported\n'




@app.route('/tickers', methods = ['GET', 'DELETE'])
def handle_tickers():
    '''
    Gets or Deletes the desired tickers stored in the redis db

    Route: <baseURL>/tickers
    Methods: ['GET', 'DELETE']

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
    Manipulates data with 3 different methods with GET, POST, and DELETE method

    Route: <baseURL>/data
    Methods: ['GET', 'POST', 'DELETE']

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
            relevantData = {"Start": df.index[0], "End": df.index[-1], "First Price": df["Open"][0], "Last Price": df["Close"][-1], "TICKER NAME": ticker}
            
            dataframes.append(relevantData)
        
        return dataframes
    else:
        return 'the method you tried is not supported\n'

    return f'Error\n'





@app.route('/data/<ticker>', methods = ['GET'])
def get_dataFrame(ticker: str):
    """
    Returns json data for a specific ticker in the data set

    Route: <baseURL>/data/<ticker>
    Methods: ['GET']

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
            df = pickle.loads(rd.get(ticker))
        except Exception as e:
            return f"Ticker Does not exist, error as {e}\n"

        returnDf_rel = {"Start": df.index[0], "End": df.index[-1], "First Price": df["Open"][0], "Last Price": df["Close"][-1], "TICKER NAME": ticker}

        return returnDf_rel, 200
    return "\n"

    

###### NEED TO MAKE IMAGE ROUTE THAT CAN HANGLE 2+ TICKERS

@app.route('/image', methods = ['DELETE'])
def del_images():
    method = request.method
    if method == 'DELETE':
        rd_image.flushdb()
        return f'All plots deleted, there are {len(rd_image.keys())} images in the db\n'
    else:
        return "This method is not supporter by the route\n"


def post_image(tickername):
    
    start_year = int(datetime.now().year) - 5 #2000 is default year
    
    end_year = int(datetime.now().year) #2000 is default year
    
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
        plt.figure()
        curr_plot = data_to_plot.plot(figsize=(12,4), legend = True) 
                
        plt.legend([f"{tickername}"])
        plt.title(f"{tickername}Stock Price History from {start_year} to {end_year}")
        plt.ylabel("$ USD")
            
        buf = io.BytesIO()
        plt.savefig(buf, format = 'png')
        buf.seek(0)

        rd_image.set(str(tickername), buf.getvalue())
    return "Success\n"


@app.route('/image/<tickername>', methods = ['GET', 'POST', 'DELETE'])
def make_image(tickername):
    '''
    Takes in a stock ticker and (optionally) a time frame.
    Returns an plot of the stock price throughout the time frame
    If a time frame is not specified, the current time and 5 years prior are used. 

    *Sets the plot in a redis database*
        To retrieve image use "base_url/image -X GET >> file_name.png"

    Route: <baseURL>/image/<tickername>
    Methods: ['GET', 'POST', 'DELETE']

    Args:
        tickername: the stock-of-interest's ticker symbol ex) 'AAPL'
    
    Query Parameters: (for Post method Only)
        "start": The start year of the plot 
        "end": the end year of the plot 

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
        rd_image.delete(tickername)
        return f'Plot deleted, there are {len(rd_image.keys())} images in the db\n'

    elif method == 'POST':
        try:
            start_year = int(request.args.get('start', int(datetime.now().year) - 5)) #2000 is default year
        except ValueError:
            return "Error: query parameter 'start' must be an integer\n", 400

        try:
            end_year = int(request.args.get('end', int(datetime.now().year))) #2000 is default year
        except ValueError:
            return "Error: query parameter 'end' must be an integer\n", 400

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
            plt.figure()
            curr_plot = data_to_plot.plot(figsize=(12,4), legend = True) 
                    
            plt.legend([f"{tickername}"])
            plt.title(f"{tickername}Stock Price History from {start_year} to {end_year}")
            plt.ylabel("$ USD")
                
            buf = io.BytesIO()
            plt.savefig(buf, format = 'png')
            buf.seek(0)

            rd_image.set(str(tickername), buf.getvalue())

        return "Image is posted\n", 200


# to support multiple images, basically do samething as above but just repeat the "data_to_plot = " and "curr_plot" = lines. should work



@app.route('/correlation/<tickername1>/<tickername2>/<start>/<end>/<value_type>', methods = ['GET'])
def cal_correlation(tickername1:str,tickername2:str,start:str,end:str,value_type:str):
    '''
    Takes in two stocks, the start and end periods, and returns the correlation value using the open value

    Args:
        tickername1: First ticker name ex) 'AAPL'
        tickername2: Second ticker name ex) 'MSFT'
        start: start of correlation period 'year-month-date' ex) '2016-04-25'
        end: end of correlation period 'year-month-date' ex) '2017-04-25'

    Returns:
        correlation_coefficient: correlation coefficient

    '''

    method = request.method

    if method == 'GET':

        #check value type
        if value_type not in ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']:
            return "Value type is invalid"
        
        #check date format
        try:
            start_dt = datetime.strptime(start, '%Y-%m-%d')
            end_dt = datetime.strptime(end, '%Y-%m-%d')
        except ValueError:
            return "Invalid date format"
        
        #check start date is before the end date
        if datetime.strptime(start, '%Y-%m-%d') > datetime.strptime(end, '%Y-%m-%d'):
            return "Start date cannot be after end date"


        #check to see ticker is valid and has been posted
        try:
            dataset1 = pickle.loads(rd.get(tickername1))
            x = dataset1.loc[f"{start}":f"{end}", value_type]
            dataset2 = pickle.loads(rd.get(tickername2))
            y = dataset2.loc[f"{start}":f"{end}", value_type]

        except Exception:
            return f"{tickername1} or {tickername2} is not a stock ticker that has been posted. Make sure you post the desired tickers first. \n"
        
        #check if date is within valid range
        
        start_found1 = False
        end_found1 = False
        start_found2 = False
        end_found2 = False

        test_date_start = start + " 00:00:00"
        test_date_end = end + " 00:00:00"
        test_date_start_dt = datetime.strptime(test_date_start, "%Y-%m-%d %H:%M:%S")
        test_date_end_dt = datetime.strptime(test_date_end, "%Y-%m-%d %H:%M:%S")

        # Check if start and end dates exist in dataset1
        for i, date in enumerate(dataset1.index):
            if date == test_date_start_dt:
                start_found1 = True
            if date == test_date_end_dt:
                end_found1 = True
            if start_found1 and end_found1:
                break

        # Check if start and end dates exist in dataset2
        for i, date in enumerate(dataset2.index):
            if date == test_date_start_dt:
                start_found2 = True
            if date == test_date_end_dt:
                end_found2 = True
            if start_found2 and end_found2:
                break


        if not start_found1 or not end_found1 or not start_found2 or not end_found2:
            if not start_found1:
                return(f"{start} not found in {tickername1}")
            if not end_found1:
                return(f"{end} not found in {tickername1}")
            if not start_found2:
                return(f"{start} not found in {tickername2}")
            if not end_found2:
                return(f"{end} not found in {tickername2}")
        else:
            # Both start and end dates exist in both datasets
            # continue with the correlation calculation
            None
            

        # making sure dates align
        if len(x) == len(y):
            n = len(x)
            # x and y product summed up
            index = 0
            x_y_product_sum = 0
            for value_type in x:
                x_y_product_sum = x_y_product_sum + (x[index] * y[index])
                index = index + 1

            # x summed and y summed and multiplied
            x_sum = 0
            y_sum = 0
            for value_type in x:
                x_sum = x_sum + value_type
            for value_type in y:
                y_sum = y_sum + value_type

            x_sum_multiply_y_sum = x_sum * y_sum

            # Values squared and summed
            x2_sum = 0
            y2_sum = 0

            for value_type in x:
                x2_sum = value_type*value_type + x2_sum
            for value_type in y:
                y2_sum = value_type*value_type + y2_sum

            correlation_coefficient = (n*x_y_product_sum - x_sum_multiply_y_sum)/math.sqrt((n*x2_sum - x_sum*x_sum)*(n*y2_sum - y_sum*y_sum))
            
            return {"correlation coefficient": correlation_coefficient}
        
        else:
            return "Dates do not match"
    
    else:
        return "Method not supported\n"




@app.route('/help', methods = ['GET'])
def get_help() -> str:
    """
    Returns a message of all the available routes and methods and how to use them 
    
    Route: <baseURL>/help 
    Methods: [GET]

    Args:
        NONE
    Returns:
        help_message (string) : brief descriptions of all available routes and methods
    """

    list_of_functions = ['post_tickers', 'handle_tickers', 'handle_data', 'get_dataFrame', 'make_image', 'get_help']
    
    help_message = '\nHERE IS A HELP MESSAGE FOR EVERY FUNCTION/ROUTE IN "quant_stock_api.py"\n\n'

    for func in list_of_functions:
        help_message = help_message + f'{func}:\n' + eval(func).__doc__ + '\n\n'

    return help_message




if __name__ == '__main__':
    # can put debug config here
    app.run(debug=True, host='0.0.0.0')
