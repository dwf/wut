from collections.abc import Mapping
from functools import wraps
from hammock import Hammock
import requests

TASK_CREATE_PROPERTIES = ('title', 'assignee_id', 'completed',
                          'recurrence_type', 'recurrence_count', 'due_date',
                          'starred')

TASK_UPDATE_PROPERTIES = TASK_CREATE_PROPERTIES + ('remove',)

MAX_TITLE_LENGTH = 255


def raise_for_status(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        raw = f(*args, **kwargs)
        raw.raise_for_status()
        return raw
    return wrapped


def return_json(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        raw = kwargs.pop('raw', False)
        returned = f(*args, **kwargs)
        returned.raise_for_status()
        assert isinstance(returned, requests.Response)
        if raw:
            return returned
        else:
            return returned.json()
    return wrapped


def extract(key):
    def wrapper_builder(f):
        @wraps(f)
        def wrapped(self, arg, *args, **kwargs):
            if isinstance(arg, Mapping):
                return f(self, arg[key], *args, **kwargs)
            else:
                return f(arg, *args, **kwargs)
        return wrapped
    return wrapper_builder


def allowed_keywords(keywords):
    keywords = frozenset(keywords)

    def wrapper_builder(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            unknown = kwargs.keys() - keywords
            if len(unknown) > 0:
                raise KeyError(', '.join(sorted(unknown)))
            return f(*args, **kwargs)
        return wrapped
    return wrapper_builder


class WunderListAPI(object):
    API_VERSION = 1
    API_BASE_URL = 'http://a.wunderlist.com/api'

    def __init__(self, client_id, access_token, api_base_url=API_BASE_URL,
                 api_version=API_VERSION):
        self.client_id = client_id
        self.access_token = access_token
        self.client = Hammock('/'.join([api_base_url,
                                        'v{}'.format(api_version)]))

    @property
    def headers(self):
        return {'X-Client-ID': self.client_id,
                'X-Access-Token': self.access_token}

    @extract('id')
    @return_json
    def tasks(self, list_id, completed=False):
        params = {'list_id': list_id, 'completed': completed}
        return self.client.tasks().GET(params=params, headers=self.headers)

    @return_json
    def lists(self):
        return self.client.lists().GET(headers=self.headers)

    @return_json
    @allowed_keywords(TASK_CREATE_PROPERTIES)
    @extract('id')
    def create_task(self, list_id, **kwargs):
        if 'title' not in kwargs:  # TODO: kw-only argument (vim sucks)
            raise KeyError('title is required')
        kwargs['list_id'] = list_id
        return self.client.tasks().POST(json=kwargs, headers=self.headers)

    @return_json
    @allowed_keywords(TASK_UPDATE_PROPERTIES)
    def update_task(self, task, **kwargs):
        kwargs['revision'] = int(task['revision'])
        return self.client.tasks(task['id']).PATCH(json=kwargs,
                                                   headers=self.headers)

    @raise_for_status
    def delete_task(self, task):
        params = {'revision': task['revision']}
        return self.client.tasks(task['id']).DELETE(params=params,
                                                    headers=self.headers)
