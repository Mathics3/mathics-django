# -*- coding: utf-8 -*-
"""
A module and library that assists in organizing document data
previously obtained from static files and Python module/class doc
strings. This data is stored in a way that facilitates viewing
documentation.

As with reading in data, viewing extracted document information is
documentation tests is done elsewhere.

FIXME: Too much of this code is duplicated from Mathics Core.
More importantly, this code should be replaced by Sphinx and autodoc.
"""

from os import listdir
from types import ModuleType
import importlib

from django.utils.safestring import mark_safe

from mathics import builtin, settings
from mathics.builtin import get_module_doc

from mathics_django.doc.utils import escape_html, slugify
from mathics_django.settings import DOC_DATA_PATH

from mathics.doc.common_doc import (
    CHAPTER_RE,
    DocGuideSection,
    DocTest,
    DocTests,
    PYTHON_RE,
    SECTION_RE,
    SUBSECTION_RE,
    TESTCASE_RE,
    XMLDoc,
    Tests,
    filter_comments,
    post_sub,
    pre_sub,
)

import pickle

# FIXME: remove globalness
try:
    with open(DOC_DATA_PATH, "rb") as doc_data_file:
        doc_data = pickle.load(doc_data_file)
except IOError:
    print(f"Trouble reading Doc file {DOC_DATA_PATH}")
    doc_data = {}


def get_doc_name_from_module(module):
    name = "???"
    if module.__doc__:
        lines = module.__doc__.strip()
        if not lines:
            name = module.__name__
        else:
            name = lines.split("\n")[0]
    return name


class DjangoDocElement(object):
    def href(self, ajax=False):
        if ajax:
            return "javascript:loadDoc('%s')" % self.get_uri()
        else:
            return "/doc%s" % self.get_uri()

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


class Documentation(DjangoDocElement):
    def __str__(self):
        return "\n\n\n".join(str(part) for part in self.parts)

    def get_part(self, part_slug):
        return self.parts_by_slug.get(part_slug)

    def get_chapter(self, part_slug, chapter_slug):
        part = self.parts_by_slug.get(part_slug)
        if part:
            return part.chapters_by_slug.get(chapter_slug)
        return None

    def get_section(self, part_slug, chapter_slug, section_slug):
        part = self.parts_by_slug.get(part_slug)
        if part:
            chapter = part.chapters_by_slug.get(chapter_slug)
            if chapter:
                return chapter.sections_by_slug.get(section_slug)
        return None

    def get_subsection(self, part_slug, chapter_slug, section_slug, subsection_slug):
        part = self.parts_by_slug.get(part_slug)
        if part:
            chapter = part.chapters_by_slug.get(chapter_slug)
            if chapter:
                section = chapter.sections_by_slug.get(section_slug)
                if section:
                    return section.subsections_by_slug.get(subsection_slug)

        return None

    def get_tests(self):
        for part in self.parts:
            for chapter in part.chapters:
                tests = chapter.doc.get_tests()
                if tests:
                    yield Tests(part.title, chapter.title, "", tests)
                for section in chapter.sections:
                    if section.installed:
                        if isinstance(section, DocGuideSection):
                            for docsection in section.subsections:
                                for docsubsection in docsection.subsections:
                                    # FIXME: Something is weird here where tests for subsection items
                                    # appear not as a collection but individually and need to be
                                    # iterated below. Probably some other code is faulty and
                                    # when fixed the below loop and collection into doctest_list[]
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
            for chapter in part.chapters:
                if matches(chapter.title):
                    result.append((False, chapter))
                for section in chapter.sections:
                    if matches(section.title):
                        if not isinstance(section, DjangoDocGuideSection):
                            result.append((section.title == query, section))
                    elif query == section.operator:
                        result.append((True, section))
                        continue
                    search_sections(section, result)

        sorted_results = sorted(result, key=name_compare_goodness)
        return sorted_results


