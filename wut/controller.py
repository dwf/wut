from functools import partial
import urwid


class SubController(urwid.WidgetWrap):
    """Base class for sub-controllers concerned with a single function.

    These sit between the Controller (a.k.a. urwid MainLoop) and
    the View in the widget hierarchy, so they can capture keypresses.

    """
    def __init__(self, root, view):
        self.root = root
        self.view = view
        if hasattr(self, 'handler'):
            self.view.register_callback(self.handler)
        super().__init__(view)

    @property
    def model(self):
        return self.root.model

    def set_alarm_in(self, *args, **kwargs):
        return self.root.set_alarm_in(*args, **kwargs)

    def remove_alarm(self, *args, **kwargs):
        return self.root.remove_alarm(*args, **kwargs)


class ListsController(SubController):
    """Controller that handles the list selection dialog."""
    def refresh(self):
        lists = self.model.lists()
        self.view.populate(lists)

    def handler(self, widget, user_data):
        self.root.select_list(user_data)


class TasksController(SubController):
    """Controller that handles the tasks/subtasks selection dialog."""
    completion_timeout = 0.8

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.show_completed = False

    def keypress(self, size, key):
        if key == 'backspace' or key == 'left':
            self.abort()
        elif key.lower() == 'r':
            return self.refresh()
        elif key.lower() == 'n':
            self.root.display_create_dialog()
        elif key.lower() == 'e':
            self.root.display_edit_dialog()
        elif key.lower() == 's' and self.active_record['type'] == 'list':
            self.active_record = self.view.focus_entity
            self.refresh()
        elif key.lower() == 'c':
            self.show_completed = not self.show_completed
            self.refresh()
        else:
            return super().keypress(size, key)

    def abort(self):
        if self.active_record['type'] == 'list':
            self.root.display_list_selection()
        else:
            assert self.active_record['type'] == 'task'
            list_id = self.active_record['list_id']
            self.active_record = self.model.list(list_id)

    @property
    def active_record(self):
        return getattr(self, '_active_record', {'id': None})

    @active_record.setter
    def active_record(self, new):
        old, self._active_record = self.active_record, new
        # Could maintain per-list foci...
        if new['id'] == old['id']:
            self.refresh(reset_focus=False)
        else:
            self.refresh(reset_focus=True)

    def refresh(self, reset_focus=False):
        if self.active_record['type'] == 'list':
            f = self.model.tasks
        else:
            assert self.active_record['type'] == 'task'
            f = self.model.subtasks
        entities = f(self.active_record, completed=self.show_completed)
        self.view.populate(entities, reset_focus=reset_focus)

    def create_entity(self, **kwargs):
        if self.active_record['type'] == 'list':
            endpoint = self.model.create_task
        else:
            assert self.active_record['type'] == 'task'
            endpoint = self.model.create_subtask
        return endpoint(self.active_record['id'], **kwargs)

    def update_entity(self, entity, **kwargs):
        if self.active_record['type'] == 'list':
            return self.model.update_task(entity, **kwargs)
        else:
            assert self.active_record['type'] == 'task'
            return self.model.update_subtask(entity, **kwargs)

    def handler(self, widget, new_state, task):
        alarm = getattr(widget, 'alarm', None)
        if alarm:
            self.remove_alarm(alarm)
        else:
            widget.alarm = self.set_alarm_in(
                self.completion_timeout,
                partial(self._mark_completed_callback, new_state),
                user_data=(task, widget)
            )

    def _mark_completed_callback(self, new_state, _, user_data):
        task, widget = user_data
        self.model.update_task(task, completed=new_state)
        self.view.remove_task_element(widget)

    def add_new_element(self, entity):
        if entity['completed'] == self.show_completed:
            self.view.insert_new(entity)

    def update_element(self, index, entity):
        self.view.replace_task_element(index, entity)

    def display_subtasks(self, task):
        self.active_record = task
        self.refresh()


class EditTaskController(SubController):
    """Controller that handles the tasks/subtasks edit dialog."""
    def keypress(self, size, key):
        if key == 'esc':
            self.abort()
        else:
            super().keypress(size, key)

    def abort(self):
        self.root.display_task_list()

    def handler(self, entity, index, title):
        self.root.display_task_list()
        if len(title) == 0:
            return
        tasks_controller = self.root.tasks_controller
        entity = tasks_controller.update_entity(entity, title=title)
        tasks_controller.update_element(index, entity)
        self.view.clear()

    def refresh(self):
        self.view.populate()


class CreateController(EditTaskController):
    """Controller that handles the task/subtask creation dialog."""
    def handler(self, title):
        self.root.display_task_list()
        if len(title) == 0:
            return
        tasks_controller = self.root.tasks_controller
        entity = tasks_controller.create_entity(title=title, completed=False)
        tasks_controller.add_new_element(entity)
        self.view.clear()


class Controller(urwid.MainLoop):
    """Root controller for the application.

    Subclass of urwid's MainLoop, so it can handle the topmost widget
    (aliased as ``active_controller``), adding/removing alarms, unhandled
    keyboard input, etc.

    """
    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.tasks_controller = TasksController(self, view.tasks_view)
        self.lists_controller = ListsController(self, view.lists_view)
        self.create_controller = CreateController(self, view.create_view)
        self.edit_task_controller = EditTaskController(self,
                                                       view.edit_task_view)
        super().__init__(self.lists_controller,
                         view.palette,
                         unhandled_input=self.keypress)

    def keypress(self, key):
        if key.lower() == 'q':
            raise urwid.ExitMainLoop()

    @property
    def active_controller(self):
        return self.widget

    @active_controller.setter
    def active_controller(self, value):
        self.widget = value

    def run(self, *args, **kwargs):
        self.active_controller.refresh()
        super().run(*args, **kwargs)

    def select_list(self, list_descr):
        self.tasks_controller.active_record = list_descr
        self.display_task_list()

    def display_list_selection(self):
        self.active_controller = self.lists_controller

    def display_task_list(self):
        self.active_controller = self.tasks_controller

    def display_create_dialog(self):
        self.active_controller = self.create_controller

    def display_edit_dialog(self):
        self.active_controller = self.edit_task_controller
        self.active_controller.refresh()
