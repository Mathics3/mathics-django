CHANGES
=======

9.0.0
-----

Aug 29, 2025

* Support for 3.13 added, Python 3.8 and 3.9 dropped
* Ajust for 9.0.0 Mathics3 Kernel API.
* Adjust tests gallery
* Add to bottom of docs next/prev

Bugs
----

#228 Service /media/ urls from a relative not absolute URL

8.0.1
-----

Feb 8, 2025

* Adjust and correct packaging (thanks to Atri Bhattacharya for testing and packaging in OpenSUSE) .
* Documentation adjusted. Update to newer MathML code and track API changes in Mathics Kernel (Mauricio Matera).


8.0.0
-----

Jan 26, 2025

* Adjust for Mathics3 core 8.0.0 API
* Add bottom documentation navigation bar
* Add summaries of items in searching. Bold (no summary) indicates a section header
* Revise gallery example
* Track Combinatorica package name change


7.0.0
-----

Aug 10, 2025

* Adjust for Mathics3 core 7.0.0 API, e.g., add explicit call to load builtins
* doctest refactored to use more routines common to mathics-core
* Support newer matplotlib, e.g. 3.9.1
* Update gallery examples
* Add background and tooltips to Graphics3D
* Expand information in /about:
   - max digits in string
   - system encoding
   - time format



6.0.0
-----

* Use the latest mathics_threejs_backend: 1.3.1
* Environment variables which change Django settings (also shown under Settings)
  - ``MATHICS_DJANGO_ALLOWED_HOSTS`` sets Django ``ALLOWED_HOST``; use semicolon to separate entries
  - ``MATHICS_DJANGO_DEBUG_HOSTS`` sets Django ``DEBUG``
  - ``MATHICS_DJANGO_DISPLAY_EXCEPTIONS_HOSTS`` sets Django ``DISPLAY_EXCEPTIONS``
* Adjust for Mathics3 core 6.0.0 API
* "About" page:
  - Python Implementation (CPython, PyPy, Pyston) explicitly is shown
  - Optional Python packages are also shown along with their version
* Long ``<url>`` lines in documentation split into several lines.
* Gallery examples now include image manipulation and Mathics3 Graph and NLP modules
* Mathics3 errors are displayed better showing error tags, messages, and output more visible distinct.
* Python tracebacks shown in the browser as formatted nicer; use ``make runserver-debug`` to have Python tracebacks included in browser, in addition to the backend console.
* Menubar entries add for:
  - running gallery examples
  - going to github repository for Mathics-Django
  - getting to the information page
* Split out controllers into separate files
* Upgrade to fontawesome 6.2.1

We have gradually been rolling in more Python type annotations and have been using current Python practices. Tools such as using ``isort``, ``black`` and ``flake8`` are used as well.


5.0.0
-----

* Adjust for Mathics3 core 5.0.0 API
* Sort document reference chapters and sections
* Urls can now have links in them


4.0.2
-----

* Extend summary lists to chapters and sections
* Support Django 4.0
* Add GPL Copyright notice to popup startup boxes
* Update mathics-threejs-backend to 1.0.3, and in this three.js to 1.3.5

4.0.1
-----

Fix a small packaging issue where we weren't install ``autoload/settings.m``.
This combined with a bug in Mathics core was causing evaluationg expressions
to fail.


4.0.0
-----

The main thrust behind this API-breaking release is to be able to
support a protocol for Graphics3D.

It new Graphics3D protocol is currently expressed in JSON. There is an
independent `threejs-based module
<https://www.npmjs.com/package/@mathicsorg/mathics-threejs-backend>`_
to implement this. Tiago Cavalcante Trindade is responsible for this
code.

Previously, this Javascript code and library was embedded into this
code base. By separating the two, this library can be used more easily
outside of Django. And the library has gotten considerably better in
terms of being tested and documented.

The other main API-breaking change is more decentralization of the
Mathics Documentation. A lot more work needs to go on here, and so
there will be one or two more API breaking releases. After this
release, the documentation code will be split off into its own git
repository.

Enhancements
++++++++++++

* a Graphics3D protocol, mentioned above, has been started
* ``mathics_django.setting`` has been gone over to simplify.
* The "about" page now includes the Python version as well as the
  mathics-threejs-backend version
* Some Image Gallery examples have been added. Some of the examples
  have been reordered to put the slower examples towards the end.
* Much of the Javascript code that remains after pulling out the
  Graphics3D code has been modernized.
* Use of the "scriptaculous" library has been reduced. It will be
  eliminated totally in a future release.


Documentation
.............

* Document data used in producing HTML-rendered documents is now
  stored in both the user space, where it can be extended, and in the
  package install space -- which is useful when there is no user-space
  data.
* Code duplication used in creating documentation has been reduced. It
  will be moved more completely out in a future release
* Summary text for various built-in functions has been started. These
  summaries are visible in Mathics Django when lists links are given
  in Chapters, Guide Sections, or Sections. See the online
  documentation of ``Associations`` for an example of a list with
  additional summary information.

