CHANGES
=======

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