class MathicsMainDocumentation(Documentation):
    def __init__(self):
        self.doc_data_file = DOC_DATA_PATH
        self.doc_dir = settings.DOC_DIR
        self.parts = []
        self.parts_by_slug = {}
        self.pymathics_doc_loaded = False
        self.title = "Overview"
        files = listdir(self.doc_dir)
        files.sort()
        appendix = []

        for file in files:
            part_title = file[2:]
            if part_title.endswith(".mdoc"):
                part_title = part_title[: -len(".mdoc")]
                part = DjangoDocPart(self, part_title)
                text = open(self.doc_dir + file, "rb").read().decode("utf8")
                text = filter_comments(text)
                chapters = CHAPTER_RE.findall(text)
                for title, text in chapters:
                    chapter = DjangoDocChapter(part, title)
                    text += '<section title=""></section>'
                    sections = SECTION_RE.findall(text)
                    for pre_text, title, text in sections:
                        if title:
                            section = DjangoDocSection(
                                chapter, title, text, operator=None, installed=True
                            )
                            chapter.sections.append(section)
                            subsections = SUBSECTION_RE.findall(text)
                            for subsection_title in subsections:
                                subsection = DjangoDocSubsection(
                                    chapter,
                                    section,
                                    subsection_title,
                                    text,
                                )
                                section.subsections.append(subsection)
                                pass
                            pass
                        else:
                            section = None
                        if not chapter.doc:
                            chapter.doc = DjangoDoc(pre_text, title, section)
                        pass

                    part.chapters.append(chapter)
                if file[0].isdigit():
                    self.parts.append(part)
                else:
                    part.is_appendix = True
                    appendix.append(part)

        for title, modules, builtins_by_module, start in [
            (
                "Reference of Built-in Symbols",
                builtin.modules,
                builtin.builtins_by_module,
                True,
            )
        ]:  # nopep8
            # ("Reference of optional symbols", optional.modules,
            #  optional.optional_builtins_by_module, False)]:

            builtin_part = DjangoDocPart(self, title, is_reference=start)
            modules_seen = set([])
            for module in modules:
                # FIXME add an additional mechanism in the module
                # to allow a docstring and indicate it is not to go in the
                # user manual
                if module.__doc__ is None:
                    continue
                if module in modules_seen:
                    continue
                title, text = get_module_doc(module)
                chapter = DjangoDocChapter(builtin_part, title, DjangoDoc(text, title, None))
                builtins = builtins_by_module[module.__name__]
                # FIXME: some Box routines, like RowBox *are*
                # documented
                sections = [
                    builtin
                    for builtin in builtins
                    if not builtin.__class__.__name__.endswith("Box")
                ]

                if module.__file__.endswith("__init__.py"):
                    # We have a Guide Section.
                    name = get_doc_name_from_module(module)
                    self.add_section(
                        chapter, name, module, operator=None, is_guide=True
                    )
                    submodules = [
                        value
                        for value in module.__dict__.values()
                        if isinstance(value, ModuleType)
                    ]

                    # Add sections in the guide section...
                    for submodule in submodules:
                        # FIXME add an additional mechanism in the module
                        # to allow a docstring and indicate it is not to go in the
                        # user manual
                        if submodule.__doc__ is None:
                            continue
                        if submodule in modules_seen:
                            continue

                        section = self.add_section(
                            chapter,
                            get_doc_name_from_module(submodule),
                            submodule,
                            operator=None,
                            is_guide=False,
                        )
                        modules_seen.add(submodule)

                        builtins = builtins_by_module[submodule.__name__]
                        subsections = [
                            builtin
                            for builtin in builtins
                            if not builtin.__class__.__name__.endswith("Box")
                        ]
                        for instance in subsections:
                            modules_seen.add(instance)
                            name = instance.get_name(short=True)
                            self.add_subsection(
                                chapter,
                                section,
                                instance.get_name(short=True),
                                instance,
                                instance.get_operator(),
                            )
                else:
                    for instance in sections:
                        if instance not in modules_seen:
                            name = instance.get_name(short=True)
                            self.add_section(
                                chapter,
                                instance.get_name(short=True),
                                instance,
                                instance.get_operator(),
                                is_guide=False,
                            )
                            modules_seen.add(instance)
                builtin_part.chapters.append(chapter)
            self.parts.append(builtin_part)

        for part in appendix:
            self.parts.append(part)

        # set keys of tests
        for tests in self.get_tests():
            for test in tests.tests:
                test.key = (tests.part, tests.chapter, tests.section, test.index)

    def add_section(
        self,
        chapter,
        section_name: str,
        section_object,
        operator,
        is_guide: bool = False,
    ):
        """
        Adds a DjangoDocSection or DangoDocGuideSection
        object to the chapter, a DjangoDocChapter object.
        "section_object" is either a Python module or a Class object instance.
        """
        installed = True
        for package in getattr(section_object, "requires", []):
            try:
                importlib.import_module(package)
            except ImportError:
                installed = False
                break
        # FIXME add an additional mechanism in the module
        # to allow a docstring and indicate it is not to go in the
        # user manual
        if not section_object.__doc__:
            return
        if is_guide:
            section = DjangoDocGuideSection(
                chapter,
                section_name,
                section_object.__doc__,
                section_object,
                installed=installed,
            )
            chapter.guide_sections.append(section)
        else:
            section = DjangoDocSection(
                chapter,
                section_name,
                section_object.__doc__,
                operator=operator,
                installed=installed,
            )
            chapter.sections.append(section)

        return section

    def add_subsection(
        self, chapter, section, subsection_name: str, instance, operator=None
    ):
        installed = True
        for package in getattr(instance, "requires", []):
            try:
                importlib.import_module(package)
            except ImportError:
                installed = False
                break

        # FIXME add an additional mechanism in the module
        # to allow a docstring and indicate it is not to go in the
        # user manual
        if not instance.__doc__:
            return
        subsection = DjangoDocSubsection(
            chapter,
            section,
            subsection_name,
            instance.__doc__,
            operator=operator,
            installed=installed,
        )
        section.subsections.append(subsection)

    def load_pymathics_doc(self):
        if self.pymathics_doc_loaded:
            return
        from mathics.settings import default_pymathics_modules

        pymathicspart = None
        # Look the "Pymathics Modules" part, and if it does not exist, create it.
        for part in self.parts:
            if part.title == "Pymathics Modules":
                pymathicspart = part
        if pymathicspart is None:
            pymathicspart = DjangoDocPart(self, "Pymathics Modules", is_reference=True)
            self.parts.append(pymathicspart)

        # For each module, create the documentation object and load the chapters in the pymathics part.
        for pymmodule in default_pymathics_modules:
            pymathicsdoc = PyMathicsDocumentation(pymmodule)
            for part in pymathicsdoc.parts:
                for ch in part.chapters:
                    ch.title = f"{pymmodule} {part.title} {ch.title}"
                    ch.part = pymathicspart
                    pymathicspart.chapters_by_slug[ch.slug] = ch
                    pymathicspart.chapters.append(ch)

        self.pymathics_doc_loaded = True


