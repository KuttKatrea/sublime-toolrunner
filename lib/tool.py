import sublime
import sys
from . import debug
from . import settings

_default_input_codec = None
_default_output_codec = None

def _set_default_codecs():
    global _default_input_codec
    global _default_output_codec

    _default_input_codec = 'cp850'
    _default_output_codec = 'cp850'

class ConfigContainer(object):
    def _get_defaults(self):
        return dict()

    def __init__(self, **kwargs):
        defaults = self._get_defaults()

        self._props = set(defaults.keys())

        debug.log("%s", self._props)

        self.update(defaults)
        self.update(kwargs)

        debug.log(self)

    def update(self, config):
        if config is None:
            return

        for k in config:
            if k in self._props:
                attr_value = config.get(k)

                debug.log("Updating %s with %s" % (k, attr_value))

                current_attr = getattr(self, k, None)

                if isinstance(current_attr, ConfigContainer):
                    current_attr.update(attr_value)
                else:
                    debug.log("Setting")
                    setattr(self, k, attr_value)

    def __repr__(self):
        return self.__class__.__name__ + ':' + self.__dict__.__repr__();

class Tool(ConfigContainer):
    command_arguments = dict(
        input_source="input_source",
        output="output",
        params="param_values",
    )

    def _get_defaults(self):
        return dict(
            name = "",
            cmd = "",
            arguments = list(),
            input = Input(),
            output = Output(),
            input_source = None,
            params_values = dict(),
        )

    def set_command_arguments(self, *args):
        def get_value(argName):
            for conf in args:
                if argName in conf:
                    return conf[argName]
            return None

        conf = {value: get_value(key) for (key, value) in Tool.command_arguments.items()}

        self.update(conf)

    def get_command_array(self, input_text=None):
        debug.log("Building command line array")

        full_arguments = [ self.cmd ]

        positional_arguments = []
        named_arguments = []
        flag_arguments = []

        debug.log("Generating argument list for params", self.params_values)
        for param_key, param_value in self.params_values.items():
            debug.log("Matching param: %s = %s" % (param_key, param_value))

            param = self.params[param_key]

            if param.get('type') == "positional":
                positional_arguments[param.order] = param_value
            elif param.get('type') == "named":
                named_arguments.append(param.get('argument'))
                named_arguments.append(param_value)
            elif param.get('type') == "flag":
                if param_value:
                    flag_arguments.append(param.get('argument'))

        debug.log("Positional args: ", positional_arguments)
        debug.log("Named args: ", named_arguments)
        debug.log("Flag args: ", flag_arguments)

        debug.log("Embedding in ", self.arguments)

        for argument in self.arguments:
            if argument == "${positional_args}":
                full_arguments += positional_arguments

            elif argument == "${named_args}":
                full_arguments += named_arguments

            elif argument == "${flags}":
                full_arguments += flag_arguments

            elif argument == "${input}":
                full_arguments += input_text

            else:
                full_arguments.append(argument)

        return full_arguments

class Input(ConfigContainer):
    def _get_defaults(self):
        return dict(
            mode = 'pipe',
            allow_empty = False,
            codec = _default_input_codec,
        )

    def update(self, config):
        ConfigContainer.update(self, config)

        if self.mode == 'none':
            self.allow_empty = True


class Output(ConfigContainer):
    def _get_defaults(self):
        return dict(
            type = 'buffer',
            reuse = 'view',
            split = 'bottom',
            focus_on_source_focus = True,
            focus_on_run = True,
            read_only = True,
            scratch = True,
            syntax_file = settings.get_setting('default_syntax_file'),
            codec = _default_output_codec,
            keep_reusing_after_save = False,
        )

def _on_plugin_loaded():
    debug.log("Setting defaults for tools")
    _set_default_codecs()

settings.register_on_plugin_loaded(_on_plugin_loaded)
