import redis
import logging

def truncate_middle(s, n):
    if len(s) <= n:
        # string is already short-enough
        return "{:^30}".format(s)
    # half of the size, minus the 3 .'s
    n_2 = int(n) / 2 - 3
    # whatever's left
    n_1 = n - n_2 - 3
    return '{0}...{1}'.format(s[:int(n_1)], s[int(-n_2):])

def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)

def is_redis_available(app):
    try:
        app.db.get('*')  # getting None returns None or throws an exception
    except (redis.exceptions.ConnectionError, redis.exceptions.BusyLoadingError):
        logging.error("Cannot connect to redis, please check connection.")
        return False
    return True