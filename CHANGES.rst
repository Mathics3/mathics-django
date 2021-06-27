CHANGES
=======

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
