import jobs
import quant_stock_api

@q.worker
def execute_job(jid):
    jobs.update_job_status(jid, 'in progress')
    # Some code here for job
    

    jobs.update_job_status(jid, 'complete')