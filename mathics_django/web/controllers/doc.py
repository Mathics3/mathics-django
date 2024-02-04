"""
Controllers related to showing Mathics3 documentation inside Django
"""

from copy import copy
from typing import Union

from django.core.handlers.wsgi import WSGIRequest
from django.http import Http404, HttpResponse
from django.shortcuts import render
from mathics.doc.common_doc import get_module_doc
from mathics.eval.pymathics import pymathics_builtins_by_module, pymathics_modules

from mathics_django.doc import documentation
from mathics_django.doc.django_doc import (
    DjangoDocChapter,
    DjangoDocPart,
    DjangoDocSection,
    MathicsDjangoDocumentation,
)
from mathics_django.web.views import JsonResponse

DocResponse = Union[HttpResponse, JsonResponse]

seen_pymathics_modules = copy(pymathics_modules)



def check_for_pymathics_load():
    global seen_pymathics_modules
    if seen_pymathics_modules != pymathics_modules:
        print("XXX refresh pymathics doc", pymathics_modules)
        new_modules = pymathics_modules - seen_pymathics_modules
        for new_module in new_modules:
            title, _ = get_module_doc(new_module)
            mathics3_module_part = documentation.parts_by_slug.get("mathics3-modules", None)
            # If this is the first loaded module, we need to create the Part
            if mathics3_module_part is None:
                mathics3_module_part = self.doc_part(
                    "Mathics3 Modules", pymathics_modules, pymathics_builtins_by_module, True
                )
                seen_pymathics_modules = copy(pymathics_modules)
                return

            # The part already exists. Lets add the new chapter.

            chapter = mathics3_module_part.doc.gather_chapter_doc_fn(
                mathics3_module_part,
                title,
                mathics3_module_part.doc,
            )
            from trepan.api import debug

            debug()
            submodule_names_seen = set()
            chapter.doc.doc_chapter(
                new_module,
                mathics3_module_part,
                pymathics_builtins_by_module,
                seen_pymathics_modules,
                submodule_names_seen,
            )
            chapter.get_tests()
        seen_pymathics_modules = copy(pymathics_modules)
        pass


def doc(request: WSGIRequest, ajax: bool = False) -> DocResponse:
    check_for_pymathics_load()
    return render_doc(
        request,
        "overview.html",
        {
            "title": "Documentation",
            "doc": documentation,
        },
        ajax=ajax,
    )


def doc_chapter(request: WSGIRequest, part, chapter, ajax: bool = False) -> DocResponse:
    """
    Produces HTML via jinja templating for a chapter. Some examples of
    Chapters:

    * Introduction (in part Manual)
    * Procedural Programming (in part Reference of Built-in Symbols)
    """
    check_for_pymathics_load()
    chapter = documentation.get_chapter(part, chapter)
    if not chapter:
        raise Http404
    return render_doc(
        request,
        "chapter.html",
        {
            "title": chapter.get_title_html(),
            "chapter": chapter,
            "object": chapter,
        },
        ajax=ajax,
    )


def doc_part(request: WSGIRequest, part, ajax: bool = False) -> DocResponse:
    """
    Produces HTML via jinja templating for a Part - the top-most
    subdivision of the document. Some examples of Parts:
    * Manual
    * Reference of Built-in Symbols
    """
    check_for_pymathics_load()
    part = documentation.get_part(part)
    if not part:
        raise Http404
    return render_doc(
        request,
        "part.html",
        {
            "title": part.get_title_html(),
            "part": part,
            "object": part,
        },
        ajax=ajax,
    )


def doc_search(request: WSGIRequest) -> DocResponse:
    check_for_pymathics_load()
    query = request.GET.get("query", "")
    result = documentation.search(query)
    if len([item for exact, item in result if exact]) <= 1:
        for exact, item in result:
            if exact and (len(item.slug) > 4) or len(result) == 1:
                if isinstance(item, DjangoDocPart):
                    return doc_part(request, item.slug, ajax=True)
                elif isinstance(item, DjangoDocChapter):
                    return doc_chapter(request, item.part.slug, item.slug, ajax=True)
                elif isinstance(item, DjangoDocSection):
                    return doc_section(
                        request,
                        item.chapter.part.slug,
                        item.chapter.slug,
                        item.slug,
                        ajax=True,
                        subsections=item.subsections,
                    )
                else:
                    return doc_subsection(
                        request,
                        item.chapter.part.slug,
                        item.chapter.slug,
                        item.section.slug,
                        item.slug,
                        ajax=True,
                    )

    result = [item for exact, item in result]

    return render_doc(
        request,
        "search.html",
        {
            "title": "Search documentation",
            "result": result,
        },
        ajax=True,
    )


def doc_section(
    request: WSGIRequest,
    part: str,
    chapter: str,
    section: str,
    ajax: bool = False,
    subsections=[],
) -> DocResponse:
    """
    Produces HTML via Jinja templating a section which is either:
    * A section of the static Manual. For example, "Why yet another CAS?"
    * A Built-in function which is not part of a Section Guide. For example, Abort[]
    * A list of builtin-functions under a Guide Section. For example: Color Directives.
      The guide section here would be Colors.
    """
    check_for_pymathics_load()
    section_obj = documentation.get_section(part, chapter, section)
    if not section_obj:
        raise Http404
    data = section_obj.html_data()
    return render_doc(
        request,
        "section.html",
        {
            "title": section_obj.get_title_html(),
            "title_operator": section_obj.operator,
            "section": section_obj,
            "subsections": subsections,
            "object": section_obj,
        },
        data=data,
        ajax=ajax,
    )


def doc_subsection(
    request: WSGIRequest,
    part: str,
    chapter: str,
    section: str,
    subsection: str,
    ajax: bool = False,
) -> DocResponse:
    """Proceses a document subsection. This is often the bottom-most
    entity right now.  In particular it contains built-in functions
    which are part of a guide section.  (Those builtings that are not
    organized in a guide section are tagged as a section rather than a
    subsection.)
    """
    check_for_pymathics_load()
    subsection_obj = documentation.get_subsection(part, chapter, section, subsection)
    if not subsection_obj:
        raise Http404
    data = subsection_obj.html_data()
    return render_doc(
        request,
        "subsection.html",
        {
            "title": subsection_obj.get_title_html(),
            "title_operator": subsection_obj.operator,
            "section": section,
            "subsection": subsection_obj,
            "object": subsection_obj,
        },
        data=data,
        ajax=ajax,
    )


def render_doc(
    request: WSGIRequest,
    template_name: str,
    context: dict,
    data=None,
    ajax: bool = False,
) -> DocResponse:
    """
    Call this routine is called to render
    documentation. ``template_name`` is the Jinja documentation
    template that is used for creating the HTML result, and
    ``context`` contains the variables used in that template.

    If ``ajax`` is True the should the ajax URI prefix, e.g. " it we pass the result

    """
    check_for_pymathics_load()
    object = context.get("object")
    context.update(
        {
            "ajax": ajax,
            "help_base": ("doc/base_ajax.html" if ajax else "doc/base_standalone.html"),
            "prev": object.get_prev() if object else None,
            "next": object.get_next() if object else None,
        }
    )
    if not ajax:
        context.update(
            {
                "data": data,
            }
        )

    result = render(request, f"doc/{template_name}", context)
    if not ajax:
        return result

    result = {
        "content": result.getvalue().decode("utf-8"),
    }
    if data is not None:
        result["data"] = data
    return JsonResponse(result)
