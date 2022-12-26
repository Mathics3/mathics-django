# A GNU Makefile to run various tasks - compatibility for us old-timers.

# Note: This makefile include remake-style target comments.
# These comments before the targets start with #:
# remake --tasks to shows the targets and the comments

GIT2CL ?= admin-tools/git2cl
MATHICS_CHARACTER_ENCODING ?= ASCII
PYTHON ?= python
PIP ?= pip3
RM  ?= rm

.PHONY: all build \
	check clean \
	develop dist doc doc-data djangotest docker \
	gstest pytest \
	rmChangeLog \
	test

THREEJS=mathics_django/web/media/js/mathics-threejs-backend/index.js mathics_django/web/media/js/mathics-threejs-backend/version.json
SANDBOX	?=
ifeq ($(OS),Windows_NT)
	SANDBOX = t
else
	UNAME_S := $(shell uname -s)
	ifeq ($(UNAME_S),Darwin)
		SANDBOX = t
	endif
endif

#: Default target - same as "develop".
all: develop

#: Build everything needed to install.
build: $(THREEJS)
	$(PYTHON) ./setup.py build

check: djangotest doctest-workaround

#: Remove derived files.
clean:
	@rm $(THREEJS) || true;

#: Set up to run from the source tree.
develop: $(THREEJS)
	$(PIP) install -e .

#: Make distribution: wheels, eggs, tarball.
dist: $(THREEJS)
	./admin-tools/make-dist.sh

#: Run Django tests.
djangotest: $(THREEJS)
	cd mathics_django && $(PYTHON) manage.py test test_django

#: Run tests that appear in docstring in the code.
doctest-workaround:
	MATHICS_CHARACTER_ENCODING=$(MATHICS_CHARACTER_ENCODING) SANDBOX=$(SANDBOX) $(PYTHON) mathics_django/docpipeline.py --exclude=NIntegrate,MaxRecursion
	MATHICS_CHARACTER_ENCODING=$(MATHICS_CHARACTER_ENCODING) SANDBOX=$(SANDBOX) $(PYTHON) mathics_django/docpipeline.py --sections=NIntegrate,MaxRecursion

#: Run tests that appear in docstring in the code.
doctest: $(THREEJS)
	MATHICS_CHARACTER_ENCODING=$(MATHICS_CHARACTER_ENCODING) SANDBOX=$(SANDBOX) $(PYTHON) mathics_django/docpipeline.py $o

#: Make Python Pickle-format document data.
doc-data:
	$(PYTHON) mathics_django/docpipeline.py -o --want-sorting

#: Install Mathics-Django
install: $(THREEJS)
	$(PYTHON) setup.py install

#: Run Django-based server in development mode. Use environment variable "o" for manage options
runserver: $(THREEJS)
	$(PYTHON) mathics_django/manage.py runserver $o

#: Remove ChangeLog
rmChangeLog:
	$(RM) ChangeLog || true

#: Run Django-based server in testserver mode. Use environment variable "o" for manage options
testserver: $(THREEJS)
	$(PYTHON) mathics_django/manage.py testserver $o

#: Create a ChangeLog from git via git log and git2cl
ChangeLog: rmChangeLog
	git log --pretty --numstat --summary | $(GIT2CL) >$@

node_modules/\@mathicsorg/mathics-threejs-backend/package.json node_modules/@mathicsorg/mathics-threejs-backend/package.json:
	npm install @mathicsorg/mathics-threejs-backend --loglevel=error

#: Install mathics-threejs-backend with npm and copy the necessary files to the right place.
build_mathics-threejs-backend: node_modules/\@mathicsorg/mathics-threejs-backend/package.json
	cp mathics_django/web/media/js/mathics-threejs-backend/index-no-custom-shader.js mathics_django/web/media/js/mathics-threejs-backend/index.js; \
	cp mathics_django/web/media/js/mathics-threejs-backend/version-no-custom-shader.js mathics_django/web/media/js/mathics-threejs-backend/version.json
# 	cp node_modules/\@mathicsorg/mathics-threejs-backend/docs/build.js mathics_django/web/media/js/mathics-threejs-backend/index.js; \
# 	cp node_modules/\@mathicsorg/mathics-threejs-backend/package.json mathics_django/web/media/js/mathics-threejs-backend/version.json


$(THREEJS): node_modules/@mathicsorg/mathics-threejs-backend/package.json package.json
	$(MAKE) build_mathics-threejs-backend
