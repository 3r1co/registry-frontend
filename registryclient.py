import asyncio
import aiohttp
import ssl
import json
import logging

class RegistryClient:

    def __init__(self, registry, username, password, cacert):
        self.registry = registry
        if username and password:
            self.auth = aiohttp.BasicAuth(username, password)
        else:
            self.auth = aiohttp.BasicAuth("xxx", "xxx")
        if cacert:
            self.sslcontext = ssl.create_default_context(cafile=cacert)
        else:
            self.sslcontext = ssl.create_default_context()


    async def retrieveRepositories(self, session):
        repositories = list()
        session.auth = self.auth
        async with session.get(self.registry + "/_catalog", ssl=self.sslcontext) as resp:
            response = await resp.json()
            repositories.extend(response["repositories"])
            return repositories

    async def retrieveTagsForRepository(self, repository, session):
        tags = list()
        session.auth = self.auth
        async with session.get(self.registry + "/" + repository + "/tags/list", ssl=self.sslcontext) as resp:
            response = await resp.json()
            tags.extend(response["tags"])
            return tags

    async def retrieveSizeForTagAndRepository(self, repository, tag, session):
        headers = {'accept': 'application/vnd.docker.distribution.manifest.v2+json' }
        sizeDict = dict()
        session.auth = self.auth
        try:
            async with session.get(self.registry + "/" + repository + "/manifests/" + tag, ssl=self.sslcontext, headers=headers) as resp:
                response = await resp.read()
                manifest = json.loads(response)
                if "config" in manifest:
                    sizeDict["manifest"] = manifest["config"]["size"]
                if "layers" in manifest:
                    for layer in manifest["layers"]:
                        sizeDict[layer["digest"]] = layer["size"]
        except (aiohttp.ServerDisconnectedError):
            logging.error("Could not retrieve information for image %s:%s" % (repository, tag))
        return sizeDict

