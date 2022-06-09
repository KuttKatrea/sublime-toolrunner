import logging

from lib.engine import (
    Command,
    Input,
    InputProvider,
    Output,
    OutputProvider,
    Tool,
    run_command,
)


class InlineInputProvider(InputProvider):
    def __init__(self, input_text):
        self.input_text = input_text

    def get_input_text(self):
        return self.input_text


class ConsoleOutputProvider(OutputProvider):
    def writeline(self, line: str):
        logging.info(line.rstrip())


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)-15s.%(msecs)03d %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

cmd = Command(
    tool=Tool(
        name="python",
        cmd=["python"],
        arguments=["-B", "-", "$[toolrunner_output_file]"],
        input=Input(
            mode="pipe",
        ),
        output=Output(
            mode="tmpfile-path",
        ),
        placeholders={},
    ),
    input_provider=InlineInputProvider(
        """
import time, sys
print(sys.argv[1])
with open(sys.argv[1], mode="w", buffering=1) as out:
    for k in range(10):
        print(f"{k}")
        out.write(f"{k}\\n")
        time.sleep(1)
"""
    ),
    output_provider=ConsoleOutputProvider(),
    placeholders_values={},
    environment={"PYTHONUNBUFFERED": "1"},
)


def on_exit(status_code: int):
    logging.info(f"Process exited with {status_code}")


if __name__ == "__main__":
    run_command(cmd, on_exit)
