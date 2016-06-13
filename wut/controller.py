import urwid


class SubController(urwid.WidgetWrap):
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
    def refresh(self):
        lists = self.model.lists()
        self.view.populate(lists)

    def handler(self, widget, user_data):
        self.root.select_list(user_data)


class TasksController(SubController):
    completion_timeout = 0.8

    def keypress(self, size, key):
        if key == 'backspace' or key == 'left':
            self.abort()
        elif key.lower() == 'r':
            return self.refresh()
        elif key.lower() == 'n':
            self.root.display_create_dialog()
        elif key.lower() == 'e':
            self.root.display_edit_dialog()
        else:
            return super().keypress(size, key)

    def abort(self):
        self.root.display_list_selection()

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
        tasks = self.model.tasks(self.active_record)
        self.view.populate(tasks, reset_focus=reset_focus)

    def mark_completed(self, _, user_data):
        task, widget = user_data
        self.model.update_task(task, completed=True)
        self.view.remove_task_element(widget)

    def handler(self, widget, new_state, task):
        alarm = getattr(widget, 'alarm', None)
        if alarm:
            self.remove_alarm(alarm)
        else:
            widget.alarm = self.set_alarm_in(
                self.completion_timeout, self.mark_completed,
                user_data=(task, widget)
            )

    def add_new_task(self, task):
        self.view.insert_new(task)

    def update_element(self, index, task):
        self.view.replace_task_element(index, task)


class EditTaskController(SubController):
    def keypress(self, size, key):
        if key == 'esc':
            self.abort()
        else:
            super().keypress(size, key)

    def abort(self):
        self.root.display_task_list()

    def handler(self, task, index, task_title):
        self.root.display_task_list()
        if len(task_title) == 0:
            return
        task = self.model.update_task(task, title=task_title)
        self.root.tasks_controller.update_element(index, task)
        self.view.clear()

    def refresh(self):
        self.view.populate()


class CreateController(EditTaskController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.view.register_callback(self.handler)

    def handler(self, title):
        active_record = self.root.tasks_controller.active_record
        self.root.display_task_list()
        if len(title) == 0:
            return
        task = self.model.create_task(active_record, title=title)
        self.root.tasks_controller.add_new_task(task)
        self.view.clear()


class Controller(urwid.MainLoop):
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
