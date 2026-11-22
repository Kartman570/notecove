PYTHON ?= python3

test:
	$(PYTHON) -m unittest discover -s tests

lint:
	$(PYTHON) -m ruff check notecove tests

coverage:
	$(PYTHON) -m coverage run --source=notecove -m unittest discover -s tests
	$(PYTHON) -m coverage report -m
