"""
Development tasks for usage with Invoke
"""
from invoke import Exit, UnexpectedExit, run, task

SOURCE_PATHS = "tool_runner_plugin.py src tasks test"


@task()
def pylint(_, warn=False):
    run(f"pylint --rcfile=setup.cfg {SOURCE_PATHS}", warn=warn)


@task()
def flake8(_, warn=False):
    run(f"flake8 {SOURCE_PATHS}", warn=warn)


@task()
def mypy(_, warn=False):
    run(f"mypy --strict {SOURCE_PATHS}", warn=warn)


@task()
def isort_check(_, warn=False):
    run(f"isort --check {SOURCE_PATHS}", warn=warn)


@task()
def black_check(_, warn=False):
    run(f"black -t py38 --check {SOURCE_PATHS}", warn=warn)


@task()
def isort(_):
    run(f"isort {SOURCE_PATHS}")


@task()
def black(_):
    run(f"black -t py38 {SOURCE_PATHS}")


@task()
def pytest(_):
    run("pytest test")


@task()
def check(context):
    errored = False

    print("--- Flake8 ---")
    try:
        flake8(context)
    except (UnexpectedExit, Exit):
        errored = True

    print("--- MyPy ---")
    try:
        mypy(context)
    except (UnexpectedExit, Exit):
        errored = True

    print("--- iSort ---")
    try:
        isort_check(context)
    except (UnexpectedExit, Exit):
        errored = True

    print("--- black ---")
    try:
        black_check(context)
    except (UnexpectedExit, Exit):
        errored = True

    if errored:
        raise Exit(message="Some checks failed", code=1)


@task()
def lint(context):
    errored = False

    try:
        check(context)
    except (UnexpectedExit, Exit):
        errored = True

    print("--- PyLint ---")
    try:
        pylint(context)
    except (UnexpectedExit, Exit):
        errored = True

    if errored:
        raise Exit(message="Some checks failed", code=1)


@task()
def fix(c):
    isort(c)
    black(c)


@task()
def test(context):
    pytest(context)
