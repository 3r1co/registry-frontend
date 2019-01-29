from sanic import Blueprint, response
from rejson import Path
from helpers.constants import REPO_PREFIX

tags = Blueprint('tags', url_prefix='/tags')

@tags.route("/<repo:(?:.+/)?([^:]+)(?::.+)?>")
async def get_tags(request, repo):
    app = request.app
    return response.json(app.db.jsonget(REPO_PREFIX + repo, Path.rootPath())) if app.persistent else response.json(app.db[repo])