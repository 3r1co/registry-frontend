from sanic import Blueprint

static = Blueprint('static', url_prefix='/')
static.static('/', './frontend/build/index.html')
static.static('/*', './frontend/build/')
static.static('/static', './frontend/build/static')
static.static('/favicon.ico', './frontend/build/favicon.ico')
