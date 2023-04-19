# Homework 6: "Say It Ain’t Genes" 
#### Scenario:
We are going to turn our attention to a brand new dataset. The Human Genome Organization (HUGO) is a non-profit which oversees the HUGO Gene Nomenclature Committee (HGNC). The HGNC “approves a unique and meaningful name for every gene”. For this homework, we will download the complete set of HGNC data and inject it into a Redis database through a Flask interface.

#### Objective:
Create a persistant API using redis and flask. 

### Data:
The data for this homework set is a JSON file that contains information on genes found in the human genome, approved by the HGNC (HUGO Genome Nomenclature Committee). The HGNC sets standards for human gene nomenclature. 

This data set holds information on all the HGNC recocgnized genes. A full explanation of the data and each dictionary key can be found at the link below.

The data can be viewed here: [HGNC Data](https://www.genenames.org/download/archive/).


## Scripts:

`gene_api.py`:
Flask application for querying the genome data. The application should loads in the data mentioned above and provides flask routes for a user to digest the data and find specific data points and associated values.
The routes and returns are as follows.


| Route         | Method        | Return |
| ------------- |:-------------:| ------------- |
| `/data`     | GET | Return all data in Redis database | 
| | DELETE |  Delete data in Redis | 
| | POST | Put data into Redis | 
| `/genes`    | GET |  Returns the unique hgnc_id of all the genes in the data set      |
| `/genes/<hgnc_id>`  | GET |  Return all data associated with a specific hgnc_id |



** Note: the variable `<hgnc_id>` takes the format "HGNC:1234", where 1234 is replaced with the unique ID number.



`Dockerfile`: Text document that contains the commands to assemble the `gene_api` Docker image that is used to produce the Docker container when ran. 

`docker-compose.yaml`: YAML script that orchestrates the containerization and port mapping of the flask app and redis database.

## Instructions and Installation:

#### IMPORTANT NOTE:
Before any use, it is required that an empty folder named "data" is created by the user, so that the user has writing priveleges.
This can be done with the following command:

```
$ mkdir data
```

### Building the Docker image

#### Method 1: Pull and use your existing image from Docker Hub

To use the existing Docker Image run the following commands:
```
$ docker pull jthet/gene_api:1.0
```
This will add the image to the users docker images, which can be checked with the command 
```
$ docker images
REPOSITORY            TAG       IMAGE ID       CREATED         SIZE
jthet/gene_api        1.0       c8b0a0825328   4 hours ago     899MB
```

#### Method 2: Build a new image from existing Dockerfile
To build a new image from the existing Dockerfile, execute the following commands:
Note: Dockerfile must be in the current directory when this command is executed.
```
$ docker build -t <dockerhubusername>/<code>:<version> .
```
Example:
```
$ docker build -t jthet/gene_api:1.0 .
Sending build context to Docker daemon   7.68kB
Step 1/4 : FROM python:3.8.10
 ---> a369814a9797
Step 2/4 : RUN pip install Flask==2.2.0 redis requests
 ---> Using cache
 ---> 20dabd1acd2c
Step 3/4 : ADD ./gene_api.py /gene_api.py
 ---> 76fe0eec9b92
Step 4/4 : CMD ["python3", "/gene_api.py"]
 ---> Running in fe2c0f85b0db
Removing intermediate container fe2c0f85b0db
 ---> ba3e81e8f47f
Successfully built ba3e81e8f47f
Successfully tagged jthet/gene_api:1.0
```

Check the image was built with `$ docker images`:
```
$ docker images
REPOSITORY                 TAG        IMAGE ID       CREATED              SIZE
jthet/gene_api             1.0        2883079fad18   About a minute ago   928MB

```

### Launch the containerized app and Redis using docker-compose
After the image is created, use the command `docker-compose up`:

```
$ docker-compose up
Starting homework06_redis-db_1 ... done
.
.
.
flask-app_1  |  * Debugger is active!
flask-app_1  |  * Debugger PIN: 411-831-197
```
This will create 2 containers; the flask app and the redis database/

Check these containers exist with:
```
$ docker ps
CONTAINER ID   IMAGE                COMMAND                  CREATED              STATUS              PORTS                                       NAMES
9df1e28ee08e   jthet/gene_api:1.0   "python3 /gene_api.py"   About a minute ago   Up About a minute   0.0.0.0:5000->5000/tcp, :::5000->5000/tcp   homework06_flask-app_1
d00467cc9354   redis:7              "docker-entrypoint.s…"   3 hours ago          Up About a minute   0.0.0.0:6379->6379/tcp, :::6379->6379/tcp   homework06_redis-db_1

```

You can now use the flask-redis api through curl: see the "Running the Flask App" section

To close the containers use the command:

```
$ docker-compose down
Stopping homework06_flask-app_1 ... done
Stopping homework06_redis-db_1  ... done
Removing homework06_flask-app_1 ... done
Removing homework06_redis-db_1  ... done
Removing network homework06_default
```



### Running the Flask App

#### Using the Flask app
Each route can be accesd with the following:
```
$ curl localhost:5000/ [ROUTE]
```


All of the routes and example output are shown below.

Route: `/data -X POST`
```
$ curl localhost:5000/data -X POST
Data Loaded there are 43625 keys in the db
```


Route: `/data -X GET` or just `/data`
```
$ curl localhost:5000/data -X POST
.
.
.
  {
    "_version_": 1761544698841792512,
    "agr": "HGNC:52786",
    "date_approved_reserved": "2016-12-09",
    "date_modified": "2016-12-09",
    "ensembl_gene_id": "ENSG00000234148",
    "entrez_id": "101927424",
    "gene_group": [
      "Long intergenic non-protein coding RNAs"
    ],
    "gene_group_id": [
      1986
    ],
    "hgnc_id": "HGNC:52786",
    "location": "2q14.1",
    "location_sortable": "02q14.1",
    "locus_group": "non-coding RNA",
    "locus_type": "RNA, long non-coding",
    "name": "long intergenic non-protein coding RNA 1961",
    "refseq_accession": [
      "XR_007087198"
    ],
    "rna_central_id": [
      "URS0000EF0A8F"
    ],
    "status": "Approved",
    "symbol": "LINC01961",
    "uuid": "b2a7b185-0b99-409e-bae9-7709ead4ddc4",
    "vega_id": "OTTHUMG00000184091"
  }
]
```

Route: `/data -X DELETE`
```
$ curl localhost:5000/data -X DELETE
data deleted, there are 0 keys in the db
```


Route: `/genes`
```
$ curl localhost:5000/genes
.
.
.
  "HGNC:28298",
  "HGNC:46772",
  "HGNC:48882",
  "HGNC:45071",
  "HGNC:32955",
  "HGNC:54917",
  "HGNC:25579",
  "HGNC:3074",
  "HGNC:52786"
]
```
Route: `/genes/<hgnc_id>` 
```
$ curl localhost:5000/genes/HGNC:52786
{
  "_version_": 1761544698841792512,
  "agr": "HGNC:52786",
  "date_approved_reserved": "2016-12-09",
  "date_modified": "2016-12-09",
  "ensembl_gene_id": "ENSG00000234148",
  "entrez_id": "101927424",
  "gene_group": [
    "Long intergenic non-protein coding RNAs"
  ],
  "gene_group_id": [
    1986
  ],
  "hgnc_id": "HGNC:52786",
  "location": "2q14.1",
  "location_sortable": "02q14.1",
  "locus_group": "non-coding RNA",
  "locus_type": "RNA, long non-coding",
  "name": "long intergenic non-protein coding RNA 1961",
  "refseq_accession": [
    "XR_007087198"
  ],
  "rna_central_id": [
    "URS0000EF0A8F"
  ],
  "status": "Approved",
  "symbol": "LINC01961",
  "uuid": "b2a7b185-0b99-409e-bae9-7709ead4ddc4",
  "vega_id": "OTTHUMG00000184091"
}
```




