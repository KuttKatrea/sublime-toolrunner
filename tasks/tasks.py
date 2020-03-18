from invoke import run, task


@task
def flake8(c):
    run("flake8 ToolRunner.py lib tasks")


@task
def isort_check(c):
    run("isort --check -rc ToolRunner.py lib tasks")


@task
def black_check(c):
    run("black --check ToolRunner.py lib tasks")


@task
def isort(c):
    run("isort -rc ToolRunner.py lib tasks")


@task
def black(c):
    run("black ToolRunner.py lib tasks")


@task
def pytest(c):
    run("pytest src")


@task(pre=[flake8, isort_check, black_check])
def lint(c):
    pass


@task(pre=[isort, black])
def fix(c):
    pass


@task(pre=[pytest])
def test(c):
    pass
