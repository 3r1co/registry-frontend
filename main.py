""" Docker Registry UI Backend """
import asyncio
import logging
import os
import sys
from types import SimpleNamespace

from sanic import Sanic

from api import api
from api.repositories import get_repositories
from helpers.data_retrieval import fetch
from helpers.init_functions import init_app, init_args, init_db

def main():
    logging.basicConfig(level=os.environ.get('LOGLEVEL', 'INFO').upper(), 
                        format='%(asctime)s %(message)s', 
                        datefmt='%m/%d/%Y %I:%M:%S %p')

    if sys.platform == 'win32':
        asyncio.set_event_loop(asyncio.ProactorEventLoop())

    app = Sanic()
    app.blueprint(api)

    args = init_args()
    init_db(app, args)
    init_app(app, args)

    logging.info("Welcome to the Docker Registry UI, I'll now retrieve the repositories for %s", args.registry)

    if not args.cli:
        app.run(host="0.0.0.0", port=int(args.port), debug=args.debug)
    else:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(fetch(app))
        request = SimpleNamespace()
        setattr(request, "app", app)
        response = loop.run_until_complete(get_repositories(request))
        print(response.body.decode("utf-8"))

if __name__ == "__main__":
    main()
