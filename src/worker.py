from jobs import get_job_by_id, update_job_status, q
from quant_stock_api import post_image

@q.worker
def execute_job(jid):
    update_job_status(jid, 'in progress')
    # Some code here for job
    symbol = get_job_by_id(jid)['ticker']
    start = get_job_by_id(jid)['start']
    end = get_job_by_id(jid)['end']
    post_image(symbol, start, end)

    update_job_status(jid, 'complete')


execute_job()