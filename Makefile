# Build, package, test, and clean
PROJECT=pygmt
TESTDIR=tmp-test-dir-with-unique-name
PYTEST_ARGS=--cov=$(PROJECT) --cov-config=../.coveragerc \
			--cov-report=term-missing --cov-report=xml --cov-report=html \
			--doctest-modules -v --mpl --mpl-results-path=results \
			--pyargs ${PYTEST_EXTRA}
BLACK_FILES=$(PROJECT) setup.py doc/conf.py examples
FLAKE8_FILES=$(PROJECT) setup.py
LINT_FILES=$(PROJECT) setup.py

help:
	@echo "Commands:"
	@echo ""
	@echo "  install   install in editable mode"
	@echo "  test      run the test suite (including doctests) and report coverage"
	@echo "  format    run black to automatically format the code"
	@echo "  check     run code style and quality checks (black and flake8)"
	@echo "  lint      run pylint for a deeper (and slower) quality check"
	@echo "  clean     clean up build and generated files"
	@echo ""

install:
	pip install --no-deps -e .

test:
	# Run a tmp folder to make sure the tests are run on the installed version
	mkdir -p $(TESTDIR)
	@echo ""
	@cd $(TESTDIR); python -c "import $(PROJECT); $(PROJECT).show_versions()"
	@echo ""
	# There are two steps to the test here because `test_grdimage_over_dateline`
	# passes only when it runs before the other tests.
	# See also https://github.com/GenericMappingTools/pygmt/pull/476
	cd $(TESTDIR); pytest -m runfirst $(PYTEST_ARGS) $(PROJECT)
	cd $(TESTDIR); pytest -m 'not runfirst' $(PYTEST_ARGS) $(PROJECT)
	cp $(TESTDIR)/coverage.xml .
	cp -r $(TESTDIR)/htmlcov .
	rm -r $(TESTDIR)

format:
	black $(BLACK_FILES)

check:
	black --check $(BLACK_FILES)
	flake8 $(FLAKE8_FILES)

lint:
	pylint $(LINT_FILES)

clean:
	find . -name "*.pyc" -exec rm -v {} \;
	find . -name "*~" -exec rm -v {} \;
	rm -rvf build dist MANIFEST *.egg-info __pycache__ .coverage .cache htmlcov coverage.xml
	rm -rvf $(TESTDIR)
	rm -rvf baseline
