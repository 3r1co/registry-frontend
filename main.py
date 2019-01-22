import progressbar
import asyncio
import argparse
import json
import os
import sys
import datetime
import logging

from sanic import Sanic
from sanic import response

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import utc

from helper import truncate_middle, sizeof_fmt
from registryclient import RegistryClient

cli = False
app = Sanic()
sizes = dict()
widgets=[ progressbar.DynamicMessage("image"), progressbar.Bar(), progressbar.Percentage(),' [', progressbar.Timer(), '] ' ]

@app.route("/repositories.json")
async def get_repositories(request):
    dictlist = []
    for repo, value in sizes.items():
        value.update(repo=repo)
        dictlist.append(value)
    return response.json({'data': dictlist})

async def fetch():   
    
    await reg.retrieveRepositories(sizes)

    if cli:
        bar = progressbar.ProgressBar(maxval=len(sizes), widgets=widgets)
        count = 1
    else:
        logging.info("Fetching the info for %d repositories" % len(sizes))

    for repo in sizes.keys():
        tags = list()
        sizeDict = dict()
        await reg.retrieveTagsForRepository(repo, tags)
        await asyncio.gather(*(reg.retrieveSizeForTagAndRepository(repo, tag, sizeDict) for tag in tags))

        size = sum(sizeDict.values())
        sizes[repo] = { 'tags' : len(tags), 'size': size }

        if cli:
            bar.update(count, image="%s (%s)" % (truncate_middle(repo, 30), "{:03d}".format(len(tags))))
            count += 1
        else:
            logging.info("Updated repository with %s with %d tags (Total size: %s)" % (repo, len(tags), sizeof_fmt(size)))

    if cli:
        bar.finish()
    else: 
        logging.info("Finished updating repositories.")

@app.listener('before_server_start')
async def initialize_scheduler(app, loop):
    scheduler = AsyncIOScheduler({'event_loop': loop})
    scheduler.add_job(fetch, 'interval', hours=1, next_run_time=datetime.datetime.now(), timezone=utc)
    scheduler.configure(timezone=utc)
    scheduler.start()

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

    cli = args.cli
    
    logging.info("Welcome to the Registry Size Reader, I'll now retrieve the image repository sizes for %s" % args.registry)

    app.static('/', './static/index.html')
    app.static('/vendor', './static/vendor')
    app.static('/favicon.ico', './static/favicon.ico')

    if sys.platform == 'win32':
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)

    reg = RegistryClient(args.registry + "/v2", args.username, args.password, args.cacert)

    if not cli:
        app.run(host="0.0.0.0", port=int(os.getenv('PORT', 8000)))
    else:
        loop = asyncio.get_event_loop() 
        loop.run_until_complete(fetch())
        logging.info(json.dumps(sizes))