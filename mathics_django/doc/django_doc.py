# -*- coding: utf-8 -*-
"""
A module which extracts XML documentation from documentation/*.mdoc and from Mathics modules.

Viewing extracted XML docs is elswhere.

FIXME: Too much of this code is duplicated from Mathics Core.
This code should be replaced by sphinx and autodoc.
"""

from os import getenv, listdir
import importlib

from django.utils.safestring import mark_safe

from mathics import builtin, settings
from mathics.builtin import get_module_doc
from mathics.core.evaluation import Message, Print

from mathics_django.doc.utils import escape_html, slugify
from mathics_django.settings import DOC_XML_DATA_PATH

from mathics.doc.common_doc import (
    CHAPTER_RE,
    DocElement,
    END_LINE_SENTINAL,
    PYTHON_RE,
    SECTION_RE,
    TESTCASE_OUT_RE,
    TESTCASE_RE,
    Tests,
    filter_comments,
    post_sub,
    pre_sub,
    strip_system_prefix,
)

import pickle

try:
    with open(DOC_XML_DATA_PATH, "rb") as xml_data_file:
        xml_data = pickle.load(xml_data_file)
except IOError:
    print(f"Trouble reading Doc XML file {DOC_XML_DATA_PATH}")
    xml_data = {}


class DjangoDocElement(DocElement):
    def href(self, ajax=False):
        if ajax:
            return "javascript:loadDoc('%s')" % self.get_url()
        else:
            return "/doc%s" % self.get_url()

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
        """for part in self.parts:
            if part.slug == part_slug:
                for chapter in self:
                    pass"""

    def get_section(self, part_slug, chapter_slug, section_slug):
        part = self.parts_by_slug.get(part_slug)
        if part:
            chapter = part.chapters_by_slug.get(chapter_slug)
            if chapter:
                return chapter.sections_by_slug.get(section_slug)
        return None

    def get_tests(self):
        for part in self.parts:
            for chapter in part.chapters:
                tests = chapter.doc.get_tests()
                if tests:
                    yield Tests(part.title, chapter.title, "", tests)
                for section in chapter.sections:
                    if section.installed:
                        tests = section.doc.get_tests()
                        if tests:
                            yield Tests(part.title, chapter.title, section.title, tests)

    def get_url(self):
        return "/"

    def search(self, query):
        query = query.strip()
        query_parts = [q.strip().lower() for q in query.split()]

        def matches(text):
            text = text.lower()
            return all(q in text for q in query_parts)

        result = []
        for part in self.parts:
            if matches(part.title):
                result.append((False, part))
            for chapter in part.chapters:
                if matches(chapter.title):
                    result.append((False, chapter))
                for section in chapter.sections:
                    if matches(section.title):
                        result.append((section.title == query, section))
                    elif query == section.operator:
                        result.append((True, section))
        return result


