#!/bin/bash
PACKAGE=Mathics-Django

# FIXME put some of the below in a common routine
function finish {
	cd $owd
}

cd $(dirname ${BASH_SOURCE[0]})
owd=$(pwd)
trap finish EXIT

if ! source ./pyenv-versions ; then
	exit $?
fi


cd ..
source mathics_django/version.py
echo $__version__
cp -v ${HOME}/.local/var/mathics/doc_html_data.pcl mathics_django/doc/

for pyversion in $PYVERSIONS; do
	if ! pyenv local $pyversion ; then
	exit $?
	fi
	rm -fr build
	python setup.py bdist_egg
	python setup.py bdist_wheel
done

python ./setup.py sdist
