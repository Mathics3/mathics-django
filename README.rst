Welcome to Mathics-Django
=========================

|CI Status| |Pypi Installs| |Latest Version| |Supported Python Versions|

|Packaging status|

This is the Django front-end to `Mathics <https://mathics.org>`_.

Features:
---------

* Extensive online documentation
* Integrated graphics, via `three.js <https://threejs.org>`_, and MathML mathematics output
* Notebook-like sessions

Note: in the future we intend to also proved a Jupyter-like interface.

ScreenShot
----------

mathicsserver: a Django-based Web interface
+++++++++++++++++++++++++++++++++++++++++++

|mathicssserver|


Running
-------

This is a Django project so Dango's `manage.py <https://docs.djangoproject.com/en/3.2/ref/django-admin/>`_ script used.

A simple way to start Mathics Django when GNU make is installed (which is the case on most POSIX systems):

::

   make runserver

Underneath this runs the Python program ``manage.py`` in ``mathics_django`` directory.

To get a list of the available commands, type ``python
mathics_django/manage.py help``. To get help on a specific command
give that command at the end. For example two commands that are useful
are the ``runserver`` and ``testserver`` commands. ``python
mathics_django/manage.py help runserver`` will show options in running
the Django server.


Environment Variables
+++++++++++++++++++++

There are two special environment variables of note which controls
where the Mathics database is located. This database is saves
authentication and worksheet information.

By default the database used is ``DATADIR + mathics.sqlite`` where
``DATADIR`` is under ``AppData/Python/Mathics/`` for MS-Windows and
``~/.local/var/mathics/`` for all others. If you want to specify your own database file set
environment variable ``MATHICS_DJANGO_DB_PATH``.

If you just want to set the ``mathics.sqlite`` portion, you can use
the environment variable ``MATHICS_DJANGO_DB``.

Information for the onine-documentation comes from one of two places,
``DOC_USER_HTML_DATA_PATH`` if that exists and
``DOC_SYSTEM_HTML_DATA_PATH`` as fallback if that doesn't exist. The
latter is created when the package is built. The former allows for the
user or developer to update this information. In the future it will
take into account plugins that have been added.


Contributing
------------

Please feel encouraged to contribute to Mathics! Create your own fork, make the desired changes, commit, and make a pull request.


License
-------

Mathics-Django is released under the GNU General Public License Version 3 (GPL3).

.. |mathicssserver| image:: https://mathics.org/images/mathicsserver.png
.. |Latest Version| image:: https://badge.fury.io/py/Mathics-Django.svg
		 :target: https://badge.fury.io/py/Mathics-Django
.. |Supported Python Versions| image:: https://img.shields.io/pypi/pyversions/Mathics-Django.svg
.. |CI status| image:: https://github.com/Mathics3/mathics-django/workflows/Mathics-Django%20(ubuntu)/badge.svg
		       :target: https://github.com/Mathics3/mathics-django/actions
.. |Packaging status| image:: https://repology.org/badge/vertical-allrepos/mathics-django.svg
			    :target: https://repology.org/project/mathics-django/versions
.. |Pypi Installs| image:: https://pepy.tech/badge/mathics-django
