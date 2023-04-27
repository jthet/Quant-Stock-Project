# Quant Stock Project

This project is an application that enables users to run various simulations on the stock market using Flask, Docker, Redis database, and Kubernetes clusters. The main objective of the project is to analyze past data and determine the optimal portfolio selection that minimizes risks while optimizing potential returns.


<h3>Data Used</h3>
To access the data required for the simulations, the application connects to an API called yfinance, which is linked to Yahoo! Finance page. The yfinance API provides the historical stock market data needed for the simulations. Here is a link for more information about yfinance https://pypi.org/project/yfinance/

<h2>Scripts</h2>

<h5>Docker Folder</h5>

`docker-compose.yml` - 

`Dockerfile.api` -

`Dockerfile.wrk` - 


<h5>Kubernetes Folder</h5>



<h5>SRC Folder</h5>

`quant_stock_api.py` - 

`jobs.py` - 

`worker.py` - 


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


<h3>Flask app example responses</h3>

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











