import urwid


class Controller(urwid.MainLoop):
    completion_timeout = 0.8

    def __init__(self, model, view):
        self.model = model
        self.view = view
        super().__init__(self.view.tasks_view, view.palette,
                         unhandled_input=self.keypress)

    def mark_completed(self, _, user_data):
        task, view, widget = user_data
        self.model.update_task(task, completed=True)
        view.remove_task_element(widget)

    def task_widget_change_handler(self, view, widget, new_state, task):
        alarm = getattr(widget, 'alarm', None)
        if alarm:
            self.remove_alarm(alarm)
        else:
            widget.alarm = self.set_alarm_in(
                self.completion_timeout, self.mark_completed,
                user_data=(task, view, widget)
            )

    def keypress(self, key):
        if key.lower() == 'r':
            self.view.fill_tasks_view(self.list_descr,
                                      self.task_widget_change_handler)
        elif key.lower() == 'q':
            raise urwid.ExitMainLoop()

    def run(self, which_list, *args, **kwargs):
        self.list_descr = [l for l in self.model.lists()
                           if l['title'] == which_list][0]
        self.view.fill_tasks_view(self.list_descr,
                                  self.task_widget_change_handler,
                                  reset_focus=True)
        super().run(*args, **kwargs)
