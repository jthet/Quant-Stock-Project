FROM python:3.8.10

RUN pip install Flask==2.2.0
RUN pip install redis
RUN pip install requests
RUN pip install matplotlib==3.7.1
RUN pip install yfinance==0.2.18
RUN pip install pandas==2.0.0
RUN pip install hotqueue==0.2.8

ADD ./quant_stock_api.py /quant_stock_api.py
ADD ./jobs.py /jobs.py
ADD ./worker.py /worker.py

CMD ["python3", "/quant_stock_api.py"]
