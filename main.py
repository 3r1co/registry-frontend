""" Docker Registry UI Backend """
import asyncio
import logging
import os
from types import SimpleNamespace

import sys
from sanic import Sanic

from api import api
from api.repositories import get_repositories
from api.scheduler import scheduler
from api.static import static
from helpers.data_retrieval import fetch
from helpers.init_functions import init_app, init_args, init_db

app = Sanic(__name__)


def main():
    logging.basicConfig(level=os.environ.get('LOGLEVEL', 'INFO').upper(), 
                        format='%(asctime)s %(message)s', 
                        datefmt='%m/%d/%Y %I:%M:%S %p')

    if sys.platform == 'win32':
        asyncio.set_event_loop(asyncio.ProactorEventLoop())

    app.blueprint(api)
    app.blueprint(scheduler)
    app.blueprint(static)

    args = init_args(sys.argv[1:])
    init_db(app, args)
    init_app(app, args)

    logging.info("Welcome to the Docker Registry UI, I'll now retrieve the repositories for %s", args.registry)

    if not args.cli:
        app.run(host=args.listen, port=int(args.port), debug=args.debug)
    else:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(fetch(app))
        request = SimpleNamespace()
        setattr(request, "app", app)
        response = loop.run_until_complete(get_repositories(request))
        print(response.body.decode("utf-8"))


if __name__ == "__main__":
    main()
