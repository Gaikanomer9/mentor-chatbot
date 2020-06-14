.PHONY: prepare_venv run_tests

VENV_NAME?=venv
PYTHON=${VENV_NAME}/bin/python
prepare_venv: $(VENV_NAME)/bin/activate

$(VENV_NAME)/bin/activate: requirements.txt
	test -d $(VENV_NAME) || python -m virtualenv $(VENV_NAME)
	${PYTHON} -m pip install -U pip
	${PYTHON} -m pip install -r requirements.txt
	touch $(VENV_NAME)/bin/activate

run_tests: prepare_venv
	${PYTHON} -m pytest

deploy: prepare_venv
	test "$(CMT_MSG)"
	echo "Preparing a new commit which will trigger auto deployment"
	make run_tests
	echo "Tests passed succesfully"
	git add --all
	git commit -m "$(CMT_MSG)"
	git push origin master

run:
	${PYTHON} app.py
