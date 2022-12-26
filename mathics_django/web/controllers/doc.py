"""
Controllers related to showing Mathics documentation inside Django
"""

from typing import Union

from django.core.handlers.wsgi import WSGIRequest
from django.http import Http404, HttpResponse

from django.shortcuts import render

from mathics_django.doc import documentation
from mathics_django.doc.django_doc import (
    DjangoDocChapter,
    DjangoDocPart,
    DjangoDocSection,
)

from mathics_django.web.views import JsonResponse

DocResponse = Union[HttpResponse, JsonResponse]

documentation.load_pymathics_doc()


def doc(request: WSGIRequest, ajax: bool = False) -> DocResponse:
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
    Produces HTML via jinja templating for a chapter. Some examples of Chapters:
    * Introduction (in part Manual)
    * Procedural Programming (in part Reference of Built-in Symbols)
    """
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
    Call this routine is called to render documentation. ``template_name`` is the Jinja documentation template
    that is used for creating the HTML result, and ``context`` contains the variables used in that template.

    If ``ajax`` is True the should the ajax URI prefix, e.g. " it we pass the result
    """
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
