from collections.abc import Mapping
from functools import wraps
from itertools import chain
from hammock import Hammock


SUBTASK_CREATE_PROPERTIES = ('title', 'completed')
TASK_CREATE_PROPERTIES = SUBTASK_CREATE_PROPERTIES + (
    'assignee_id', 'recurrence_type', 'recurrence_count',
    'due_date', 'starred'
)

SUBTASK_UPDATE_PROPERTIES = SUBTASK_CREATE_PROPERTIES
TASK_UPDATE_PROPERTIES = TASK_CREATE_PROPERTIES + ('remove',)

MAX_TITLE_LENGTH = 255


def raise_for_status(f):
    """Raise exception if returned ``request.Response`` is bogus."""
    @wraps(f)
    def wrapped(*args, **kwargs):
        raw = f(*args, **kwargs)
        raw.raise_for_status()
        return raw
    return wrapped


def reorder(entities, positions):
    """From the Wunderlist API docs:

    To determine the order of resources the following convention shall be
    followed:

     * Existing resources follow the order of their ids in the
       "values" array
     * Ids in the "values" array which do not refer to an
       existing resource are simply ignored
     * Existing resources with ids that do not appear in the values array
       appear at the end ordered by id ASC and then local id ASC.

    I have no idea what "local id" means and I would have thought ids were
    unique.

    """
    entities = {e['id']: e for e in entities}
    not_appearing = sorted(entities.keys() - set(positions), reverse=True)
    ordered = list(chain((entities[p] for p in not_appearing),
                         (entities[p] for p in positions if p in entities)))
    return ordered


def extract(key):
    """Automatically unwrap dict-likes containing a key of interest."""
    def wrapper_builder(f):
        @wraps(f)
        def wrapped(self, arg, *args, **kwargs):
            if isinstance(arg, Mapping):
                return f(self, arg[key], *args, **kwargs)
            else:
                return f(self, arg, *args, **kwargs)
        return wrapped
    return wrapper_builder


def allowed_keywords(keywords):
    """Raise an error if a key in kwargs falls outside of an allowed set."""
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
    """Wunderlist API wrapper. Does very little input validation."""
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
    def tasks(self, list_id, completed=False, ordered=True):
        params = {'list_id': list_id, 'completed': completed}
        tasks = (self.client.tasks().GET(params=params,
                                         headers=self.headers).json())
        if ordered:
            del params['completed']
            # Why is this a list?
            positions, = (self.client.task_positions()
                          .GET(params=params, headers=self.headers).json())
            tasks = reorder(tasks, positions['values'])
        return tasks

    @extract('id')
    def task(self, id_):
        return self.client.tasks(id_).GET(headers=self.headers).json()

    @extract('id')
    def subtasks(self, task_id, completed=False, ordered=True):
        # You can also grab all(?) subtasks based on a list_id, but ignore
        # that for now.
        params = {'task_id': task_id, 'completed': completed}
        subtasks = self.client.subtasks().GET(params=params,
                                              headers=self.headers).json()
        if ordered:
            del params['completed']
            # Why is this a list?
            positions, = (self.client.subtask_positions()
                          .GET(params=params, headers=self.headers).json())
            subtasks = reorder(subtasks, positions['values'])
        return subtasks

    def lists(self, ordered=True, inbox_first=True):
        lists = self.client.lists().GET(headers=self.headers).json()
        if ordered:
            # Why is this a list?
            positions, = (self.client.list_positions()
                          .GET(headers=self.headers).json())
            lists = reorder(lists, positions['values'])
        inbox, = [l for l in lists if l['list_type'] == 'inbox']
        if inbox_first:
            del lists[lists.index(inbox)]
            lists.insert(0, inbox)
        return lists

    @extract('id')
    def list(self, id_):
        return self.client.lists(id_).GET(headers=self.headers).json()

    @allowed_keywords(TASK_CREATE_PROPERTIES)
    @extract('id')
    def create_task(self, list_id, **kwargs):
        return self._create(self.client.tasks, 'list_id', list_id, **kwargs)

    @allowed_keywords(SUBTASK_CREATE_PROPERTIES)
    @extract('id')
    def create_subtask(self, task_id, **kwargs):
        return self._create(self.client.subtasks, 'task_id', task_id, **kwargs)

    def _create(self, endpoint, container_key, container_id, **kwargs):
        if 'title' not in kwargs:  # TODO: kw-only argument (vim sucks)
            raise KeyError('title is required')
        kwargs[container_key] = container_id
        return endpoint.POST(json=kwargs, headers=self.headers).json()

    @allowed_keywords(TASK_UPDATE_PROPERTIES)
    def update_task(self, task, **kwargs):
        return self._update(self.client.tasks, task, **kwargs)

    @allowed_keywords(SUBTASK_UPDATE_PROPERTIES)
    def update_subtask(self, subtask, **kwargs):
        return self._update(self.client.subtasks, subtask, **kwargs)

    def _update(self, endpoint, entity, **kwargs):
        kwargs['revision'] = int(entity['revision'])
        return (endpoint(entity['id'])
                .PATCH(json=kwargs, headers=self.headers).json())

    @raise_for_status
    def delete_task(self, task):
        params = {'revision': task['revision']}
        return (self.client.tasks(task['id'])
                .DELETE(params=params, headers=self.headers).json())
