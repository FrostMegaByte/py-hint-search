# PyHintSearch

_Note, the terms "type hint" and "type annotation" are used interchangably._

Welcome to PyHintSearch! This is a type annotation searcher based on ML-determined type annotations.

## Disclaimer

This project is meant to statically analyse a given Python project and add type annotations in yet to be filled-in slots. Due to the suggested type annotations being determined by a ML algorithm, it might not always be the exact type hint that is expected, but it does pass a test that checks the viability of that annotation.

E.g. you might receive:

```python
def multiply(a: int, b: int) -> int:
    return a * b
```

Whereas you expected it to be:

```python
def multiply(a: float, b: float) -> float:
    return a * b
```

The more annotations that are already provided in the code, the better the results.

## Setup

To run this project, perform the following steps and read further:

1. Install [Node.js](https://nodejs.org/en) (Needed for Pyright)
2. Install [Docker](https://www.docker.com/)
3. Follow the simple [Type4Py guide](https://github.com/saltudelft/type4py/wiki/Type4Py's-Local-Model) to get the ML model running
4. Install [Poetry](https://python-poetry.org/)
5. Pull this project
6. `cd py-hint-search`
7. `poetry init`
8. `cd src`

## Virtual environment

More accurate type annotations can be determined when all the dependencies of the project are installed in a virtual environment. Inside the folder of the project you want to annotate, we recommend running the following commands to create a virtual environment (or use tools like `poetry` or `pipenv`):

```bash
python -m venv .venv
source .venv/Scripts/activate # On Windows
source .venv/bin/activate # On Linux
pip install .
```

## Pyright annotations for improved performance

To get some guaranteed correct type annotations and decrease the number of combinations the search algorithm needs to check, it is possible to let Pyright determine some type annotations beforehand by creating stub files in the 'typings' directory.

This can be performed by running:  
_(PATH_OF_PROJECT_PYTHON_FILES_DIRECTORY should have forward slashes)_

```bash
poetry run python pyright_typestubs_creator.py --project-path "PATH_OF_PROJECT_PYTHON_FILES_DIRECTORY"
```

Note that these files might still contain function decorators, which sometimes break libcst's parsing of the Pyright stub files. If an error is thrown during the main searching algorithm failing on parsing the Pyright stub, we recommend manually editing the corresponding stub file inside the 'typings' directory (e.g. remove the failing function decorator).  
[https://microsoft.github.io/pyright/#/type-stubs?id=cleaning-up-generated-type-stubs](https://microsoft.github.io/pyright/#/type-stubs?id=cleaning-up-generated-type-stubs)

## Running the main searching algorithm

The main searching algorithm will fill in empty type slots with different combinations of ML-determined type hints in order to find a combination of type hints that passes the Pyright validation. The added type hints always satisfy the validation, but may not necessarily be the exact type annotations that were expected as shown in the disclaimer.

To run the main searching algorithm, enter the command:  
_(`PATH_OF_PROJECT_TO_ANNOTATE` and `PATH_OF_PROJECT_VIRTUAL_ENVIRONMENT` should have forward slashes)_

```bash
poetry run python main.py --project-path "PATH_OF_PROJECT_PYTHON_FILES_DIRECTORY" --venv "PATH_OF_PROJECT_VIRTUAL_ENVIRONMENT"
```

The following options can be specified in the command:

- `--project-path` (The path to the Python files directory of the project that will be type annotated)
- `--venv-path` (The path to the virtual environment of the project that will be type annotated)
- `--top-k` (Try the top-k type annotation predictions during search)
- `--keep-source-code-files` (Keep or discard the source code files after type annotating them)
