from . import debug, settings

_default_input_codec = None
_default_output_codec = None


def _set_default_codecs():
    global _default_input_codec
    global _default_output_codec

    _default_input_codec = "utf-8"  # 'cp850'
    _default_output_codec = "utf-8"  # 'cp850'


class ConfigContainer(object):
    def _get_defaults(self):
        return dict()

    def __init__(self, **kwargs):
        defaults = self._get_defaults()

        self._props = set(defaults.keys())

        self.update(defaults)
        self.update(kwargs)

    def update(self, config):
        if config is None:
            return

        for k in config:
            if k in self._props:
                attr_value = config.get(k)

                # debug.log("Updating %s with %s" % (k, attr_value))

                current_attr = getattr(self, k, None)

                if isinstance(current_attr, ConfigContainer):
                    current_attr.update(attr_value)
                else:
                    setattr(self, k, attr_value)

    def __repr__(self):
        return self.__class__.__name__ + ":" + self.__dict__.__repr__()


class Tool(ConfigContainer):
    command_arguments = dict(
        input_source="input_source", results="results", params="params_values"
    )

    def _get_defaults(self):
        return dict(
            name="",
            cmd="",
            shell=False,
            arguments=list(),
            input=Input(),
            output=Output(),
            results=Results(),
            params=dict(),
            input_source=None,
            params_values=dict(),
        )

    def set_command_arguments(self, *args):
        def get_value(argName):
            for conf in args:
                if argName in conf:
                    return conf[argName]
            return None

        conf = {
            value: get_value(key) for (key, value) in Tool.command_arguments.items()
        }

        self.update(conf)

    def get_command_array(self, input_text=None):
        if type(self.cmd) == list:
            full_arguments = self.cmd.copy()
        else:
            full_arguments = [self.cmd]

        positional_arguments = []
        named_arguments = []
        flag_arguments = []

        if self.params_values is not None:
            for param_key, param_value in self.params_values.items():
                param = self.params[param_key]

                if param.get("type") == "positional":
                    positional_arguments.append(param_value)
                elif param.get("type") == "named":
                    named_arguments.append(param.get("argument"))
                    named_arguments.append(param_value)
                elif param.get("type") == "flag":
                    if param_value:
                        flag_arguments.append(param.get("argument"))

        for argument in self.arguments:
            if argument == "$[toolrunner_positional_arguments]":
                full_arguments += positional_arguments

            elif argument == "$[toolrunner_named_arguments]":
                full_arguments += named_arguments

            elif argument == "$[toolrunner_flag_arguments]":
                full_arguments += flag_arguments

            else:
                full_arguments.append(argument)

        return full_arguments


class Input(ConfigContainer):
    def _get_defaults(self):
        return dict(
            mode="pipe",  # tmpfile-path, cmdline
            allow_empty=False,
            file_suffix=None,
            codec=_default_input_codec,
        )

    def update(self, config):
        ConfigContainer.update(self, config)

        if self.mode == "none":
            self.allow_empty = True


class Output(ConfigContainer):
    def _get_defaults(self):
        return dict(
            mode="pipe", codec=_default_output_codec  # tmpfile-path, tmpfile-pipe
        )


class Results(ConfigContainer):
    def _get_defaults(self):
        return dict(
            mode=settings.get_setting("default_output_mode"),
            read_only=False,
            scratch=True,
            line_numbers=False,
            syntax_file=settings.get_setting("default_syntax_file"),
        )


def _on_plugin_loaded():
    debug.log("Setting defaults for tools")
    _set_default_codecs()


settings.register_on_plugin_loaded(_on_plugin_loaded)
