"""Prototype of a Wunderlist terminal client."""
import itertools
import os
import urwid
import yaml
from wut.api import WunderListAPI


def show_or_exit(key):
    if key in ('q', 'Q'):
        raise urwid.ExitMainLoop()


class TaskPile(urwid.Pile):
    def __init__(self, client, which_list, focus_item=None,
                 completion_timeout=0.8):
        super().__init__([], focus_item)
        self.client = client
        self.which_list = which_list
        self.completion_timeout = completion_timeout
        self.main_loop = None
        self.refresh()

    def refresh(self):
        list_descr, = [l for l in client.lists()
                       if l['title'] == self.which_list]
        tasks = self.client.tasks(list_descr)[::-1]
        buttons = [urwid.AttrMap(
            urwid.CheckBox(task['title']),
            None,
            focus_map='reversed'
        ) for task in tasks]
        self.contents.clear()
        self.contents.extend(list(zip(buttons,
                                      itertools.repeat(('pack', None)))))
        if len(self.contents):
            self.focus_position = 0

    def keypress(self, size, key):
        if key.lower() == 'r':
            self.refresh()
        else:
            return super().keypress(size, key)


if __name__ == "__main__":
    with open(os.path.expanduser('~/.wutrc')) as f:
        config = yaml.load(f)
    client = WunderListAPI(config['client_id'], config['token'])
    pile = TaskPile(client, config['which_list'])
    listbox = urwid.ListBox([pile])
    loop = urwid.MainLoop(urwid.Padding(listbox, left=2, right=2),
                          [('reversed', 'black', 'white', 'standout')],
                          unhandled_input=show_or_exit)
    pile.main_loop = loop
    loop.run()
