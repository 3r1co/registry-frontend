from sanic import Blueprint

from .status import status
from .repositories import repositories
from .tags import tags
from .manifest import manifest

api = Blueprint.group(status, repositories, tags, manifest, url_prefix='/api')