class MathicsMainDocumentation(Documentation):
    def __init__(self):
        self.title = "Overview"
        self.parts = []
        self.parts_by_slug = {}
        self.pymathics_doc_loaded = False
        self.xml_data_file = DOC_XML_DATA_PATH
        self.doc_dir = settings.DOC_DIR
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
            for module in modules:
                # FIXME add an additional mechanism in the module
                # to allow a docstring and indicate it is not to go in the
                # user manual
                if module.__doc__ is None:
                    continue
                title, text = get_module_doc(module)
                chapter = DjangoDocChapter(builtin_part, title, DjangoDoc(text))
                builtins = builtins_by_module[module.__name__]
                # FIXME: some Box routines, like RowBox *are*
                # documented
                section_names = [
                    builtin
                    for builtin in builtins
                    if not builtin.__class__.__name__.endswith("Box")
                ]
                for instance in section_names:
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
                    if instance.__doc__ is None:
                        continue
                    section = DjangoDocSection(
                        chapter,
                        strip_system_prefix(instance.get_name()),
                        instance.__doc__ or "",
                        operator=instance.get_operator(),
                        installed=installed,
                    )
                    chapter.sections.append(section)
                builtin_part.chapters.append(chapter)
            self.parts.append(builtin_part)

        for part in appendix:
            self.parts.append(part)

        # set keys of tests
        for tests in self.get_tests():
            for test in tests.tests:
                test.key = (tests.part, tests.chapter, tests.section, test.index)

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
        self.xml_data_file = None
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
        self.xml_data_file = self.doc_dir + "xml/data"
        self.tex_data_file = self.doc_dir + "tex/data"

        # Load the dictionary of mathics symbols defined in the module
        self.symbols = {}
        from mathics.builtin import is_builtin, Builtin

        print("loading symbols")
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
            self.xml_data_file = ""
            self.tex_data_file = ""
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

        # Builds the automatic documentation
        builtin_part = DjangoDocPart(self, "Pymathics Modules", is_reference=True)
        title, text = get_module_doc(self.pymathicsmodule)
        chapter = DjangoDocChapter(builtin_part, title, DjangoDoc(text))
        for name in self.symbols:
            instance = self.symbols[name]
            installed = True
            for package in getattr(instance, "requires", []):
                try:
                    importlib.import_module(package)
                except ImportError:
                    installed = False
                    break
            section = DjangoDocSection(
                chapter,
                strip_system_prefix(name),
                instance.__doc__ or "",
                operator=instance.get_operator(),
                installed=installed,
            )
            chapter.sections.append(section)
        builtin_part.chapters.append(chapter)
        self.parts.append(builtin_part)
        # Adds possible appendices
        for part in appendix:
            self.parts.append(part)

        # set keys of tests
        for tests in self.get_tests():
            for test in tests.tests:
                test.key = (tests.part, tests.chapter, tests.section, test.index)


class DjangoDoc(object):
    def __init__(self, doc):
        self.items = []
        # remove commented lines
        doc = filter_comments(doc)
        # pre-substitute Python code because it might contain tests
        doc, post_substitutions = pre_sub(
            PYTHON_RE, doc, lambda m: "<python>%s</python>" % m.group(1)
        )
        # HACK: Artificially construct a last testcase to get the "intertext"
        # after the last (real) testcase. Ignore the test, of course.
        doc += "\n>> test\n = test"
        testcases = TESTCASE_RE.findall(doc)
        tests = None
        for index in range(len(testcases)):
            testcase = list(testcases[index])
            text = testcase.pop(0).strip()
            if text:
                if tests is not None:
                    self.items.append(tests)
                    tests = None
                text = post_sub(text, post_substitutions)
                self.items.append(DjangoDocText(text))
                tests = None
            if index < len(testcases) - 1:
                test = DjangoDocTest(index, testcase)
                if tests is None:
                    tests = DjangoDocTests()
                tests.tests.append(test)
            if tests is not None:
                self.items.append(tests)
                tests = None

    def __str__(self):
        return "\n".join(str(item) for item in self.items)

    def text(self, detail_level):
        # used for introspection
        # TODO parse XML and pretty print
        # HACK
        item = str(self.items[0])
        item = "\n".join(line.strip() for line in item.split("\n"))
        item = item.replace("<dl>", "")
        item = item.replace("</dl>", "")
        item = item.replace("<dt>", "  ")
        item = item.replace("</dt>", "")
        item = item.replace("<dd>", "    ")
        item = item.replace("</dd>", "")
        item = "\n".join(line for line in item.split("\n") if not line.isspace())
        return item

    def get_tests(self):
        tests = []
        for item in self.items:
            tests.extend(item.get_tests())
        return tests

    def html(self):
        counters = {}
        return mark_safe(
            "\n".join(
                item.html(counters) for item in self.items if not item.is_private()
            )
        )


class DjangoDocChapter(DjangoDocElement):
    """An object for a Django Documentation Chapter.
    A Chapter is part of a Part and contains Sections.
    """

    def __init__(self, part, title, doc=None):
        self.part = part
        self.title = title
        self.slug = slugify(title)
        self.doc = doc
        self.sections = []
        self.sections_by_slug = {}
        part.chapters_by_slug[self.slug] = self

    def __str__(self):
        sections = "\n".join(str(section) for section in self.sections)
        return f"= {self.title} =\n\n{sections}"

    def get_collection(self):
        return self.part.chapters

    def get_url(self):
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
        return self.doc.parts

    def html(self, counters=None):
        if len(self.tests) == 0:
            return "\n"
        return '<ul class="tests">%s</ul>' % (
            "\n".join(
                "<li>%s</li>" % test.html() for test in self.tests if not test.private
            )
        )

    def get_url(self):
        return f"/{self.slug}/"


