# Quant Stock Project

This project is an application that enables users to run various simulations on the stock market using Flask, Docker, Redis database, and Kubernetes clusters. The main objective of the project is to analyze past data and determine the optimal portfolio selection that minimizes risks while maximizing returns (maximizing sharpe ratio).


<h3>Data Used</h3>
To access the data required for the simulations, the application connects to an API called yfinance, which is linked to Yahoo! Finance page. The yfinance API provides the historical stock market data needed for the simulations. Here is a link for more information about yfinance https://pypi.org/project/yfinance/

<h2>Scripts</h2>

<h5>Docker Folder</h5>

`docker-compose.yml` - Composes the docker images into a functioning app with docker-compose up

`Dockerfile.api` - Dockerfile for the quant_stock_api

`Dockerfile.wrk` - Dockerfile for the worker


<h5>Kubernetes Folder</h5>

`quant-data-flask-deployment.yml` - Flask API deployment yml configuration

`quant-data-flask-ingress.yml` - Manages external access of the application

`quant-data-flask-nodeport-service.yml` - Exposes a port on each node in the cluster and connects it to one address

`quant-data-flask-service.yml` - Service for the flask deployment

`quant-data-redis-deployment.yml` - deployment of Redis database

`quant-data-pvc.yml` - Persistent Volume Claim so that Redis saves data even when the deployment goes down

`quant-data-redis-service.yml` - Service for the redis database


<h5>SRC Folder</h5>

`quant_stock_api.py` - API with all of the routes of the Flask App

`jobs.py` - Job functions that are called in worker and the Flask API

`worker.py` - Listens to the queue and runs analysis on the data in the background


| Route  | Method   | What it does     |
| ----------- | -------- | ----------- |
| `/tickers/<ticker>`      | POST |POST the desired tickers stored into the tickers redis db |
| `/tickers`      | GET |Gets the tickers stored in the tickers redis db |
| `/tickers`      | DELETE |Deletes the tickers stored in the tickers redis db|
| `/data`      | POST |Posts ticker data input into the tickers route |
| `/data`      | GET |Returns data about the tickers including end, first price, last price, start, tickername|
| `/data`      | DELETE |Deletes the data  |
| `/data/<ticker>`      | GET |Returns data about the ticker including end, first price, last price, start, tickername|
| `/jobs/image…  -d '{"ticker": "<tickername>"}'`      | POST |Returns job ID|
| `/jobs/<jid>`      | GET |takes a job ID and returns the job status |
| `/correlation/<tickername1>/<tickername2>/<start>/<end>/<value_type>`      | GET |Takes in two stocks, the start and end periods, and returns the correlation value using the open value |
| `/help`      | GET |Returns each route and the help methods|

<h3>Running the script</h3>

### Kubernetes Notes

If you change the redis service name, you must change the value of REDIS-IP to the new name
```
env:
    - name: REDIS-IP
      value: <SERVICE-NAME>
```


If you want to change 'REDIS-IP' to something else on this line
```
redis_ip = os.environ.get('REDIS-IP')
```
You umst also change this line in your docker-compose to whatever you have renamed it to
```
environment:
    REDIS-IP: redis-db
```

### INSTRUCTIONS TO RUN

#### MUST DO!!!

git pull this repository

run
```
cd Quant_Stock_Project
```

Then type:
```
mkdir data
```
This ensures that the redis data saves properly


For testing methods 1 and 2, make sure to use a python debug deployment to exec in to and run the curl commands.
Here is an example yaml file for a debug deployment
```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: py-debug-deployment
  labels:
    app: py-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: py-app
  template:
    metadata:
      labels:
        app: py-app
    spec:
      containers:
        - name: py39
          image: python:3.9
          command: ['sleep', '999999999']
```

#### Method 1 - Kubernetes Deployment of the App

kubectl apply -f all of the yaml files in the kubernetes directory

```
kubectl apply -f quant-data-<file>.yml
```

This sums up using the prebuilt application.

