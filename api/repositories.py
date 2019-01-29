from rejson import Path
from sanic import Blueprint, response

from helpers.constants import REPO_PREFIX

repositories = Blueprint('repositories', url_prefix='/repositories')

@repositories.route("/")
async def get_repositories(request):
    dictlist = list()
    app = request.app
    repos = app.db.keys("repo_*") if app.persistent else app.db
    for repo in repos:
        value = app.db.jsonget(repo, Path.rootPath()) if app.persistent else app.db[repo]
        len_to_truncate = len(REPO_PREFIX) if app.persistent else 0
        dictlist.append({'repo': repo[len_to_truncate:], 'tags': len(value['tags']), 'size': value['size']})
    return response.json({'data': dictlist})