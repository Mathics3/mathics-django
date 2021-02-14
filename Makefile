# A GNU Makefile to run various tasks - compatibility for us old-timers.

# Note: This makefile include remake-style target comments.
# These comments before the targets start with #:
# remake --tasks to shows the targets and the comments

GIT2CL ?= admin-tools/git2cl
PYTHON ?= python3
PIP ?= pip3
RM  ?= rm

.PHONY: all build \
   check clean \
   develop dist doc doc-data djangotest docker \
   gstest pytest \
   rmChangeLog \
   test

SANDBOX	?=
ifeq ($(OS),Windows_NT)
	SANDBOX = t
else
	UNAME_S := $(shell uname -s)
	ifeq ($(UNAME_S),Darwin)
		SANDBOX = t
	endif
endif

#: Default target - same as "develop"
all: develop

#: build everything needed to install
build:
	$(PYTHON) ./setup.py build

#: Set up to run from the source tree
develop:
	$(PIP) install -e .

#: Make distirbution: wheels, eggs, tarball
dist:
	./admin-tools/make-dist.sh

#: Install Mathics-Django
install:
	$(PYTHON) setup.py install

#: Run Django-based server in development mode. Use environment variable "o" for manage options
runserver:
	$(PYTHON) mathics_django/manage.py runserver $o

check: djangotest doctest

#: Remove derived files
clean:
	for dir in mathics-django/doc ; do \
	   ($(MAKE) -C "$$dir" clean); \
	done;

#: Run tests that appear in docstring in the code.
doctest:
	SANDBOX=$(SANDBOX) $(PYTHON) mathics_django/test.py $o

#: Run Django tests
djangotest:
	cd mathics_django && $(PYTHON) manage.py test test_django

#: Remove ChangeLog
rmChangeLog:
	$(RM) ChangeLog || true

#: Create a ChangeLog from git via git log and git2cl
ChangeLog: rmChangeLog
	git log --pretty --numstat --summary | $(GIT2CL) >$@