Regressions
+++++++++++

* Some of the test output for buitins inside a guide sections is not
  automatically rendered. See the on-line documentation for ``Binarize`` for
  an example of this.
* Density plot rendered in Mathics Django do not render as nice since we no longer
  use the secret protocol handshake hack. We may fix this in a future release


3.2.0
-----

Use NPM package `mathics-threejs-backend <https://www.npmjs.com/package/@mathicsorg/mathics-threejs-backend>`_ to provide 3D Graphics rendering via `three.js <threejs.org>`_.

3.1.0
-----

* Add ``Arrow`` and ``Cylinder`` (preliminary)
* Improve sectioning and subsectioning. (A lot more could be done on both the data tagging and presentation side)
* Improve gallery examples
* Modernize Javascript code more and get closer to removing scriptaculous

3.0.1
-----

Fix packaging issues: ``settings.m`` wasn't getting included in package.

3.0.0
-----

This release contains been a major overhaul and upgrade of the code.

It can't be stressed enough, but this was made only possible due to
the tireless work of Tiago Cavalcante Trindade.

There is still a lot of work still to do. However where we are at
right now, there have been massive changes and improvements:

* three.js has been upgraded to r124 (from r52) which brings us from
  up seven years from circa 2013 to late 2020!
* Plots and Graphs no longer appear inside MathML when there is no reason for them to be in MathML.
* The "About" page now shows all of the the Mathics ``Settings`` that
  are in effect. You can change Boolean setting inside the About page.
* 3D Polygon rendering has been greatly improved. However we currently
  do not handle even/odd space filling.
* We support TickStyle coloring in 3D Graphics.
* Tick positions in most 2D Plots and Graphs as been fixed.
* We tolerate smaller screens in SVG rendering.
* Styling of Cells has been improved. A somewhat Jupyter-style frame box is used.
* Output which are strings now have surrounding quotes. (This can be
  turned off via ``Settings`$QuotedStrings``.)
* In headings, we make it more clear that the code is Django
  based. This is to make clear the distinction should there be a
  Flask-based front-end or the long sought for Jupyter front end.
* In the online document, sections which are empty are omitted from
  the online view.
* A stray in the space between logo and Mathics at the top was removed.
* Gallery examples have been improved.
* A major rewrite of the JavaScript code according to more modern
  Javascript style has been started. More work will probably continue
  in future releases.
* Respecting ``PointSize`` in the rendering of 3D plots as been
  fixed. The default point size now more closely matches the intended specification.
* The use of Prototype and Scriptaculous are being phased out.



2.2.0
-----

* Upgrade to MathJax-2.7.9. See `MathJax v2.7.9 <https://github.com/mathjax/MathJax/releases/tag/2.7.9>`_.
  Over a decade of improvements here. One that I like is that output which is too large to fit on this screen can be viewed in the Zoom popup which has a scrollbar.
* Don't use MathJax for string output. (HTML/Hrefs coming later)
* String output is no longer passed to MathJax for rendering in MathML. As a result its output is more visually distinct from unexpanded and symbol output:
  it is left aligned and in a different monospace font. In the future we may consider settings for enabling/disabling this.
* Create a ``settings.m`` including ``Settings`$UseSansSerif`` and autoload that.
* "About" page expanded to include Machine, System, and Directory information



2.2.0rc1
--------

* Upgrade to `Django 3.2 <https://docs.djangoproject.com/en/3.2/releases/3.2/>` or newer. Django 3.2 is `long-term support release <https://docs.djangoproject.com/en/3.2/internals/release-process/#term-long-term-support-release>`_
* Upgrade three.js to r52. See PR #36.
* Allow Django's database (default ``mathics.sqlite``) to be settable from environment variables ``MATHICS_DJANGO_DB`` and ``MATHICS_DJANGO_DB_PATH``.
* Update gallery examples with more graphics
* Add an "about" page to show version information and for installed software three.js and MathJax.

2.1.0
-----

* Text inside graphics fixed. In particular 2D plots show axes labels.
  See `PR #1209 <https://github.com/Mathics3/mathics-django/pull/28/>`_.
* Allow worksheet deletion. Contributed by danielpyon.
  See `PR #1209 <https://github.com/Mathics3/mathics-django/pull/26/>`_.
* Update Gallery examples - includes a 2D plot inside a table and a plot with colored axes using ``TickStyle``.
* Fixed displaying CompiledCode.

2.0.1
-----

Small bug fixes.

* Saving and loading had a bug due to a Django API change. See PR #24
* non-django-specific unit tests duplicated from from Mathics have been removed.
* Add networkx dependency Fixes #18

2.0.0
-----

* Use Mathics-Scanner
* Unicode translation improvements
* FullForm & OutputForm should not use MathML

1.0.0
-----

Code split off from Mathics 1.1.0. We have some support for NetworkX/pyplot graphs.
