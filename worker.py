from jobs import q, update_job_status

@q.worker
def execute_job(jid):
    update_job_status(jid, 'in progress')
    # Some code here for job
    update_job_status(jid, 'complete')