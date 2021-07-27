#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import unicodedata

from django.utils.html import linebreaks

from mathics.doc.common_doc import (
    ALLOWED_TAGS,
    ALLOWED_TAGS_RE,
    CONSOLE_RE,
    DL_ITEM_RE,
    DL_RE,
    HYPERTEXT_RE,
    LATEX_RE,
    LIST_ITEM_RE,
    LIST_RE,
    MATHICS_RE,
    post_sub,
    pre_sub,
    IMG_PNG_RE,
    IMG_RE,
    REF_RE,
    PYTHON_RE,
    QUOTATIONS_RE,
    SPECIAL_COMMANDS,
    SUBSECTION_END_RE,
    SUBSECTION_RE,
    _replace_all,
)


def slugify(value):
    """
    Converts to lowercase, removes non-word characters apart from '$',
    and converts spaces to hyphens. Also strips leading and trailing
    whitespace.

    Based on the Django version, but modified to preserve '$'.
    """
    value = (
        unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    )
    value = re.sub("[^$`\w\s-]", "", value).strip().lower()
    return re.sub("[-\s`]+", "-", value)


# FIXME: can we replace this with Python 3's html.escape ?
def escape_html(text, verbatim_mode=False, counters=None, single_line=False):
    def repl_python(match):
        return (
            r"""<pre><![CDATA[
%s
]]></pre>"""
            % match.group(1).strip()
        )

    text, post_substitutions = pre_sub(PYTHON_RE, text, repl_python)

    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    if not verbatim_mode:

        def repl_quotation(match):
            return r"&ldquo;%s&rdquo;" % match.group(1)

        text = QUOTATIONS_RE.sub(repl_quotation, text)

    if counters is None:
        counters = {}

    text = text.replace('"', "&quot;")
    if not verbatim_mode:

        def repl_latex(match):
            return "%s<var>%s</var>%s" % (
                match.group(1),
                match.group(2),
                match.group(3),
            )

        text = LATEX_RE.sub(repl_latex, text)

        def repl_mathics(match):
            text = match.group(1)
            text = text.replace("\\'", "'")
            text = text.replace(" ", "&nbsp;")
            if text:
                return "<code>%s</code>" % text
            else:
                return "'"

        def repl_allowed(match):
            content = _replace_all(
                match.group(1), [("&ldquo;", '"'), ("&rdquo;", '"'), ("&quot;", '"')]
            )
            return "<%s>" % content

        text = MATHICS_RE.sub(repl_mathics, text)
        for allowed in ALLOWED_TAGS:
            text = ALLOWED_TAGS_RE[allowed].sub(repl_allowed, text)
            text = text.replace("&lt;/%s&gt;" % allowed, "</%s>" % allowed)

        def repl_dl(match):
            text = match.group(1)
            text = DL_ITEM_RE.sub(
                lambda m: "<%(tag)s>%(content)s</%(tag)s>\n" % m.groupdict(), text
            )
            return "<dl>%s</dl>" % text

        text = DL_RE.sub(repl_dl, text)

        def repl_list(match):
            tag = match.group("tag")
            content = match.group("content")
            content = LIST_ITEM_RE.sub(lambda m: "<li>%s</li>" % m.group(1), content)
            return "<%s>%s</%s>" % (tag, content, tag)

        text = LIST_RE.sub(repl_list, text)

        def repl_hypertext(match):
            tag = match.group("tag")
            content = match.group("content")
            if tag == "em":
                return r"<em>%s</em>" % content
            elif tag == "url":
                return r'<a href="%s">%s</a>' % (content, content)

        text = HYPERTEXT_RE.sub(repl_hypertext, text)

        def repl_console(match):
            tag = match.group("tag")
            content = match.group("content")
            tag = "div" if tag == "console" else "span"
            content = content.strip()
            pre = post = ""

            # gets replaced for <br /> later by DocText.html()
            content = content.replace("\n", "<br>")

            return r'<%s class="console">%s%s%s</%s>' % (tag, pre, content, post, tag)

        text = CONSOLE_RE.sub(repl_console, text)

        def repl_img(match):
            src = match.group("src")
            title = match.group("title")
            return (
                r'<a href="/media/doc/%(src)s.pdf">'
                r'<img src="/media/doc/%(src)s.png" title="%(title)s" />'
                r"</a>"
            ) % {"src": src, "title": title}

        text = IMG_RE.sub(repl_img, text)

        def repl_imgpng(match):
            src = match.group("src")
            title = match.group("title")
            return (r'<img src="/media/doc/%(src)s" title="%(title)s" />') % {
                "src": src,
                "title": title,
            }

        text = IMG_PNG_RE.sub(repl_imgpng, text)

        def repl_ref(match):
            # TODO: this is not an optimal solution - maybe we need figure
            # numbers in the XML doc as well?
            return r"the following figure"

        text = REF_RE.sub(repl_ref, text)

        def repl_subsection(match):
            return '\n<h2 label="%s">%s</h2>\n' % (match.group(1), match.group(1))

        text = SUBSECTION_RE.sub(repl_subsection, text)
        text = SUBSECTION_END_RE.sub("", text)

        text = text.replace("\\'", "'")
    else:
        text = text.replace(" ", "&nbsp;")
        text = "<code>%s</code>" % text
    text = text.replace("'", "&#39;")
    text = text.replace("---", "&mdash;")
    for key, (xml, tex) in SPECIAL_COMMANDS.items():
        text = text.replace("\\" + key, xml)

    if not single_line:
        text = linebreaks(text)
        text = text.replace("<br />", "\n").replace("<br>", "<br />")

    text = post_sub(text, post_substitutions)

    text = text.replace("<p><pre>", "<pre>").replace("</pre></p>", "</pre>")

    return text