Use the following to exec into the debug deployment and then begin curl commands
```
kubectl exec -it <python-debug-deployment-name> -- /bin/bash
```


#### Method 2 - Kubernetes Deployment of your own image

Using the provided quant_stock_api.py and Dockerfiles, build your own image to your liking.
Use
```
docker build -t <username>/<image-name>:<tag> -f Dockerfile.<api/wrk> .
```
In order to run this image in your application, simply change the image name of jthet/quant_stock_api:1.0.1 and jthet/quant_stock_worker:1.0.1 to whatever you have just built in the flask-deployment.yml file

```
version: "3"

services:
    redis-db:
        image: redis:7
        ports:
            - 6379:6379
        volumes:
            - ../data:/data
        user: "1000:1000"
    flask-app:
        build:
            context: ../
            dockerfile: ./docker/Dockerfile.api
        depends_on:
            - redis-db
        environment:
            - REDIS-IP=redis-db
        image: <YOUR_IMAGE_NAME_HERE> #lucalabardini/quant:1.0 jthet/quant_stock_api:1.0.1
        ports:
            - 5000:5000
        volumes:
            - ./config.yaml:/config/config.yaml
    worker:
        build:
            context: ../
            dockerfile: ./docker/Dockerfile.wrk
        depends_on:
            - redis-db
        environment:
            - REDIS-IP=redis-db
        image: <YOUR_IMAGE_NAME_HERE> #lucalabardini/qworker:1.0 jthet/quant_stock_worker:1.0.1
```
After that, follow the steps for Method 1 and you can begin testing the app

#### Method 3 - Docker-Compose

Pull the docker image from dockerhub using (or use your own)
```
docker pull jthet/quant_stock_api:1.0.1
docker pull jthet/quant_stock_worker:1.0.1
```

Then simply type in the terminal:

```
cd docker
docker-compose up
```

Then in a separate terminal run curl commands such as
```
curl localhost:5000/data
```




<h3>Flask app example responses</h3>

#### Note
For methods 1 and 2 be sure to change 'localhost' in the following messages to the IP for the specific flask service
To do so run:
```
kubectl get services
```

This will return something like the following:
```
NAME                                TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE
quant-data-flask-service   ClusterIP   10.233.4.216    <none>        6379/TCP   6d5h
```
Pick the CLUSTER-IP in the row that has `quant-data-flask-service`


#### Examples

To input a specific ticker
```
curl localhost:5000/tickers/AAPL -X POST
```

returns

```
Ticker posted
```
---

To see which tickers have been posted
```
curl localhost:5000/tickers -X GET
```

returns

```
[
  "APPL",
  "AKTX"
]
```
---

To actually input the given tickers data 
```
curl localhost:5000/data -X POST
```

```
curl localhost:5000/data -X GET
```

returns

```
[
  {
    "End": "Wed, 26 Apr 2023 00:00:00 GMT",
    "First Price": 0.1283479928970337,
    "Last Price": 163.75999450683594,
    "Start": "Fri, 12 Dec 1980 00:00:00 GMT",
    "TICKER NAME": "AAPL"
  },
  {
    "End": "Wed, 26 Apr 2023 00:00:00 GMT",
    "First Price": 0.08854199945926666,
    "Last Price": 295.3699951171875,
    "Start": "Thu, 13 Mar 1986 00:00:00 GMT",
    "TICKER NAME": "MSFT"
  }
]
```

for a specific ticker run

```
curl localhost:5000/data/MSFT -X GET
```

```
[
  {
    "End": "Wed, 26 Apr 2023 00:00:00 GMT",
    "First Price": 0.08854199945926666,
    "Last Price": 295.3699951171875,
    "Start": "Thu, 13 Mar 1986 00:00:00 GMT",
    "TICKER NAME": "MSFT"
  }
]
```

---

To see the price history of a specific stock, queue up a job to post. Make sure the ticker is valid and the data has been posted to the db first. Here is the command to post it

