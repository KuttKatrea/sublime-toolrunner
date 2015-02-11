class ToolRunnerViewManager(object):
    def __init__(self, settings):
        self.settings = settings
        self.views_by_source_id = dict()
        self.sources_by_target_id = dict()
        self.commands_for_view = dict()

    def getViewForSource(self, view):
        source_id = str(view.id())

        if source_id not in self.views_by_source_id:
            new_view = view.window().new_file()

            self.views_by_source_id[source_id] = new_view
            self.sources_by_target_id[str(new_view.id())] = source_id

        return self.views_by_source_id[source_id]

    def getCommandForView(self, view):
        view_id = str(view.id())

        if view_id not in self.commands_for_view:
            if view_id in self.views_by_source_id:
                view_id = str(self.views_by_source_id[view_id].id())
            else:
                return None

        if view_id in self.commands_for_view:
            return self.commands_for_view[view_id]

        return None

    def setCommandForView(self, target_view, command):
        view_id = str(target_view.id())
        if command is None:
            self.commands_for_view.pop(view_id,None)
        else:
            self.commands_for_view[view_id] = command

    def remove(self, view):
        target_id = str(view.id())
        source_id = self.sources_by_target_id.pop(target_id, None)
        if source_id is not None:
            self.views_by_source_id.pop(str(source_id), None)
