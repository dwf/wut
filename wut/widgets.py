from __future__ import print_function
from abc import ABCMeta
from collections.abc import MutableSequence
import urwid

from .api import MAX_TITLE_LENGTH


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


class ABCMetaWidget(urwid.WidgetMeta, ABCMeta):
    pass


class EntityPile(MutableSequence, urwid.Pile, metaclass=ABCMetaWidget):
    style = ('pack', None)

    def __init__(self):
        super().__init__([])
        self.entities = []

    def construct_element_for(self, value):
        return (self.build_widget(value), self.style)

    def insert(self, index, value):
        self.contents.insert(index, self.construct_element_for(value))
        self.entities.insert(index, value)

    def __getitem__(self, index):
        return self.entities[index]

    def __setitem__(self, index, value):
        self.entities[index] = value
        self.contents[index] = self.construct_element_for(value)

    def __delitem__(self, index):
        del self.entities[index]
        del self.contents[index]

    def __len__(self):
        assert len(self.entities) == len(self.contents)
        return len(self.entities)


class CallbackEntityPile(EntityPile):
    def __init__(self, callback=None):
        super().__init__()
        self.callback = callback


class TaskPile(CallbackEntityPile):
    def build_widget(self, task):
        checkbox = urwid.CheckBox(task['title'],
                                  on_state_change=self.callback,
                                  user_data=task)
        return urwid.AttrMap(checkbox, None, focus_map='reversed')


class ListPile(CallbackEntityPile):
    def build_widget(self, list_):
        button = urwid.Button(list_['title'], on_press=self.callback,
                              user_data=list_)
        return urwid.AttrMap(button, None, focus_map='reversed')