```
curl localhost:5000/jobs/image -X POST -d '{"ticker": "AAPL"}'
```
returns
```
{"id": "a2f38a06-1781-435c-846d-47e76ca67b20", "status": "submitted", "ticker": "AAPL"}
```
Then use the specific job ID to run

```
curl localhost:5000/jobs/"a2f38a06-1781-435c-846d-47e76ca67b20"
```
returns
```
{
  "id": "a2f38a06-1781-435c-846d-47e76ca67b20",
  "status": "complete",
  "ticker": "AAPL"
}
```

Then to actually see the plots, run
```
curl localhost:5000/image/AAPL --output image.png
```

```
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100 47712  100 47712    0     0  11.3M      0 --:--:-- --:--:-- --:--:-- 11.3M

```

And it will return an image

---
To see the correlation between two stocks users can run, (an example with AAPL & AKTX)

```
curl localhost:5000/correlation/AAPL/AKTX/'2019-05-06'/'2023-04-12'/Open -X GET
```

```
{
  "correlation coefficient": -0.46150834121485207
}
```

To see all of the possible routes and their functionality run
```
curl localhost:5000/help
```

will return this help message
```
HERE IS A HELP MESSAGE FOR EVERY FUNCTION/ROUTE IN "quant_stock_api.py"

post_tickers:

    Posts the desired ticker stored in the redis db

    Route: <baseURL>/tickers/<ticker>
    Methods: ['POST']

    Args: None

    Returns: String stating success or failure
    

handle_tickers:

    Gets or Deletes the desired tickers stored in the redis db

    Route: <baseURL>/tickers
    Methods: ['GET', 'DELETE']

    Args: None

    Returns: Something corresponding to which method was used
        "DELETE" method: deletes all tickers in redis db
        "GET" method: returns list of all tickers listed in redis db
    

handle_data:

    Manipulates data with 3 different methods with GET, POST, and DELETE method

    Route: <baseURL>/data
    Methods: ['GET', 'POST', 'DELETE']

    Args: None

    Returns: String corresponding to which method was used
        "DELETE" method: deletes all data in redis db
        "POST" method: posts data into redis db
        "GET" method: returns ALL data from redis db
    

get_dataFrame:

    Returns json data for a specific ticker in the data set

    Route: <baseURL>/data/<ticker>
    Methods: ['GET']

    Args:
        ticker (str): ticker 

    Returns:
        json_data: json data of ticker of interest
    

make_image:

    Takes in a stock ticker and (optionally) a time frame.
    Returns an plot of the stock price throughout the time frame
    If a time frame is not specified, the current time and 5 years prior are used. 

    *Sets the plot in a redis database*
        To retrieve image use "base_url/image -X GET >> file_name.png"

    Route: <baseURL>/image/<tickername>
    Methods: ['GET', 'DELETE']

    Args:
        tickername: the stock-of-interest's ticker symbol ex) 'AAPL'
    
    Query Parameters: (for Post method Only)
        "start": The start year of the plot 
        "end": the end year of the plot 

    Returns:
        Success method and a image in a redis data base
    

get_help:

    Returns a message of all the available routes and methods and how to use them 
    
    Route: <baseURL>/help 
    Methods: [GET]

    Args:
        NONE
    Returns:
        help_message (string) : brief descriptions of all available routes and methods
    

job_status:

    This route takes a job ID and returns the job status

    Args: jid

    Returns: status of the job that has been requested
    

job_api:

    API route for creating a new job to do some analysis. This route accepts a JSON payload
    describing the job to be created.

    Input:
    -d '{"ticker": "<TickerNameHere>"}'
    

del_images:

    route: /image -X DELETE

    This route deletes all of the images in the database.
    

cal_correlation:

    Takes in two stocks, the start and end periods, and returns the correlation value using the open value

    Args:
        tickername1: First ticker name ex 'AAPL'
        tickername2: Second ticker name ex 'MSFT'
        start: start of correlation period 'year-month-date' ex '2016-04-25'
        end: end of correlation period 'year-month-date' ex '2017-04-25'

    Returns:
        correlation_coefficient: correlation coefficient
```









