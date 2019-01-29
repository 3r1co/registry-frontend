import logging

from configargparse import ArgParser
from rejson import Client

from helpers.helper import is_redis_available
from registryclient import RegistryClient


def init_args(args):
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
    parser.add_argument('--listen', help='Hostname of your Redis instance', required=False,
                        env_var='LISTEN', default="0.0.0.0")
    parser.add_argument('--port', help='Hostname of your Redis instance', required=False,
                        env_var='PORT', default="8000")
    parser.add_argument('--cli', help='Flag for a one time analysis instead of you', required=False,
                        action='store_true')
    parser.add_argument('--debug', help='Start Sanic in debug mode', required=False,
                        action='store_true')
    return parser.parse_args(args)


def init_db(app, args):
    if args.redis is not None:
        app.db = Client(host=args.redis, charset="utf-8", decode_responses=True)
        if not is_redis_available(app):
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
