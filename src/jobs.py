from hotqueue import HotQueue
import redis
import uuid
import os
import json


def get_queue_db():
    redis_ip = os.environ.get('REDIS-IP')
    if not redis_ip:
        raise Exception()
    return HotQueue("queue", host=redis_ip, port=6379, db=4)

def get_redis_client():
    redis_ip = os.environ.get('REDIS-IP')
    if not redis_ip:
        raise Exception()
    return redis.Redis(host=redis_ip, port=6379, db=3)

q = get_queue_db()
rd = get_redis_client()

def generate_jid():
    """
    Generate a pseudo-random identifier for a job.
    """
    return str(uuid.uuid4())

def generate_job_key(jid):
    """
    Generate the redis key from the job id to be used when storing, retrieving or updating
    a job in the database.
    """
    return 'job.{}'.format(jid)

def instantiate_job(jid, status, ticker):
    """
    Create the job object description as a python dictionary. Requires the job id, status,
    and ticker parameters.
    """
    if type(jid) == str:
        return {'id': jid,
                'status': status,
                'ticker': ticker
        }
    return {'id': jid.decode('utf-8'),
            'status': status.decode('utf-8'),
            'ticker': ticker.decode('utf-8')
    }

def save_job(job_key, job_dict):
    """Save a job object in the Redis database."""
    rd.set(job_key, json.dumps(job_dict))

def queue_job(jid):
    """Add a job to the redis queue."""
    q.put(jid)

def add_job(ticker, status="submitted"):
    """Add a job to the redis queue."""
    jid = generate_jid()
    job_dict = instantiate_job(jid, status, ticker)
    # update call to save_job:
    save_job(generate_job_key(jid), job_dict)
    # update call to queue_job:
    queue_job(jid)
    return job_dict

def get_job_by_id(jid):
    """
    Gets job by id name
    """
    return json.loads(rd.get(generate_job_key(jid)))

def update_job_status(jid, status):
    """Update the status of job with job id `jid` to status `status`."""
    job = get_job_by_id(jid)
    if job:
        job['status'] = status
        save_job(generate_job_key(jid), job)
    else:
        raise Exception()