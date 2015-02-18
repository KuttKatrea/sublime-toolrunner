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

_set_default_codecs()

class Tool(object):
    def __init__(self):
        self.name = ""
        self.cmd = ""
        self.arguments = []
        self.input = Input()
        self.output = Output()
        self.input_source = None
        self.params_values = {}

    def set_name(self, name):
        if name is not None:
            self.name = name

    def set_cmd(self, cmd):
        debug.log(cmd)
        if cmd is not None:
            self.cmd = cmd

    def set_arguments(self, arguments):
        debug.log(arguments)
        if arguments is not None:
            self.arguments = arguments

    def set_input(self, input):
        if input is None: return

        self.input.mode = input.get('mode')
        self.input.allow_empty = input.get('allow_empty')
        self.input.codec = input.get('codec')

    def set_output(self, output):
        if output is None: return
        self.output.codec = output.get('codec')
        self.output.syntax_file = output.get('syntax_file')
    
    def set_params(self, params):
        if params is not None:
            self.params = params

    def set_input_source(self, input_source):
        if input_source is not None:
            self.input_source = input_source 

    def set_params_values(self, params_values):
        if params_values is not None:
            self.params_values = params_values

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

class Input(object):
    def __init__(self):
        self._mode = 'pipe'
        self._allow_empty = False
        self._codec = _default_input_codec

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, new_mode):
        if new_mode is not None:
            self._mode = new_mode

            if new_mode == 'none':
                self.allow_empty = True
    
    @property
    def allow_empty(self):
        return self._allow_empty

    @allow_empty.setter
    def allow_empty(self, new_allow_empty):
        if new_allow_empty is not None:
            self._allow_empty = new_allow_empty

    @property
    def codec(self):
        return self._codec

    @codec.setter
    def codec(self, new_codec):
        if new_codec is not None:
            self._codec = new_codec

class Output(object):
    def __init__(self):
        self._codec = _default_output_codec
        self._split = 'bottom'
        self._syntax_file = settings.expand(settings.get_setting('default_syntax_file'))

    @property
    def codec(self):
        return self._codec

    def codec(self, new_codec):
        if new_codec is not None:
            self._codec = new_codec

    @property
    def split(self):
        return self._split

    def split(self, new_split):
        if new_split is not None:
            self._split = new_split

    @property
    def syntax_file(self):
        return self._syntax_file

    @syntax_file.setter
    def syntax_file(self, new_syntax_file):
        if new_syntax_file is not None:
            self._syntax_file = settings.expand(settings.get_setting('default_syntax_file'))
