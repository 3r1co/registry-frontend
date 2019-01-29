from api import api
import pytest
import main
import os
from unittest import mock

@pytest.fixture(scope = 'module')
def app():
    main.app.blueprint(api)
    main.app.reg = mock.MagicMock()
    main.app.persistent = False
    return main.app


def test_status_200(app):
    _, response = app.test_client.get('/api/status')
    assert response.status == 200
    assert response.body.decode("utf-8") == "true"


def test_manifest(app):
    f = open(get_resource('response_manifest_v1.json'), "r")
    app.manifests = dict({'test/alpine/latest': f.read() })
    _, response = app.test_client.get('/api/manifest/test/alpine/latest')
    assert response.status == 200

def test_repositories(app):
    app.db = {'test/alpine': {'tags': ["latest"], 'size': 1}}
    _, response = app.test_client.get('/api/repositories')
    assert response.status == 200

def get_resource(filename):
    return os.path.join(os.path.dirname(__file__), 'resources', filename)