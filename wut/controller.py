import urwid


class SubController(urwid.WidgetWrap):
    def __init__(self, root, view):
        self.root = root
        super().__init__(getattr(view, self.VIEW_WIDGET))

    @property
    def view(self):
        return self.root.view

    @property
    def model(self):
        return self.root.model

    def set_alarm_in(self, *args, **kwargs):
        return self.root.set_alarm_in(*args, **kwargs)

    def remove_alarm(self, *args, **kwargs):
        return self.root.remove_alarm(*args, **kwargs)


class ListSelectionController(SubController):
    VIEW_WIDGET = 'lists_view'

    def refresh(self):
        self.view.fill_lists_view(self.selection_handler)

    def selection_handler(self, widget, user_data):
        self.root.select_list(user_data)


class TasksModeController(SubController):
    VIEW_WIDGET = 'tasks_view'
    completion_timeout = 0.8

    def keypress(self, size, key):
        if key == 'backspace':
            self.root.display_list_selection()
        elif key.lower() == 'r':
            return self.refresh()
        elif key.lower() == 'n':
            self.root.create_new_task()
        else:
            return super().keypress(size, key)

    @property
    def active_list(self):
        return getattr(self, '_active_list', {'id': None})

    @active_list.setter
    def active_list(self, new):
        old, self._active_list = self.active_list, new
        # Could maintain per-list foci...
        if new['id'] == old['id']:
            self.refresh(reset_focus=False)
        else:
            self.refresh(reset_focus=True)

    def refresh(self, reset_focus=False):
        self.view.fill_tasks_view(self.active_list,
                                  self.task_widget_change_handler,
                                  reset_focus=reset_focus)

    def mark_completed(self, _, user_data):
        task, widget = user_data
        self.model.update_task(task, completed=True)
        self.view.remove_task_element(widget)

    def task_widget_change_handler(self, widget, new_state, task):
        alarm = getattr(widget, 'alarm', None)
        if alarm:
            self.remove_alarm(alarm)
        else:
            widget.alarm = self.set_alarm_in(
                self.completion_timeout, self.mark_completed,
                user_data=(task, widget)
            )

    def add_new_task(self, task):
        self.view.insert_new_task_entry(task, self.task_widget_change_handler)


class NewTaskController(SubController):
    VIEW_WIDGET = 'new_task_view'

    def keypress(self, size, key):
        if key == 'esc':
            self.root.display_task_list()
        else:
            super().keypress(size, key)

    def handler(self, new_task_title):
        self.root.display_task_list()
        active_list = self.root.tasks_controller.active_list
        task = self.model.create_task(active_list, title=new_task_title)
        self.root.tasks_controller.add_new_task(task)
        self.view.clear_new_task_text()


class Controller(urwid.MainLoop):
    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.tasks_controller = TasksModeController(self, self.view)
        self.lists_controller = ListSelectionController(self, self.view)
        self.new_task_controller = NewTaskController(self, self.view)
        self.view.new_task_callback = self.new_task_controller.handler
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
        self.tasks_controller.active_list = list_descr
        self.display_task_list()

    def display_list_selection(self):
        self.active_controller = self.lists_controller

    def display_task_list(self):
        self.active_controller = self.tasks_controller

    def create_new_task(self):
        self.active_controller = self.new_task_controller
