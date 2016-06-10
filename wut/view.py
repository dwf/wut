import itertools
import urwid


class View:
    palette = [('reversed', 'black', 'white', 'standout')]

    def __init__(self, model):
        self.model = model
        self._tasks_pile = urwid.Pile([])
        self.tasks_view = urwid.Padding(urwid.ListBox([self._tasks_pile]),
                                        left=2, right=2)
        self._lists_pile = urwid.Pile([])
        self.lists_view = urwid.Padding(urwid.ListBox([self._lists_pile]),
                                        left=2, right=2)

    def fill_tasks_view(self, list_descr, change_handler, reset_focus=False):
        try:
            old_focus = self._tasks_pile.focus_position
        except IndexError:
            old_focus = None
            reset_focus = True
        tasks = self.model.tasks(list_descr)[::-1]
        buttons = [urwid.AttrMap(
            urwid.CheckBox(task['title'], on_state_change=change_handler,
                           user_data=task),
            None,
            focus_map='reversed'
        ) for task in tasks]
        contents = self._tasks_pile.contents
        contents.clear()
        contents.extend(list(zip(buttons, itertools.repeat(('pack', None)))))
        try:
            self._tasks_pile.focus_position = 0 if reset_focus else old_focus
        except IndexError:
            pass

    def fill_lists_view(self, selection_handler):
        try:
            old_focus = self._tasks_pile.focus_position
        except IndexError:
            old_focus = None
            reset_focus = True
        lists = self.model.lists()
        buttons = [urwid.AttrMap(
            urwid.Button(list_['title'],
                         on_press=selection_handler,
                         user_data=list_),
            None,
            focus_map='reversed'
        ) for list_ in lists]
        contents = self._lists_pile.contents
        contents.clear()
        contents.extend(list(zip(buttons, itertools.repeat(('pack', None)))))
        self._lists_pile.focus_position = 0 if reset_focus else old_focus

    def remove_task_element(self, element):
        elems = [e for e in self._tasks_pile.contents
                 if e[0].base_widget == element]
        assert len(elems) == 1
        self._tasks_pile.contents.remove(elems[0])
