import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import utc
from sanic import Blueprint, response

from helpers.data_retrieval import fetch

status = Blueprint('status', url_prefix='/status')

@status.route("/")
async def get_jobs(request):
    return response.json(request.app.jobRunning)

@status.listener('before_server_start')
async def initialize_scheduler(app, loop):
    scheduler = AsyncIOScheduler({'event_loop': loop})
    scheduler.add_job(fetch, 'interval', hours=1, next_run_time=datetime.datetime.now(), timezone=utc, args=[app])
    scheduler.configure(timezone=utc)
    scheduler.start()
