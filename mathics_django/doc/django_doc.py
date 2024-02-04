# -*- coding: utf-8 -*-
"""
This code is the Django-specific part of the homegrown sphinx documentation.
FIXME: Ditch this and hook into sphinx
"""

import pickle
import re
from typing import Optional

from django.utils.safestring import mark_safe
from mathics import settings
from mathics.doc.common_doc import (
    DocChapter,
    DocGuideSection,
    DocSection,
    DocSubsection,
    DocTest,
    DocTests,
    DocText,
    DocumentationEntry,
    MathicsMainDocumentation,
    Tests,
    get_results_by_test,
    parse_docstring_to_DocumentationEntry_items,
    sorted_chapters,
)
from mathics.doc.utils import slugify

from mathics_django.doc.utils import escape_html
from mathics_django.settings import get_doctest_html_data_path

# FIXME: remove globalness
doctest_html_data_path = get_doctest_html_data_path(should_be_readable=True)
try:
    with open(doctest_html_data_path, "rb") as doctest_html_data_file:
        doc_data = pickle.load(doctest_html_data_file)
except IOError:
    print(f"Trouble reading Doc file {doctest_html_data_path}")
    doc_data = {}


class DjangoDocElement:
    def href(self, ajax=False):
        if ajax:
            return f"javascript:loadDoc('{self.get_uri()}')"
        else:
            return f"/doc{self.get_uri()}"

    def get_prev(self):
        return self.get_prev_next()[0]

    def get_next(self):
        return self.get_prev_next()[1]

    def get_collection(self):
        return []

    def get_prev_next(self):
        collection = self.get_collection()
        index = collection.index(self)
        prev = collection[index - 1] if index > 0 else None
        next = collection[index + 1] if index < len(collection) - 1 else None
        return prev, next

    def get_title_html(self):
        return mark_safe(escape_html(self.title, single_line=True))


class DjangoDocumentationMixin(DjangoDocElement):
    def __str__(self):
        return "\n\n\n".join(str(part) for part in self.parts)

    def ___get_tests(self):
        for part in self.parts:
            for chapter in sorted_chapters(part.chapters):
                tests = chapter.doc.get_tests()
                if tests:
                    yield Tests(part.title, chapter.title, "", tests)
                for section in chapter.sections:
                    if section.installed:
                        if isinstance(section, DocGuideSection):
                            for docsection in section.subsections:
                                for docsubsection in docsection.subsections:
                                    # FIXME: Something is weird here
                                    # where tests for subsection items
                                    # appear not as a collection but
                                    # individually and need to be
                                    # iterated below. Probably some
                                    # other code is faulty and when
                                    # fixed the below loop and
                                    # collection into doctest_list[]
                                    # will be removed.
                                    doctest_list = []
                                    index = 1
                                    for doctests in docsubsection.items:
                                        doctest_list += list(doctests.get_tests())
                                        for test in doctest_list:
                                            test.index = index
                                            index += 1

                                    if doctest_list:
                                        yield Tests(
                                            section.chapter.part.title,
                                            section.chapter.title,
                                            docsubsection.title,
                                            doctest_list,
                                        )
                        else:
                            tests = section.doc.get_tests()
                            if tests:
                                yield Tests(
                                    part.title, chapter.title, section.title, tests
                                )
                                pass
                            pass
                        pass
                    pass
                pass
            pass
        return


class MathicsDjangoDocumentation(MathicsMainDocumentation, DjangoDocElement):
    def __init__(self, want_sorting=True):

        self.chapter_class = DjangoDocChapter
        self.doc_dir = settings.DOC_DIR
        self.doc_class = DjangoDocumentationEntry
        self.guide_section_class = DjangoDocGuideSection
        self.part_class = DjangoDocPart
        self.section_class = DjangoDocSection
        self.subsection_class = DjangoDocSubsection
        # Initialize the superclass
        super().__init__(want_sorting)
        # Now, let's load the documentation
        self.load_documentation_sources()
        self.title = "Mathics Documentation"

    def get_uri(self) -> str:
        return "/"

    def search(self, query):
        """Handles interactive search in browser."""

        query = query.strip()
        query_parts = [q.strip().lower() for q in query.split()]

        def matches(text):
            text = text.lower()
            return all(q in text for q in query_parts)

        def name_compare_goodness(result_data):
            exact, item = result_data
            name = item.title
            if exact:
                return -4 if name == query else -3

            if name.startswith(query):
                return -2
            if query in name:
                return -1
            lower_name = name.lower()
            if lower_name.startswith(query):
                return 0
            if lower_name in query:
                return 1
            return 2

        def search_sections(section, result):
            for subsection in section.subsections:
                if matches(subsection.title):
                    result.append((subsection.title == query, subsection))
                elif query == subsection.operator:
                    result.append((True, subsection))

        result = []
        for part in self.parts:
            if matches(part.title):
                result.append((False, part))
            for chapter in sorted_chapters(part.chapters):
                if matches(chapter.title):
                    result.append((False, chapter))
                for section in chapter.all_sections:
                    if matches(section.title):
                        if not isinstance(section, DjangoDocGuideSection):
                            result.append((section.title == query, section))
                    elif query == section.operator:
                        result.append((True, section))
                        continue
                    search_sections(section, result)

        sorted_results = sorted(result, key=name_compare_goodness)
        return sorted_results


