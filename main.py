import progressbar
import asyncio
import aiohttp
import os
import sys
import datetime
import logging
import redis
import json
from rejson import Client, Path
from configargparse import ArgParser

from sanic import Sanic
from sanic import response

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import utc

from helper import truncate_middle, sizeof_fmt
from registryclient import RegistryClient

app = Sanic()

REPO_PREFIX = "repo_"
MANIFEST_PREFIX = "manifest_"

@app.route("/status")
async def get_jobs(request):
    return response.json(app.jobRunning)


@app.route("/repositories")
async def get_repositories(request):
    dictlist = list()
    repos = app.db.keys("repo_*") if app.persistent else app.db
    for repo in repos:
        value = app.db.jsonget(repo, Path.rootPath()) if app.persistent else app.db[repo]
        dictlist.append({'repo': repo[len(REPO_PREFIX):], 'tags': len(value['tags']), 'size': value['size']})
    return response.json({'data': dictlist})


@app.route("/tags/<repo:(?:.+/)?([^:]+)(?::.+)?>")
async def get_tags(request, repo):
    return response.json(app.db.jsonget(REPO_PREFIX + repo, Path.rootPath())) if app.persistent else response.json(app.db[repo])


@app.route('/manifest/<repo:path>/<tag>')
async def tag_handler(request, repo, tag):
    loop = asyncio.get_event_loop()
    key = repo + "/" + tag
    manifest = app.db.jsontype(MANIFEST_PREFIX + key, Path.rootPath()) if app.persistent else app.manifests[key]
    if manifest is not None:
        return response.json(app.db.jsonget(MANIFEST_PREFIX + key, Path.rootPath()))
    else:
        async with aiohttp.ClientSession(loop=loop) as session:
            resp = await app.reg.retrieve_manifest_v1_for_tag_and_repository(repo, tag, session)
            if app.persistent:
                app.db.jsonset(MANIFEST_PREFIX + key, Path.rootPath(), resp.decode("utf-8"))
            else:
                app.manifests[key] = resp.decode("utf-8")
            return response.json(resp.decode("utf-8"))


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
            widgets=[ progressbar.DynamicMessage("image"), progressbar.Bar(),
                      progressbar.Percentage(),' [', progressbar.Timer(), '] ']
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
        app.db.jsonset(REPO_PREFIX + repo, Path.rootPath(), {'tags' : tags_and_sizes, 'size': total_size })
    else:
        app.db.update({repo: {'tags' : tags_and_sizes, 'size': total_size }})    

    if app.cli:
        app.bar.update(app.count, image="%s (%s)" % (truncate_middle(repo, 30), "{:03d}".format(len(tags))))
        app.count += 1
    else:
        logging.info("Updated repository with %s with %d tags (Total size: %s)" %
                     (repo, len(tags), sizeof_fmt(total_size)))


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

def init_args():
    parser = ArgParser()
    parser.add_argument('--registry',
                        help='Specify the URL of your docker registry (use protocol prefix like http or https)',
                        required=True,
                        env_var='DOCKER_REGISTRY')
    parser.add_argument('--username', help='Specify Username', required=False,
                        env_var='DOCKER_USERNAME')
    parser.add_argument('--password', help='Specify Password', required=False,
                        env_var='DOCKER_PASSWORD')
    parser.add_argument('--cacert', help='Path to your custom root CA', required=False,
                        env_var='DOCKER_CACERT')
    parser.add_argument('--redis', help='Hostname of your Redis instance', required=False,
                        env_var='REDIS_HOST')
    parser.add_argument('--port', help='Hostname of your Redis instance', required=False,
                        env_var='PORT', default="8000")
    parser.add_argument('--cli', help='Flag for a one time analysis instead of you', required=False,
                        action='store_true')
    return parser.parse_args()

def init_db(app, args):
    if args.redis is not None:
        app.db = Client(host=args.redis, charset="utf-8", decode_responses=True)
        if not is_redis_available():
            raise Exception('Cannot launch application without connection to redis')
        app.persistent = True
    else:
        app.db = dict()
        app.manifests = dict()
        app.persistent = False
        logging.info("Launching Registry UI without database, data won't be persisted.")

def init_app(app, args):
    app.cli = args.cli
    app.static('/', './frontend/build/index.html')
    app.static('/static', './frontend/build/static')
    app.static('/favicon.ico', './frontend/build/favicon.ico')
    app.reg = RegistryClient(args.registry + "/v2", args.username, args.password, args.cacert)

if __name__ == "__main__":

    logging.basicConfig(level=os.environ.get('LOGLEVEL', 'INFO').upper(), 
                        format='%(asctime)s %(message)s', 
                        datefmt='%m/%d/%Y %I:%M:%S %p')

    if sys.platform == 'win32':
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)

    args = init_args()
    init_db(app, args)
    init_app(app, args)

    logging.info("Welcome to the Docker Registry UI, I'll now retrieve the repositories for %s" % args.registry)

    if not app.cli:
        app.run(host="0.0.0.0", port=int(args.port))
    else:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(fetch())
        response = loop.run_until_complete(get_repositories(None))
        print(response.body.decode("utf-8"))
