from __future__ import print_function
from contextlib import contextmanager
from functools import partial
import urwid
from .widgets import TitleEdit, TaskPile, ListPile


@contextmanager
def preserve_focus(widget, delta=0, reset=False):
    try:
        old_focus = widget.focus_position
    except IndexError:
        old_focus = None
        reset = True
    yield
    if reset:
        try:
            widget.focus_position = 0
        except IndexError:
            pass
    elif old_focus is not None:
        try:
            widget.focus_position = old_focus + delta
        except IndexError:
            # This might fail when e.g. switching between
            # completed/not completed view.
            pass


class SelectorView(urwid.WidgetWrap):
    def __init__(self):
        self._pile = self.pile_class()
        super().__init__(urwid.Padding(urwid.ListBox([self._pile]),
                                       left=2, right=2))

    @property
    def focus(self):
        return self._pile.focus

    @property
    def focus_position(self):
        return self._pile.focus_position

    def register_callback(self, callback):
        self._pile.callback = callback


class TasksView(SelectorView):
    pile_class = TaskPile

    def populate(self, tasks, reset_focus=False):
        with preserve_focus(self._pile, reset=reset_focus):
            self._pile.clear()
            self._pile.extend(tasks)

    @property
    def focus_entity(self):
        return self._pile[self._pile.focus_position]

    def insert_new(self, task, index=0):
        with preserve_focus(self._pile, delta=1):
            self._pile.insert(0, task)

    def remove_task_element(self, element):
        index, = [idx for idx, (elem, _) in enumerate(self._pile.contents)
                  if elem == element or elem.base_widget == element]
        del self._pile[index]

    def replace_task_element(self, index, task):
        self._pile[index] = task


class ListsView(SelectorView):
    pile_class = ListPile

    def populate(self, lists):
        with preserve_focus(self._pile):
            self._pile.clear()
            self._pile.extend(lists)


class EditView(urwid.WidgetWrap):
    def __init__(self, tasks_view, caption, callback=None):
        self._edit_widget = TitleEdit(callback)
        self.tasks_view = tasks_view
        super().__init__(urwid.Overlay(
            urwid.LineBox(
                urwid.Padding(urwid.ListBox([
                    urwid.Text(caption),
                    urwid.Divider(),
                    urwid.LineBox(self._edit_widget)
                ]), left=3, right=3)
            ),
            tasks_view, width=('relative', 80),
            height=('relative', 30), align='center', valign='middle',
            min_height=8))

    def register_callback(self, callback):
        self._edit_widget.enter_callback = callback

    def clear(self):
        self._edit_widget.set_edit_text('')


class EditExistingTaskView(EditView):
    def populate(self):
        task = self.tasks_view.focus_entity
        position = self.tasks_view.focus_position
        self._edit_widget.enter_callback = partial(self._base_callback,
                                                   task, position)
        self._edit_widget.set_edit_text(task['title'])
        self._edit_widget.set_edit_pos(self._edit_widget.max_length)

    def register_callback(self, callback):
        self._base_callback = callback


class View:
    palette = [('reversed', 'black', 'white', 'standout')]

    def __init__(self):
        self.lists_view = ListsView()
        self.tasks_view = TasksView()
        self.create_view = EditView(self.tasks_view,
                                    'Title for new task:')
        self.edit_task_view = EditExistingTaskView(self.tasks_view,
                                                   'New title for task:')