class PyMathicsDocumentation(Documentation):
    def __init__(self, module=None):
        self.title = "Overview"
        self.parts = []
        self.parts_by_slug = {}
        self.doc_dir = None
        self.doc_data_file = None
        self.symbols = {}
        if module is None:
            return

        import importlib

        # Load the module and verifies it is a pymathics module
        try:
            self.pymathicsmodule = importlib.import_module(module)
        except ImportError:
            print("Module does not exist")
            self.pymathicsmodule = None
            self.parts = []
            return

        try:
            if "name" in self.pymathicsmodule.pymathics_version_data:
                self.name = self.version = self.pymathicsmodule.pymathics_version_data[
                    "name"
                ]
            else:
                self.name = (self.pymathicsmodule.__package__)[10:]
            self.version = self.pymathicsmodule.pymathics_version_data["version"]
            self.author = self.pymathicsmodule.pymathics_version_data["author"]
        except (AttributeError, KeyError, IndexError):
            print(module + " is not a pymathics module.")
            self.pymathicsmodule = None
            self.parts = []
            return

        # Paths
        self.doc_dir = self.pymathicsmodule.__path__[0] + "/doc/"
        self.doc_data_file = self.doc_dir + "xml/data"

        # Load the dictionary of mathics symbols defined in the module
        self.symbols = {}
        from mathics.builtin import is_builtin, Builtin

        for name in dir(self.pymathicsmodule):
            var = getattr(self.pymathicsmodule, name)
            if (
                hasattr(var, "__module__")
                and var.__module__ != "mathics.builtin.base"
                and is_builtin(var)
                and not name.startswith("_")
                and var.__module__[: len(self.pymathicsmodule.__name__)]
                == self.pymathicsmodule.__name__
            ):  # nopep8
                instance = var(expression=False)
                if isinstance(instance, Builtin):
                    self.symbols[instance.get_name()] = instance
        # Defines de default first part, in case we are building an independent documentation module.
        self.title = "Overview"
        self.parts = []
        self.parts_by_slug = {}
        try:
            files = listdir(self.doc_dir)
            files.sort()
        except FileNotFoundError:
            self.doc_dir = ""
            self.doc_data_file = ""
            files = []
        appendix = []
        for file in files:
            part_title = file[2:]
            if part_title.endswith(".mdoc"):
                part_title = part_title[: -len(".mdoc")]
                part = DjangoDocPart(self, part_title)
                text = open(self.doc_dir + file, "rb").read().decode("utf8")
                text = filter_comments(text)
                chapters = CHAPTER_RE.findall(text)
                for title, text in chapters:
                    chapter = DjangoDocChapter(part, title)
                    text += '<section title=""></section>'
                    sections = SECTION_RE.findall(text)
                    for pre_text, title, text in sections:
                        if not chapter.doc:
                            chapter.doc = DjangoDoc(pre_text)
                        if title:
                            section = DjangoDocSection(chapter, title, text)
                            chapter.sections.append(section)
                    part.chapters.append(chapter)
                if file[0].isdigit():
                    self.parts.append(part)
                else:
                    part.is_appendix = True
                    appendix.append(part)

        # Adds possible appendices
        for part in appendix:
            self.parts.append(part)

        # set keys of tests
        for tests in self.get_tests():
            for test in tests.tests:
                test.key = (tests.part, tests.chapter, tests.section, test.index)


