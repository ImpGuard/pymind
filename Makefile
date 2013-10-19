.PHONY: venv, check, really-check

default:

check:
	nosetests

really-check:
	nosetests --with-coverage --cover-erase --cover-html --cover-package=pymind

clean:
	rm $(shell find pymind -name *.pyc)