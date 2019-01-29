import os
import aiohttp
import asyncio
import pytest
import json
from aioresponses import aioresponses
from registryclient import RegistryClient

@pytest.fixture(scope = 'module')
def global_data():
    return {'registry': "http://registry",
            'repository': "test/alpine",
            'tag': "latest"}

@pytest.fixture(scope = 'module')
def client(global_data):
    return RegistryClient(global_data["registry"], None, None, None)

@pytest.mark.asyncio
async def test_retrieve_repositories(global_data, client):
    f = open(get_resource('response_repositories.json'), "r")
    with aioresponses() as m:
        m.get("%s/v2/_catalog" % global_data["registry"], status=200, body=f.read())
        session = aiohttp.ClientSession()
        resp = await client.retrieve_repositories(session)
        expect = set([global_data["repository"]])
        assert check_equal(resp, expect)
        await session.close()


@pytest.mark.asyncio
async def test_retrieve_tags_for_repository(global_data, client):
    f = open(get_resource('response_tags.json'), "r")
    with aioresponses() as m:
        m.get("%s/v2/%s/tags/list" % (global_data["registry"], global_data["repository"]), status=200, body=f.read())
        session = aiohttp.ClientSession()
        resp = await client.retrieve_tags_for_repository(global_data["repository"], session)
        expect = set([global_data["tag"]])
        assert check_equal(resp, expect)
        await session.close()


@pytest.mark.asyncio
async def test_retrieve_size_for_tag_and_repository(global_data, client):
    f = open(get_resource('response_manifest_v2.json'), "r")
    with aioresponses() as m:
        m.get("%s/v2/%s/manifests/%s" % (global_data["registry"], global_data["repository"], global_data["tag"]), status=200, body=f.read())
        session = aiohttp.ClientSession()
        resp = await client.retrieve_size_for_tag_and_repository(global_data["repository"], global_data["tag"], session)
        expect = {'repo': 'test/alpine', 'tag': 'latest', 'sizes': 
                    {'manifest': 7023, 
                    'sha256:e692418e4cbaf90ca69d05a66403747baa33ee08806650b51fab815ad7fc331f': 32654, 
                    'sha256:3c3a4604a545cdc127456d94e421cd355bca5b528f4a9c1905b15da2eb4a4c6b': 16724, 
                    'sha256:ec4b8955958665577945c89419d1af06b5f7636b4ac3da7f12184802ad867736': 73109}}
        assert check_equal(resp, expect)
        await session.close()

@pytest.mark.asyncio
async def test_retrieve_manifest_v1_for_tag_and_repository(global_data, client):
    f = open(get_resource('response_manifest_v1.json'), "r")
    with aioresponses() as m:
        m.get("%s/v2/%s/manifests/%s" % (global_data["registry"], global_data["repository"], global_data["tag"]), status=200, body=f.read())
        session = aiohttp.ClientSession()
        resp = await client.retrieve_manifest_v1_for_tag_and_repository(global_data["repository"], global_data["tag"], session)
        response = json.loads(resp)
        assert response["architecture"] == "amd64"
        await session.close()

def check_equal(s1, s2):
    return len(s1) == len(s2) and sorted(s1) == sorted(s2)

def get_resource(filename):
    return os.path.join(os.path.dirname(__file__), 'resources', filename)