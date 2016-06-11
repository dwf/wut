import os
import yaml
from .api import WunderListAPI
from .controller import Controller
from .view import View


def main():
    config_filename = os.environ.get('WUT_CONFIG_PATH',
                                     os.path.expanduser('~/.wutrc'))
    with open(config_filename) as f:
        config = yaml.load(f)
    model = WunderListAPI(config['client_id'], config['token'])
    view = View(model)
    controller = Controller(model, view)
    controller.run()
