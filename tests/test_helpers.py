import random
import string
from types import SimpleNamespace

import redis
from mock import Mock

from helpers import constants, helper


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
    db.get = Mock(return_value=None)
    app.db = db
    assert helper.is_redis_available(app) == True
    db.get = Mock(side_effect=redis.exceptions.ConnectionError)
    assert helper.is_redis_available(app) == False
