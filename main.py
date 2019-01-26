import progressbar
import asyncio
import aiohttp
import argparse
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
    dictlist = list()
    keys = app.db.keys() if app.persistent else app.db
    for key in keys:
        value = app.db.jsonget(key, Path.rootPath()) if app.persistent else app.db[key]
        value.update(repo=key)
        dictlist.append(value)
    return response.json({'data': dictlist})


@app.route("/status")
async def get_jobs(request):
    return response.json(app.jobRunning)


@app.route('/manifest/<repo>/<tag>')
async def tag_handler(request, repo, tag):
    async with aiohttp.ClientSession(loop=loop) as session:
        return await app.reg.retrieve_manifest_v1_for_tag_and_repository(repo, tag, session)


async def fetch():

    app.jobRunning = True

    loop = asyncio.get_event_loop()
    async with aiohttp.ClientSession(loop=loop) as session:
    
        repositories = await app.reg.retrieve_repositories(session)

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
            tasks = [(process_repository(session, progress_queue)) for repo in repositories]
            await asyncio.gather(*tasks)

        if app.cli:
            app.bar.finish()
            app.jobRunning = False
        else: 
            logging.info("Finished updating repositories.")

        app.jobRunning = False


async def process_repository(session, repo_queue):

    repo = await repo_queue.get()

    tags = await app.reg.retrieve_tags_for_repository(repo, session)
    tags_and_sizes = await asyncio.gather(*(app.reg.retrieve_size_for_tag_and_repository(repo, tag, session)
                                            for tag in tags))
    sizes = dict()
    [sizes.update(s["sizes"]) for s in tags_and_sizes]
    total_size = sum(sizes.values())
    if app.persistent:
        app.db.jsonset(repo, Path.rootPath(), {'tags' : tags_and_sizes, 'size': total_size })
    else:
        app.db.update({repo: {'tags' : tags_and_sizes, 'size': total_size }})

    if app.cli:
        app.bar.update(app.count, image="%s (%s)" % (truncate_middle(repo, 30), "{:03d}".format(len(tags))))
        app.count += 1
    else:
        logging.info("Updated repository with %s with %d tags (Total size: %s)" % (repo, len(tags), sizeof_fmt(total_size)))


@app.listener('before_server_start')
async def initialize_scheduler(app, loop):
    app.scheduler = AsyncIOScheduler({'event_loop': loop})
    app.scheduler.add_job(fetch, 'interval', hours=1, next_run_time=datetime.datetime.now(), timezone=utc)
    app.scheduler.configure(timezone=utc)
    app.scheduler.start()


def is_redis_available():
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
    args = parser.parse_args()

    app.cli = args.cli

    app.static('/', './frontend/build/index.html')
    app.static('/static', './frontend/build/static')
    app.static('/favicon.ico', './frontend/build/favicon.ico')

    if sys.platform == 'win32':
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)

    if os.getenv('REDIS_HOST') is not None:
        app.db = Client(host=os.getenv('REDIS_HOST', '192.168.99.100'), charset="utf-8", decode_responses=True)
        if not is_redis_available():
            raise Exception('Cannot launch application without connection to redis')
        app.persistent = True
    else:
        app.db = dict()
        app.persistent = False
        logging.info("Launching Registry UI without database, data won't be persisted.")

    app.reg = RegistryClient(args.registry + "/v2", args.username, args.password, args.cacert)

    logging.info("Welcome to the Docker Registry UI, I'll now retrieve the image repository sizes for %s" % args.registry)

    if not app.cli:
        app.run(host="0.0.0.0", port=int(os.getenv('PORT', 8000)))
    else:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(fetch())
        response = loop.run_until_complete(get_repositories(None))
        print(response.body.decode("utf-8"))
