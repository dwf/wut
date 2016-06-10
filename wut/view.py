from __future__ import print_function
import itertools
import urwid
from api import MAX_TITLE_LENGTH


class MaxLengthMixin:
    def set_edit_text(self, value):
        if len(value) >= self.max_length:
            print('\a', end=None)
        else:
            super().set_edit_text(value)


class CallbackEdit(urwid.Edit):
    def __init__(self, enter_callback, *args, **kwargs):
        self.enter_callback = enter_callback
        super().__init__(*args, **kwargs)

    def keypress(self, size, key):
        if key == 'enter':
            self.enter_callback(self.edit_text)
        else:
            super().keypress(size, key)


class TitleEdit(MaxLengthMixin, CallbackEdit):
    def __init__(self, *args, **kwargs):
        self.max_length = MAX_TITLE_LENGTH
        super().__init__(*args, **kwargs)


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
        self._new_task_edit = TitleEdit(None)
        self.new_task_view = urwid.Overlay(
            urwid.LineBox(
                urwid.Padding(urwid.ListBox([
                    urwid.Text('Title for new task:'),
                    urwid.Divider(),
                    urwid.LineBox(self._new_task_edit)
                ]), left=3, right=3)
            ),
            self.tasks_view, width=('relative', 80),
            height=('relative', 30), align='center', valign='middle',
            min_height=8)

    @property
    def new_task_callback(self):
        return self._new_task_edit.enter_callback

    @new_task_callback.setter
    def new_task_callback(self, value):
        self._new_task_edit.enter_callback = value

    def clear_new_task_text(self):
        self._new_task_edit.set_edit_text('')

    def fill_tasks_view(self, list_descr, change_handler, reset_focus=False):
        try:
            old_focus = self._tasks_pile.focus_position
        except IndexError:
            old_focus = None
            reset_focus = True
        tasks = self.model.tasks(list_descr)[::-1]
        buttons = [self._create_task_checkbox_entry(task, change_handler)
                   for task in tasks]
        contents = self._tasks_pile.contents
        contents.clear()
        contents.extend(list(zip(buttons, itertools.repeat(('pack', None)))))
        try:
            self._tasks_pile.focus_position = 0 if reset_focus else old_focus
        except IndexError:
            pass

    @staticmethod
    def _create_task_checkbox_entry(task, change_handler):
        return urwid.AttrMap(
            urwid.CheckBox(task['title'], on_state_change=change_handler,
                           user_data=task),
            None,
            focus_map='reversed'
        )

    def insert_new_task_entry(self, task, change_handler):
        try:
            old_focus = self._tasks_pile.focus_position
        except IndexError:
            old_focus = None

        new_entry = (self._create_task_checkbox_entry(task, change_handler),
                     ('pack', None))
        self._tasks_pile.contents.insert(0, new_entry)

        if old_focus is not None:
            self._tasks_pile.focus_position = old_focus + 1

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
