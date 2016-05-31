"""Prototype of a Wunderlist terminal client."""
import os
import urwid
import wunderpy2
import yaml


def show_or_exit(key):
    if key in ('q', 'Q'):
        raise urwid.ExitMainLoop()


if __name__ == "__main__":
    with open(os.path.expanduser('~/.wutrc')) as f:
        config = yaml.load(f)
    api = wunderpy2.WunderApi()
    client = api.get_client(config['token'], config['client_id'])
    list_id, = [l['id'] for l in client.get_lists()
                if l['title'] == config['which_list']]
    tasks = client.get_tasks(list_id)
    buttons = [urwid.AttrMap(
        urwid.CheckBox(task['title']),
        None,
        focus_map='reversed'
    ) for task in tasks]
    pile = urwid.Pile(buttons)
    listbox = urwid.ListBox([pile])
    loop = urwid.MainLoop(urwid.Padding(listbox, left=2, right=2),
                          [('reversed', 'black', 'white', 'standout')],
                          unhandled_input=show_or_exit)
    loop.run()
