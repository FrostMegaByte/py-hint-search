# PyHintSearch

_Note, the terms "type hint" and "type annotation" are used interchangably._

Welcome to type annotation searcher (PyHintSearch) based on ML-determined type annotations.

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

1. Install [Docker](https://www.docker.com/)
2. Follow the simple [Type4Py guide](https://github.com/saltudelft/type4py/wiki/Type4Py's-Local-Model) to get the ML model running
3. Install [Poetry](https://python-poetry.org/)
4. Pull this project
5. `cd type-annotation-searcher`
6. `poetry init`
7. `cd src`

## Pyright annotations for improved performance

To get some guaranteed correct type annotations and decrease the number of combinations the search algorithm needs to check, it is possible to let Pyright determine some type annotations beforehand by creating stub files in the 'typings' directory.

This can be performed by running:  
_(PATH_OF_PROJECT_TO_ANNOTATE should have forward slashes)_  
`poetry run python pyright_stubs_creator.py --project-dir "PATH_OF_PROJECT_TO_ANNOTATE"`

## Running the main searching algorithm

The main searching algorithm will fill in empty type slots with different combinations of ML-determined type hints in order to find a combination that passes the Pyright validation. The added type hints always satisfy the validation, but may not necessarily be the exact type annotations that were expected.

To run the main searching algorithm, enter the command:
_(PATH_OF_PROJECT_TO_ANNOTATE should have forward slashes)_  
`poetry run python main.py --project-dir "PATH_OF_PROJECT_TO_ANNOTATE"`
