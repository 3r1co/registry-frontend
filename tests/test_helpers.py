import random
import string
from types import SimpleNamespace
from unittest import mock

import pytest
import redis

import registryclient
from helpers import constants, helper, init_functions


def test_repo_prefix():
    assert constants.REPO_PREFIX == "repo_"


def test_manifest_prefix():
    assert constants.MANIFEST_PREFIX == "manifest_"


def test_truncate_middle():
    # abcd = 4, maxlength = 30 -> 30-4 = 26 / 2 = 13
    assert " " * 13 + "abcd" + " " * 13 == helper.truncate_middle("abcd", 30)
    str = ''.join(random.choice(string.ascii_letters) for x in range(40))
    assert str[0:15] + "..." + str[-12:] == helper.truncate_middle(str, 30)


def test_size_of_fmt():
    assert "1.0KiB" == helper.sizeof_fmt(1024)
    assert "1.0MiB" == helper.sizeof_fmt(1024 ** 2)
    assert "2.0MiB" == helper.sizeof_fmt(2 * 1024 ** 2)
    assert "1.0GiB" == helper.sizeof_fmt(1024 ** 3)
    assert "1.0TiB" == helper.sizeof_fmt(1024 ** 4)
    assert "1.0PiB" == helper.sizeof_fmt(1024 ** 5)
    assert "1.0EiB" == helper.sizeof_fmt(1024 ** 6)
    assert "1.0ZiB" == helper.sizeof_fmt(1024 ** 7)
    assert "1.0YiB" == helper.sizeof_fmt(1024 ** 8)


def test_redis_available():
    app = SimpleNamespace()
    db = SimpleNamespace()
    db.get = mock.Mock(return_value=None)
    app.db = db
    assert helper.is_redis_available(app) == True
    db.get = mock.Mock(side_effect=redis.exceptions.ConnectionError)
    assert helper.is_redis_available(app) == False

def test_startup_arguments():
    args = init_functions.init_args(["--registry", "registry",
                              "--username", "aaa",
                              "--password", "bbb",
                              "--listen", "0.0.0.0",
                              "--port", "8888",
                              "--redis", "redis",
                              "--cacert", "ca.crt",
                              "--cli","--debug"
                              ])
    assert args.registry == "registry"
    assert args.username == "aaa"
    assert args.password == "bbb"
    assert args.listen == "0.0.0.0"
    assert args.redis == "redis"
    assert args.cacert == "ca.crt"
    assert args.cli == True
    assert args.debug == True


def test_init_db_no_persistence():
    app = SimpleNamespace()
    args = SimpleNamespace()
    args.redis = None
    init_functions.init_db(app, args)
    assert app.db == dict()
    assert app.manifests == dict()
    assert app.persistent == False


@mock.patch('helpers.init_functions.Client')
def test_init_db_persistence(mock_rejson):
    app = SimpleNamespace()
    args = SimpleNamespace()
    args.redis = "localhost"
    init_functions.init_db(app, args)
    assert app.persistent == True


@mock.patch('helpers.init_functions.Client')
@mock.patch('helpers.init_functions.is_redis_available')
def test_init_db_persistence_no_connection(mock_is_available, mock_rejson):
    app = SimpleNamespace()
    args = SimpleNamespace()
    args.redis = "localhost"
    mock_is_available.return_value = False
    try:
        init_functions.init_db(app, args)
        pytest.fail("Exception should have been thrown")
    except Exception:
        pass


def test_init_app():
    app = mock.Mock()
    app.static = mock.MagicMock()
    args = SimpleNamespace()
    args.registry = "http://localhost:5000"
    args.username = "username"
    args.password = "password"
    args.cli = False
    args.cacert = None
    init_functions.init_app(app, args)
    assert app.static.call_count == 3
    assert isinstance(app.reg, registryclient.RegistryClient)