class DjangoDocumentationEntry(DocumentationEntry):
    def __init__(self, doc_str: str, title: str, section: Optional["DjangoDocSection"]):
        self.docTest_collection_class = DjangoDocTests
        self.docTest_class = DjangoDocTest
        self.docText_class = DjangoDocText
        super().__init__(doc_str, title, section)

    def __str__(self):
        return "\n".join(str(item) for item in self.items)

    def get_tests(self):
        tests = []
        for item in self.items:
            tests.extend(item.get_tests())
        return tests

    def html(self):
        items = [item for item in self.items if not item.is_private()]
        title_line = self.title + "\n"
        if len(items) and items[0].text.startswith(title_line):
            # In module-style docstring tagging, the first line of the docstring is the section title.
            # since that is tagged and shown as a title, it is redundant here is the section body.
            # Or that is the intent. This code is a bit hacky.
            items[0].text = items[0].text[len(title_line) :]

        text = "\n".join(item.html() for item in items if not item.is_private())
        if text == "":
            # HACK ALERT if text is "" we may have missed some test markup.
            return mark_safe(escape_html(self.rawdoc))
        return mark_safe(text)


class DjangoDocChapter(DocChapter, DjangoDocElement):
    """An object for a Django Documentation Chapter.
    A Chapter is part of a Part and contains Sections.
    """

    def get_collection(self):
        """Return a list of chapters in the part of this chapter."""
        return self.part.chapters

    def get_uri(self) -> str:
        return f"/{self.part.slug}/{self.slug}/"


class DjangoDocPart(DjangoDocElement):
    def __init__(self, doc, title, is_reference=False):
        self.doc = doc
        self.title = title
        self.slug = slugify(title)
        self.chapters = []
        self.chapters_by_slug = {}
        self.is_reference = is_reference
        self.is_appendix = False
        doc.parts_by_slug[self.slug] = self

    def __str__(self):
        return "%s\n\n%s" % (
            self.title,
            "\n".join(str(chapter) for chapter in sorted_chapters(self.chapters)),
        )

    def get_collection(self):
        """Return a list of parts in this doc"""
        return self.doc.parts

    def html(self):
        if len(self.tests) == 0:
            return "\n"
        return '<ul class="tests">%s</ul>' % (
            "\n".join(
                "<li>%s</li>" % test.html() for test in self.tests if not test.private
            )
        )

    def get_uri(self) -> str:
        return f"/{self.slug}/"


class DjangoDocSection(DocSection, DjangoDocElement):
    """An object for a Django Documented Section.
    A Section is part of a Chapter. It can contain subsections.
    """

    def __init__(
        self,
        chapter,
        title: str,
        text: str,
        operator,
        installed=True,
        in_guide=False,
        summary_text="",
    ):
        self.chapter = chapter
        self.in_guide = in_guide
        self.installed = installed
        self.operator = operator
        self.slug = slugify(title)
        self.subsections = []
        self.subsections_by_slug = {}
        self.summary_text = summary_text
        self.title = title

        if text.count("<dl>") != text.count("</dl>"):
            raise ValueError(
                f"Missing opening or closing <dl> tag in {title} documentation"
            )

        # Needs to come after self.chapter is initialized since
        # DocumentationEntry uses self.chapter.
        self.doc = DjangoDocumentationEntry(text, title, self)

        chapter.sections_by_slug[self.slug] = self

    def __str__(self):
        return f"== {self.title} ==\n{self.doc}"

    def get_collection(self):
        """Return a list of subsections for this section that this section belongs
        to."""
        return self.chapter.all_sections

    def html_data(self):
        indices = set()
        for test in self.doc.items:
            indices.update(test.test_indices())
        result = {}
        for index in indices:
            result[index] = doc_data.get(
                (self.chapter.part.title, self.chapter.title, self.title, index)
            )
        return result

    def get_uri(self) -> str:
        """Return the URI of this section."""
        return f"/{self.chapter.part.slug}/{self.chapter.slug}/{self.slug}/"


