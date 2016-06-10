"""Prototype of a Wunderlist terminal client."""
import itertools
import os
import urwid
import yaml
from wut.api import WunderListAPI
from wut.controller import Controller
from wut.view import View


if __name__ == "__main__":
    with open(os.path.expanduser('~/.wutrc')) as f:
        config = yaml.load(f)
    model = WunderListAPI(config['client_id'], config['token'])
    view = View(model)
    controller = Controller(model, view)
    controller.run()
