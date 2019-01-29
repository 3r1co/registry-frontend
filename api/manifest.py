import asyncio
import aiohttp
from helpers.constants import MANIFEST_PREFIX
from sanic import Blueprint, response
from rejson import Path

manifest = Blueprint('manifest', url_prefix='/manifest')

@manifest.route('/<repo:path>/<tag>')
async def tag_handler(request, repo, tag):
    loop = asyncio.get_event_loop()
    key = repo + "/" + tag
    app = request.app
    manifest = app.db.jsontype(MANIFEST_PREFIX + key, Path.rootPath()) if app.persistent else app.manifests[key]
    if manifest is not None:
        return response.json(app.db.jsonget(MANIFEST_PREFIX + key, Path.rootPath())) if app.persistent else response.json(manifest)
    else:
        async with aiohttp.ClientSession(loop=loop) as session:
            resp = await app.reg.retrieve_manifest_v1_for_tag_and_repository(repo, tag, session)
            if app.persistent:
                app.db.jsonset(MANIFEST_PREFIX + key, Path.rootPath(), resp.decode("utf-8"))
            else:
                app.manifests[key] = resp.decode("utf-8")
            return response.json(resp.decode("utf-8"))