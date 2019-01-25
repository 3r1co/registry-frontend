import progressbar
import asyncio
import aiohttp
import argparse
import json
import os
import sys
import datetime
import logging
import redis
from rejson import Client, Path

from sanic import Sanic
from sanic import response

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import utc

from helper import truncate_middle, sizeof_fmt
from registryclient import RegistryClient

app = Sanic()

@app.route("/repositories.json")
async def get_repositories(request):
    dictlist = []
    for key in app.db.keys():
        value = app.db.jsonget(key, Path.rootPath())
        value.update(repo=key)
        dictlist.append(value)
    return response.json({'data': dictlist})

@app.route("/status")
async def get_jobs(request):
    return response.json(app.jobRunning)

async def fetch():

    app.jobRunning = True

    loop = asyncio.get_event_loop()
    connector = aiohttp.TCPConnector(limit = 100)
    async with aiohttp.ClientSession(loop=loop, connector=connector) as session:
    
        repositories = await reg.retrieveRepositories(session)

        progress_queue = asyncio.Queue(loop=loop)
        for repo in repositories:
            progress_queue.put_nowait(repo)

        logging.info("Fetching the info for %d repositories" % len(repositories))

        if app.cli:
            widgets=[ progressbar.DynamicMessage("image"), progressbar.Bar(), progressbar.Percentage(),' [', progressbar.Timer(), '] ' ]
            app.bar = progressbar.ProgressBar(maxval=len(repositories), widgets=widgets)
            app.bar.start()
            app.count = 1
        
        async with aiohttp.ClientSession(loop=loop) as session:
            tasks = [(processRepository(session, progress_queue)) for repo in repositories]
            await asyncio.gather(*tasks)

        if app.cli:
            app.bar.finish()
            app.jobRunning = False
        else: 
            logging.info("Finished updating repositories.")

        app.jobRunning = False

async def processRepository(session, repo_queue):

    repo = await repo_queue.get()

    repoSizeDict = dict()
    tags = await reg.retrieveTagsForRepository(repo, session)
    repoSizeDict = await asyncio.gather(*(reg.retrieveSizeForTagAndRepository(repo, tag, session) for tag in tags))

    sizes = dict()
    [sizes.update(s) for s in repoSizeDict]
    size = sum(sizes.values())
    app.db.jsonset(repo, Path.rootPath(), {'tags' : tags, 'size': size })

    if app.cli:
        app.bar.update(app.count, image="%s (%s)" % (truncate_middle(repo, 30), "{:03d}".format(len(tags))))
        app.count += 1
    else:
        logging.info("Updated repository with %s with %d tags (Total size: %s)" % (repo, len(tags), sizeof_fmt(size)))

@app.listener('before_server_start')
async def initialize_scheduler(app, loop):
    app.scheduler = AsyncIOScheduler({'event_loop': loop})
    app.scheduler.add_job(fetch, 'interval', hours=1, next_run_time=datetime.datetime.now(), timezone=utc)
    app.scheduler.configure(timezone=utc)
    app.scheduler.start()

def is_redis_available():
    # ... get redis connection here, or pass it in. up to you.
    try:
        app.db.get('*')  # getting None returns None or throws an exception
    except (redis.exceptions.ConnectionError, redis.exceptions.BusyLoadingError):
        logging.error("Cannot connect to redis, please check connection.")
        return False
    return True

if __name__ == "__main__":

    logging.basicConfig(level=os.environ.get('LOGLEVEL', 'INFO').upper(), 
                        format='%(asctime)s %(message)s', 
                        datefmt='%m/%d/%Y %I:%M:%S %p')

    parser = argparse.ArgumentParser()
    parser.add_argument('--registry',help='Specify the URL of your docker registry (use protocol prefix like http or https)', required=True)
    parser.add_argument('--username', help='Specify Username', required=False)
    parser.add_argument('--password', help='Specify Password', required=False)
    parser.add_argument('--cacert', help='Path to your custom root CA', required=False)
    parser.add_argument('--cli', help='Flag for a one time analysis instead of you', required=False, action='store_true')
    args=parser.parse_args()

    app.cli = args.cli

    app.static('/', './static/index.html')
    app.static('/vendor', './static/vendor')
    app.static('/favicon.ico', './static/favicon.ico')

    if sys.platform == 'win32':
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)

    app.db = Client(host=os.getenv('REDIS_HOST', '192.168.99.100'), charset="utf-8", decode_responses=True)
    if not is_redis_available():
        raise Exception('Cannot launch application without redis')

    reg = RegistryClient(args.registry + "/v2", args.username, args.password, args.cacert)

    logging.info("Welcome to the Docker Registry UI, I'll now retrieve the image repository sizes for %s" % args.registry)

    if not app.cli:
        app.run(host="0.0.0.0", port=int(os.getenv('PORT', 8000)))
    else:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(fetch())
        response = loop.run_until_complete(get_repositories(None))