class DjangoDocSection(DjangoDocElement):
    """An object for a Django Documented Section.
    A Section is part of a Chapter. In the future it can contain subsections.
    """

    def __init__(self, chapter, title, text, operator=None, installed=True):
        self.chapter = chapter
        self.title = title
        self.slug = slugify(title)
        if text.count("<dl>") != text.count("</dl>"):
            raise ValueError(
                "Missing opening or closing <dl> tag in "
                "{} documentation".format(title)
            )
        self.doc = DjangoDoc(text)
        self.operator = operator
        self.installed = installed
        chapter.sections_by_slug[self.slug] = self

    def __str__(self):
        return f"== {self.title} ==\n{self.doc}"

    def get_collection(self):
        return self.chapter.sections

    def html_data(self):
        indices = set()
        for test in self.doc.items:
            indices.update(test.test_indices())
        result = {}
        for index in indices:
            result[index] = xml_data.get(
                (self.chapter.part.title, self.chapter.title, self.title, index)
            )
        return result

    def get_url(self):
        return f"/{self.chapter.part.slug}/{self.chapter.slug}/{self.slug}/"


class DjangoDocTest(object):
    """
    DocTest formatting rules:

    * `>>` Marks test case; it will also appear as part of
           the documentation.
    * `#>` Marks test private or one that does not appear as part of
           the documentation.
    * `X>` Shows the example in the docs, but disables testing the example.
    * `S>` Shows the example in the docs, but disables testing if environment
           variable SANDBOX is set.
    * `=`  Compares the result text.
    * `:`  Compares an (error) message.
      `|`  Prints output.
    """

    def __init__(self, index, testcase):
        def strip_sentinal(line):
            """Remove END_LINE_SENTINAL from the end of a line if it appears.

            Some editors like to strip blanks at the end of a line.
            Since the line ends in END_LINE_SENTINAL which isn't blank,
            any blanks that appear before will be preserved.

            Some tests require some lines to be blank or entry because
            Mathics output can be that way
            """
            if line.endswith(END_LINE_SENTINAL):
                line = line[: -len(END_LINE_SENTINAL)]

            # Also remove any remaining trailing blanks since that
            # seems *also* what we want to do.
            return line.strip()

        self.index = index
        self.result = None
        self.outs = []

        # Private test cases are executed, but NOT shown as part of the docs
        self.private = testcase[0] == "#"

        # Ignored test cases are NOT executed, but shown as part of the docs
        # Sandboxed test cases are NOT executed if environtment SANDBOX is set
        if testcase[0] == "X" or (testcase[0] == "S" and getenv("SANDBOX", False)):
            self.ignore = True
            # substitute '>' again so we get the correct formatting
            testcase[0] = ">"
        else:
            self.ignore = False

        self.test = strip_sentinal(testcase[1])

        self.key = None
        outs = testcase[2].splitlines()
        for line in outs:
            line = strip_sentinal(line)
            if line:
                if line.startswith("."):
                    text = line[1:]
                    if text.startswith(" "):
                        text = text[1:]
                    text = "\n" + text
                    if self.result is not None:
                        self.result += text
                    elif self.outs:
                        self.outs[-1].text += text
                    continue

                match = TESTCASE_OUT_RE.match(line)
                symbol, text = match.group(1), match.group(2)
                text = text.strip()
                if symbol == "=":
                    self.result = text
                elif symbol == ":":
                    out = Message("", "", text)
                    self.outs.append(out)
                elif symbol == "|":
                    out = Print(text)
                    self.outs.append(out)

    def __str__(self):
        return self.test

    def html(self):
        result = '<div class="test"><span class="move"></span>'
        result += '<ul class="test" id="test_%d">' % self.index
        result += '<li class="test">%s</li>' % escape_html(self.test, True)
        result += "</ul>"
        result += "</div>"
        return result


class DjangoDocTests(object):
    def __init__(self):
        self.tests = []

    def get_tests(self):
        return self.tests

    def is_private(self):
        return all(test.private for test in self.tests)

    def __str__(self):
        return "\n".join(str(test) for test in self.tests)

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