def gather_tests(doc: str, key_part=None) -> list:
    # Remove commented lines.
    doc = filter_comments(doc).strip(r"\s")

    # Remove leading <dl>...</dl>
    # doc = DL_RE.sub("", doc)

    # pre-substitute Python code because it might contain tests
    doc, post_substitutions = pre_sub(
        PYTHON_RE, doc, lambda m: "<python>%s</python>" % m.group(1)
    )

    # HACK: Artificially construct a last testcase to get the "intertext"
    # after the last (real) testcase. Ignore the test, of course.
    doc += "\n>> test\n = test"
    testcases = TESTCASE_RE.findall(doc)

    tests = None
    items = []
    for index in range(len(testcases)):
        testcase = list(testcases[index])
        text = testcase.pop(0).strip()
        if text:
            if tests is not None:
                items.append(tests)
                tests = None
            text = post_sub(text, post_substitutions)
            items.append(DjangoDocText(text))
            tests = None
        if index < len(testcases) - 1:
            test = DjangoDocTest(index, testcase, key_part)
            if tests is None:
                tests = DjangoDocTests()
            tests.tests.append(test)
        if tests is not None:
            items.append(tests)
            tests = None
    return items


class DjangoDoc(XMLDoc):
    def __init__(self, doc, title, section):
        self.title = title
        if section:
            chapter = section.chapter
            part = chapter.part
            # Note: we elide section.title
            key_prefix = (part.title, chapter.title, title)
        else:
            key_prefix = None

        self.items = gather_tests(doc, key_prefix)

    def __str__(self):
        return "\n".join(str(item) for item in self.items)

    def get_tests(self):
        tests = []
        for item in self.items:
            tests.extend(item.get_tests())
        return tests

    def html(self):
        counters = {}
        items = [item for item in self.items if not item.is_private()]
        if len(items) and items[0].text.startswith(self.title):
            # In module-style docstring tagging, the first line of the docstring is the section title.
            # since that is tagged and shown as a title, it is redundant here is the section body.
            # Or that is the intent. This code is a bit hacky.
            items = items[1:]
        return mark_safe(
            "\n".join(item.html(counters) for item in items if not item.is_private())
        )


