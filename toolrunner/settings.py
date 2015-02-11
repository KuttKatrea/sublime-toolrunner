import sublime
import platform
from .debug import log

class ToolRunnerSettings:
    def __init__(self, package):
        self.package = package

    def getPlatformSettingsFileName(self):
        return self.getSettingsFileName(sublime.platform().capitalize())

    def getHostSettingsFileName(self):
        return self.getSettingsFileName(platform.uname()[1])

    def getSettingsFileName(self, special=None):
        special = " (" + special + ")" if special else ""
        return "".join(("ToolRunner", special, ".sublime-settings"))

    def getSetting(self, settingName, default=None):
        host_settings = sublime.load_settings(
            self.getHostSettingsFileName())

        platform_settings = sublime.load_settings(
            self.getPlatformSettingsFileName())

        user_settings = sublime.load_settings(
            self.getSettingsFileName())

        return host_settings.get(settingName,
            platform_settings.get(settingName,
            user_settings.get(settingName, default)
            ))

    def setSetting(self, settingName, settingValue):
        host_settings = sublime.load_settings(
            self.getHostSettingsFileName())

        # user_settings = sublime.load_settings(
        #     self.getSettingsFileName())

        host_settings.set(settingName, settingValue)

        sublime.save_settings(self.getHostSettingsFileName())

    def getConnectionList(self):
        return self.getSetting('connections')

    def getSettingsFilePath(self, scope):
        return "${packages}/%0s/%1s" % self.getSettingsPieces(scope)

    def getSettingsPieces(self, scope):
        if scope == 'host':
            return ('User/', self.getHostSettingsFileName())
        elif scope == 'user':
            return ('User/', self.getSettingsFileName())
        elif scope == 'os':
            return ('User/', self.getPlatformSettingsFileName())
        else:  # default
            return (self.package, self.getSettingsFileName())

    def getGroups(self):
        groups = self.getSetting('user_groups', [])
        groups += self.getSetting('os_groups', [])
        groups += self.getSetting('host_groups', [])

        return groups

    def getProfiles(self, profile_group):
        groups = self.getGroups()

        for group in groups:
            if group["name"] == profile_group:
                return group["profiles"]

        return []
