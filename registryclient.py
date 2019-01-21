import asyncio
import aiohttp
import ssl
import json

class RegistryClient:

    def __init__(self, registry, username, password, cacert):
        self.registry = registry
        self.auth = aiohttp.BasicAuth(username, password)
        if cacert:
            self.sslcontext = ssl.create_default_context(cafile=cacert)
        else:
            self.sslcontext = ssl.create_default_context()


    async def retrieveRepositories(self, repositories):
        async with aiohttp.ClientSession(auth=self.auth) as session:
            async with session.get(self.registry + "/_catalog", ssl=self.sslcontext) as resp:
                response = await resp.json()
                repositories.extend(response["repositories"])

    async def retrieveTagsForRepository(self, repository, tags):
        async with aiohttp.ClientSession(auth=self.auth) as session:
            async with session.get(self.registry + "/" + repository + "/tags/list", ssl=self.sslcontext) as resp:
                response = await resp.json()
                tags.extend(response["tags"])

    async def retrieveSizeForTagAndRepository(self, repository, tag, sizeDict):
        headers = {'accept': 'application/vnd.docker.distribution.manifest.v2+json' }
        async with aiohttp.ClientSession(auth=self.auth) as session:
            async with session.get(self.registry + "/" + repository + "/manifests/" + tag, ssl=self.sslcontext, headers=headers) as resp:
                response = await resp.read()
                manifest = json.loads(response)
                if "config" in manifest:
                    sizeDict["manifest"] = manifest["config"]["size"]
                if "layers" in manifest:
                    for layer in manifest["layers"]:
                        sizeDict[layer["digest"]] = layer["size"]