class DjangoDocChapter(DjangoDocElement):
    """An object for a Django Documentation Chapter.
    A Chapter is part of a Part and contains Sections.
    """

    def __init__(self, part: str, title: str, doc=None):
        self.doc = doc
        self.guide_sections = []
        self.part = part
        self.sections = []
        self.sections_by_slug = {}
        self.slug = slugify(title)
        self.title = title
        part.chapters_by_slug[self.slug] = self

    def __str__(self):
        sections = "\n".join(str(section) for section in self.sections)
        return f"= {self.title} =\n\n{sections}"

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
            "\n".join(str(chapter) for chapter in self.chapters),
        )

    def get_collection(self):
        """Return a list of parts in this doc"""
        return self.doc.parts

    def html(self, counters=None):
        if len(self.tests) == 0:
            return "\n"
        return '<ul class="tests">%s</ul>' % (
            "\n".join(
                "<li>%s</li>" % test.html() for test in self.tests if not test.private
            )
        )

    def get_uri(self) -> str:
        return f"/{self.slug}/"


class DjangoDocSection(DjangoDocElement):
    """An object for a Django Documented Section.
    A Section is part of a Chapter. It can contain subsections.
    """

    def __init__(
        self, chapter, section_title: str, text: str, operator, installed=True
    ):
        self.chapter = chapter
        self.installed = installed
        self.operator = operator
        self.slug = slugify(section_title)
        self.subsections = []
        self.subsections_by_slug = {}
        self.title = section_title

        if text.count("<dl>") != text.count("</dl>"):
            raise ValueError(
                "Missing opening or closing <dl> tag in "
                "{} documentation".format(section_title)
            )

        # Needs to come after self.chapter is initialized since
        # XMLDoc uses self.chapter.
        self.doc = DjangoDoc(text, section_title, self)

        chapter.sections_by_slug[self.slug] = self

    def __str__(self):
        return f"== {self.title} ==\n{self.doc}"

    def get_collection(self):
        """Return a list of subsections for this sectione chapter this section belongs to."""
        return self.chapter.sections

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
        self.doc = DjangoDoc(text, title, None)
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
                "Missing opening or closing <dl> tag in "
                "{} documentation".format(title)
            )
        # print("YYY Adding section", title)
        chapter.sections_by_slug[self.slug] = self

    def get_uri(self) -> str:
        """Return the URI of this section."""
        return f"/{self.chapter.part.slug}/{self.chapter.slug}/guide/"


class DjangoDocSubsection(DjangoDocElement):
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

        For example the Chapter "Colors" is a module so the docstring text for it is in
        mathics/builtin/colors/__init__.py . In mathics/builtin/colors/named-colors.py we have
        the "section" name for the class Read (the subsection) inside it.
        """

        self.doc = DjangoDoc(text, title, section)
        self.chapter = chapter
        self.installed = installed
        self.operator = operator

        self.section = section
        self.slug = slugify(title)
        self.title = title
        if text.count("<dl>") != text.count("</dl>"):
            raise ValueError(
                "Missing opening or closing <dl> tag in "
                "{} documentation".format(title)
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
        return f"/{self.chapter.part.slug}/{self.chapter.slug}/{self.section.slug}/{self.slug}/"


class DjangoDocTest(DocTest):
    """
    See DocTest for formatting rules.
    """
    def html(self) -> str:
        result = '<div class="test"><span class="move"></span>'
        result += '<ul class="test" id="test_%d">' % self.index
        result += '<li class="test">%s</li>' % escape_html(self.test, True)
        result += "</ul>"
        result += "</div>"
        return result


class DjangoDocTests(DocTests):
    def __init__(self):
        self.tests = []
        self.text = ""

    def html(self, counters=None):
        if len(self.tests) == 0:
            return "\n"
        return '<ul class="tests">%s</ul>' % (
            "\n".join(
                "<li>%s</li>" % test.html() for test in self.tests if not test.private
            )
        )

    def test_indices(self):
        return [test.index for test in self.tests]


class DjangoDocText(object):
    def __init__(self, text):
        self.text = text

    def get_tests(self):
        return []

    def is_private(self):
        return False

    def __str__(self):
        return self.text

    def html(self, counters=None):
        result = escape_html(self.text, counters=counters)
        return result

    def test_indices(self):
        return []