class DjangoDocGuideSection(DjangoDocSection):
    """An object for a Django Documented Guide Section.
    A Guide Section is part of a Chapter. "Colors" or "Special Functions"
    are examples of Guide Sections, and each contains a number of Sections.
    like NamedColors or Orthogonal Polynomials.
    """

    def __init__(
        self, chapter: str, title: str, text: str, submodule, installed: bool = True
    ):
        self.chapter = chapter
        self.doc = DjangoDocumentationEntry(text, title, None)
        self.in_guide = False
        self.installed = installed
        self.slug = slugify(title)
        self.section = submodule
        self.slug = slugify(title)
        self.subsections = []
        self.subsections_by_slug = {}
        self.title = title

        # FIXME: Sections never are operators. Subsections can have
        # operators though.  Fix up the view and searching code not to
        # look for the operator field of a section.
        self.operator = False

        if text.count("<dl>") != text.count("</dl>"):
            raise ValueError(
                f"Missing opening or closing <dl> tag in {title} documentation"
            )
        # print("YYY Adding section", title)
        chapter.sections_by_slug[self.slug] = self

    def get_uri(self) -> str:
        """Return the URI of this section."""
        return f"/{self.chapter.part.slug}/{self.chapter.slug}/guide/"


class DjangoDocSubsection(DocSubsection, DjangoDocElement):
    """An object for a Django Documented Subsection.
    A Subsection is part of a Section.
    """

    def __init__(
        self,
        chapter,
        section,
        title,
        text,
        operator=None,
        installed=True,
        in_guide=False,
        summary_text="",
    ):
        """
        Information that goes into a subsection object. This can be a written text, or
        text extracted from the docstring of a builtin module or class.

        About some of the parameters...

        Some built-in classes are Operators. These are documented in a
        slightly special way.

        Some built-in require special libraries. When those libraries are not available,
        parameter "installed" is False.

        Some of the subsections are contained in a grouping module and need special work to
        get the grouping module name correct.

        For example the Chapter "Colors" is a module so the docstring
        text for it is in mathics/builtin/colors/__init__.py . In
        mathics/builtin/colors/named-colors.py we have the "section"
        name for the class Read (the subsection) inside it.
        """
        super().__init__(
            chapter, section, title, text, operator, installed, in_guide, summary_text
        )
        self.doc = DjangoDocumentationEntry(text, title, section)
        return
        # Check if any of this is actually needed.
        title_summary_text = re.split(" -- ", title)
        n = len(title_summary_text)
        self.title = title_summary_text[0] if n > 0 else ""
        self.summary_text = title_summary_text[1] if n > 1 else summary_text

        self.doc = DjangoDocumentationEntry(text, title, section)
        self.chapter = chapter
        self.installed = installed
        self.operator = operator

        self.section = section
        self.slug = slugify(title)
        self.title = title

        if section:
            chapter = section.chapter
            part = chapter.part
            # Note: we elide section.title
            key_prefix = (part.title, chapter.title, title)
        else:
            key_prefix = None

        if in_guide:
            # Tests haven't been picked out yet from the doc string yet.
            # Gather them here.
            self.items = gather_tests(
                text, DjangoDocTests, DjangoDocTest, DjangoDocText, key_prefix
            )
        else:
            self.items = []

        if text.count("<dl>") != text.count("</dl>"):
            raise ValueError(
                f"Missing opening or closing <dl> tag in {title} documentation"
            )
        self.section.subsections_by_slug[self.slug] = self

    def __str__(self):
        return f"=== {self.title} ===\n{self.doc}"

    def get_collection(self) -> str:
        """Return a list of subsections of the section."""
        return self.section.subsections

    def html_data(self):
        indices = set()
        for test in self.doc.items:
            indices.update(test.test_indices())
        result = {}
        for index in indices:
            result[index] = doc_data.get(
                (self.chapter.part.title, self.chapter.title, self.title, index)
            )
        return result

    def get_uri(self) -> str:
        """Return the URI of this subsection."""
        return (
            f"/{self.chapter.part.slug}/{self.chapter.slug}/{self.section.slug}/"
            f"{self.slug}/"
        )


class DjangoDocTest(DocTest):
    """
    See DocTest for formatting rules.
    """

    def html(self) -> str:
        result = '<div class="test"><span class="move"></span>'
        result += f'<ul class="test" id="test_{self.index}">'

        result += f'<li class="test">{escape_html(self.test, True)}</li>'

        if self.key is None:
            result += "</ul>"
            result += "</div>"
            return result

        output_for_key = doc_data.get(self.key, None)
        # HACK ALERT:
        # output_for_key is not None, then the output appears
        # mysteriously some other way.
        # But if it is None then test number don't line up and that is a different
        # bug that we address here.
        if output_for_key is None:
            output_for_key = get_results_by_test(self.test, self.key, doc_data)
            results = output_for_key.get("results", [])
            result += '<ul class="out">'
            for r in results:
                for out in r["out"]:
                    result += f'<li class="out">{escape_html(out["text"])}</li>'
                if r["result"]:  # is not None and result['result'].strip():
                    result += f'<li class="result">{r["result"]}</li>'
            result += "</ul>"

        result += "</ul>"
        result += "</div>"
        return result


class DjangoDocTests(DocTests):
    def html(self):
        if len(self.tests) == 0:
            return "\n"
        return '<ul class="tests">%s</ul>' % (
            "\n".join(
                "<li>%s</li>" % test.html() for test in self.tests if not test.private
            )
        )


class DjangoDocText(DocText):
    def html(self) -> str:
        result = escape_html(self.text)
        return result
