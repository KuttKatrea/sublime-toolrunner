import sublime
import sys
from . import debug

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

        self.input.update_mode(input.get('mode'))
        self.input.update_allow_empty(input.get('allow_empty'))
        self.input.update_codec(input.get('codec'))

    def set_output(self, output):
        if output is None: return
        self.output.update_codec(output.get('codec'))
    
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
        self.mode = 'pipe'
        self.allow_empty = False
        self.codec = _default_input_codec

    def update_mode(self, mode):
        if mode is not None:
            self.mode = mode

            if mode == 'none':
                self.allow_empty = True

    def update_allow_empty(self, allow_empty):
        if allow_empty is not None:
            self.allow_empty = allow_empty

    def update_codec(self, codec):
        if codec is not None:
            self.codec = codec

class Output(object):
    def __init__(self):
        self.codec = _default_output_codec
        self.split = 'bottom'

    def update_codec(self, codec):
        if codec is not None:
            self.codec = codec

    def update_split(self, split):
        if split is not None:
            self.split = split
