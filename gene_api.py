from flask import Flask, request, send_file
import redis
import requests
import json
import os
import matplotlib.pyplot as plt
import io

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

rd = get_redis_client()

rd_image = get_redis_image_db()

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
        response = requests.get(url = 'https://ftp.ebi.ac.uk/pub/databases/genenames/hgnc/json/hgnc_complete_set.json')
        data = response.json()

        for item in data['response']['docs']:
            rd.set(item.get('hgnc_id'), json.dumps(item))
        return f'Data Loaded there are {len(rd.keys())} keys in the db\n'
    

    elif method == 'GET':
        output_list = []
        keys = rd.keys()
        for key in keys:
            output_list.append(json.loads(rd.get(key)))
        return output_list
        

    elif method == 'DELETE':
        rd.flushdb()
        return f'data deleted, there are {len(rd.keys())} keys in the db\n'


    else:
        return 'the method you tried is not supported\n'

    return f'method completed \n'


@app.route('/genes', methods = ['GET'])
def get_ids() -> list:
    '''
    Returns json-formatted list of all hgnc_ids

    Args: NONE

    Returns:
        id_list: List of all the hgnc IDs
    '''
    id_list = []

    for key in rd.keys():
        id_list.append(key)

    return(id_list)



@app.route('/genes/<hgnc_id>', methods = ['GET'])
def get_hgnc_data(hgnc_id) -> dict:
    '''
    Return all data associated with <hgnc_id>

    ROUTE: /gene/<hgnc_id>

    Args:
        hgnc_id:    The hgnc ID from the HGNC data set
    
    Returns:
        all data associated with the given hcnc ID

    '''
    if len(rd.keys()) == 0:
        return "Database is empty. Please post data. \n"

    for key in rd.keys():
        if str(key) == str(hgnc_id):
            return json.loads(rd.get(key))

    return "Given ID did not match any IDs in the Data base\n"



@app.route('/image', methods = ['POST', 'GET', 'DELETE'])
def image_manip():
    '''
    Manipulates image database with GET, POST, and DELETE methods
    
    Args: None

    Methods:
        "DELETE" method: deletes all images in database
        "POST" method: posts image into redis db
        "GET" method: returns image

    Returns:
        "DELETE" and "POST" methods: return string confirming action
        "GET" method: returns image from redis db which is then piped into a file
            example: $ curl localhost:5000/image -X GET >> image.png
        
    '''

    method = request.method

    if method == 'GET':
        if(len(rd_image.keys()) == 0):
            return "No images in the Database\n"
        else:
            image = rd_image.get('image')
            buf = io.BytesIO(image)
            buf.seek(0)

            existing_images = rd_image.keys() == 0

            file_name = f'image{existing_images}.png'
            return send_file(buf, mimetype = 'image/png') #, as_attachment=True, download_name=file_name)   <--- Could potentially add, works without

    elif method == 'POST':
        if (len(rd.keys()) == 0):
            return "No data in the data base\n"
        else:

            chromosome_counts = [0] * 23

            for item in rd.keys():
                try:
                    spec_id = rd.get(item)
                    spec_id = json.loads(spec_id)

                    location = spec_id['location_sortable']
                    location = str(location)

                    if location[0] == '0':
                        chromosome = str(location[1])
                    else:
                        chromosome = str(location[0] + location[1])

                    
                    if chromosome.isdigit():
                        index = int(chromosome) - 1
                        chromosome_counts[index] = chromosome_counts[index] + 1
                    else:
                        pass
                except:
                    pass


            ## Plotting
            chromosome_names = ['chr' + str(i) for i in range(1, 24)]

            plt.pie(chromosome_counts, labels=chromosome_names, autopct='%1.1f%%')
            plt.title('Proportion of Genes on Each Chromosome')
            plt.axis('equal')

            buf = io.BytesIO()
            plt.savefig(buf, format = 'png')
            buf.seek(0)

            rd_image.set('image', buf.getvalue())

            return 'Image is posted\n'

    elif method =='DELETE':
        rd_image.flushdb()
        return f'Plot deleted, there are {len(rd_image.keys())} images in the db\n'



if __name__ == '__main__':

    app.run(debug=True, host='0.0.0.0')
