from jobs import get_job_by_id, update_job_status, q
from quant_stock_api import post_image

@q.worker
def execute_job(jid):
    update_job_status(jid, 'in progress')
    # Some code here for job
    symbol = get_job_by_id(jid)['ticker']
    post_image(symbol)

    update_job_status(jid, 'complete')
