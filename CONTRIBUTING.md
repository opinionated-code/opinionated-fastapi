# How to contribute


## Dependencies

We use [poetry](https://github.com/python-poetry/poetry) to manage dependencies.
Once you have it installed, set up a virtualenv and install this project's dependencies by running the `install` command:

```bash
poetry install
```

To activate your `virtualenv` run `poetry shell`, or run commands individually with `poetry run`.


## Code Style

We use Black with default options - make sure you run it on any code before committing.

## Documentation

All docstrings are in Google style, as we use mkdocstrings for the API documentation.

## Static Analysis

We use mypy for type checking. It is configured via pyproject.toml, and you can run it easily:

```commandline
mypy
```

## Tests

We use pytest. Run the test suite with:

```commandline
pytest
```

## Linting

We don't currently run any additional linting beyond code style with Black.

## Submitting your code

We use standard github style fork-and-pull-request for submissions. 

When creating a pull request for a submission:

1. Run `mypy` and `pytest` to make sure everything was working before making changes. This is important as it can expose issues in your local dev environment, even if code is passing all tests in the CI pipeline.
2. Add any changes you want. Try to break up changes into multiple commits where it makes sense to do so.
3. Write comments to explain the "why" of your changes - if you need to comment what it is doing, it might not help.
4. Add tests for the new changes.
6. Edit documentation where the change alters the behaviour of the code in any significant way.
7. Update `CHANGELOG.md` with a quick summary of your changes.
8. Run `pytest` again to make sure it is still working.
9. Run `mypy` to ensure that types are correct.
10. Run `black` to ensure that code style is correct.
