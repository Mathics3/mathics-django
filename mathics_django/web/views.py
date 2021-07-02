# -*- coding: utf-8 -*-

import os.path as osp
import re
import sys
import traceback

from builtins import open as builtin_open
from django import __version__ as django_version
from django.shortcuts import render
from django.template import RequestContext, loader
from django.http import (
    HttpResponse,
    HttpResponseNotFound,
    HttpResponseServerError,
    Http404,
)
import json
from django.conf import settings
from django.contrib import auth
from django.contrib.auth.models import User

from django.core.mail import send_mail

from mathics import version_info as mathics_version_info
from mathics.core.definitions import Definitions
from mathics.core.evaluation import Message, Result
from mathics.system_info import mathics_system_info

from mathics_django.doc import documentation
from mathics_django.doc.django_doc import (
    DjangoDocPart,
    DjangoDocChapter,
    DjangoDocSection,
)
from mathics_django.settings import DOC_XML_DATA_PATH, MATHICS_DJANGO_DB_PATH
from mathics_django.version import __version__
from mathics_django.web.forms import LoginForm, SaveForm
from mathics_django.web.models import Query, Worksheet, get_session_evaluation

from mathics_scanner import replace_wl_with_plain_text
from mathics.settings import default_pymathics_modules

documentation.load_pymathics_doc()

if settings.DEBUG:
    JSON_CONTENT_TYPE = "text/html"
else:
    JSON_CONTENT_TYPE = "application/json"


class JsonResponse(HttpResponse):
    def __init__(self, result={}):
        response = json.dumps(result)
        super(JsonResponse, self).__init__(response, content_type=JSON_CONTENT_TYPE)


def is_authenticated(user):
    if callable(user.is_authenticated):
        return user.is_authenticated()
    return user.is_authenticated


# def require_ajax_login(func):
#     def new_func(request, *args, **kwargs):
#         if not is_authenticated(request.user):
#             return JsonResponse({"requireLogin": True})
#         return func(request, *args, **kwargs)

#     return new_func


def get_three_version():
    """
    Get the three.js version the static and hacky way not involving javascript.
    """
    three_file = osp.join(
        osp.normcase(osp.dirname(osp.abspath(__file__))),
        "media",
        "js",
        "three",
        "three.js",
    )
    pattern = r"""var REVISION = '(\d+)'"""
    match = re.search(pattern, builtin_open(three_file).read())
    if match:
        return "r" + match.group(1)
    else:
        return "r??"


def get_MathJax_version():
    """
    Get the MathJax version the static and hacky way not involving javascript.
    """
    three_file = osp.join(
        osp.normcase(osp.dirname(osp.abspath(__file__))),
        "media",
        "js",
        "mathjax",
        "MathJax.js",
    )
    pattern = r'MathJax.version="(\d\.\d\.\d)"'
    match = re.search(pattern, builtin_open(three_file).read())
    if match:
        return match.group(1)
    else:
        return "?.?.?"


def get_user_settings(evaluation):
    definitions = evaluation.definitions
    setting_names = sorted(definitions.get_matching_names("Settings`*"))
    user_settings = {}

    evaluation.stopped = False

    for setting_name in setting_names:
        rule = evaluation.parse(setting_name)
        value = rule.evaluate(evaluation).to_python()

        setting_usage_expr = evaluation.parse(setting_name + "::usage")
        setting_usage = setting_usage_expr.evaluate(evaluation).to_python(
            string_quotes=False
        )

        user_settings[setting_name] = {
            "value": value,
            "usage": setting_usage,
            "is_boolean": type(value) is bool,
            "boolean_value": value,
        }

    return user_settings


def about_view(request):
    """
    This view gives information about the version and software we have loaded.
    """
    evaluation = get_session_evaluation(request.session)
    definitions = evaluation.definitions
    system_info = mathics_system_info(definitions)

    return render(
        request,
        "about.html",
        {
            "django_version": django_version,
            "three_js_version": get_three_version(),
            "MathJax_version": get_MathJax_version(),
            "mathics_version": mathics_version_info["mathics"],
            "mathics_django_version": __version__,
            "mpmath_version": mathics_version_info["mpmath"],
            "numpy_version": mathics_version_info["mathics"],
            "python_version": mathics_version_info["python"],
            "sympy_version": mathics_version_info["sympy"],
            "SystemID": system_info["$SystemID"],
            "SystemTimeZone": system_info["$SystemTimeZone"],
            "UserName": system_info["$UserName"],
            "BaseDirectory": system_info["$BaseDirectory"],
            "HomeDirectory": system_info["$HomeDirectory"],
            "InstallationDirectory": system_info["$InstallationDirectory"],
            "RootDirectory": system_info["$RootDirectory"],
            "TemporaryDirectory": system_info["$TemporaryDirectory"],
            "DB_PATH": MATHICS_DJANGO_DB_PATH,
            "DOC_XML_DATA_PATH": DOC_XML_DATA_PATH,
            "HTTP_USER_AGENT": request.META.get("HTTP_USER_AGENT", ""),
            "REMOTE_USER": request.META.get("REMOTE_USER", ""),
            "REMOTE_ADDR": request.META.get("REMOTE_ADDR", ""),
            "REMOTE_HOST": request.META.get("REMOTE_HOST", ""),
            "MachinePrecision": system_info["MachinePrecision"],
            "MemoryAvailable": system_info["MemoryAvailable[]"],
            "SystemMemory": system_info["$SystemMemory"],
            "Machine": system_info["$Machine"],
            "MachineName": system_info["$MachineName"],
            "ProcessID": system_info["$ProcessID"],
            "ProcessorType": system_info["$ProcessorType"],
            "user_settings": get_user_settings(evaluation),
        },
    )


def require_ajax_login(f):
    return f


def main_view(request):
    """
    This is what people normally see when running the server.
    It contains the banner line with logo and icons to load and save and
    a worksheet area to evaluate expressions. Off the the right is optional documentation.
    """
    context = {
        "login_form": LoginForm(),
        "save_form": SaveForm(),
        "require_login": settings.REQUIRE_LOGIN,
    }
    return render(request, "main.html", context)


def error_404_view(request, exception):
    t = loader.get_template("404.html")
    return HttpResponseNotFound(
        t.render(
            RequestContext(
                request,
                {
                    "title": "Page not found",
                    "request_path": request.path,
                },
            )
        )
    )


def error_500_view(request):
    t = loader.get_template("500.html")
    return HttpResponseServerError(
        t.render(
            RequestContext(
                request,
                {
                    "title": "Server error",
                },
            )
        )
    )


def query(request):
    """
    Handles Mathics input expressions.
    """
    global definitions
    from mathics.core.parser import MathicsMultiLineFeeder

    input = request.POST.get("query", "")
    if settings.DEBUG and not input:
        input = request.GET.get("query", "")

    if settings.LOG_QUERIES:
        query_log = Query(
            query=input,
            error=True,
            browser=request.META.get("HTTP_USER_AGENT", ""),
            remote_user=request.META.get("REMOTE_USER", ""),
            remote_addr=request.META.get("REMOTE_ADDR", ""),
            remote_host=request.META.get("REMOTE_HOST", ""),
            meta=str(request.META),
            log="",
        )
        query_log.save()

    evaluation = get_session_evaluation(request.session)
    feeder = MathicsMultiLineFeeder(input, "<notebook>")
    results = []
    try:
        while not feeder.empty():
            expr = evaluation.parse_feeder(feeder)
            if expr is None:
                results.append(Result(evaluation.out, None, None))  # syntax errors
                evaluation.out = []
                continue
            result = evaluation.evaluate(expr, timeout=settings.TIMEOUT)
            if result.result is not None:
                result.result = replace_wl_with_plain_text(result.result)
            results.append(result)  # syntax errors

    except SystemExit:
        results = []
        result = None
        definitions = Definitions(
            add_builtin=True, extension_modules=default_pymathics_modules
        )
        evaluation.definitions = definitions
    except Exception as exc:
        if settings.DEBUG and settings.DISPLAY_EXCEPTIONS:
            info = traceback.format_exception(*sys.exc_info())
            info = "\n".join(info)
            msg = "Exception raised: %s\n\n%s" % (exc, info)
            results.append(Result([Message("System", "exception", msg)], None, None))
        else:
            raise
    result = {
        "results": [result.get_data() for result in results],
    }
    if settings.LOG_QUERIES:
        query_log.timeout = evaluation.timeout
        query_log.result = str(result)  # evaluation.results
        query_log.error = False
        query_log.save()
    return JsonResponse(result)


# nicepass is taken from http://code.activestate.com/recipes/410076/
def nicepass(alpha=6, numeric=2):
    """
    returns a human-readble password (say rol86din instead of
    a difficult to remember K8Yn9muL )
    """
    import string
    import random

    vowels = ["a", "e", "i", "o", "u"]
    consonants = [a for a in string.ascii_lowercase if a not in vowels]
    digits = string.digits

    # utility functions
    def a_part(slen):
        ret = ""
        for i in range(slen):
            if i % 2 == 0:
                randid = random.randint(0, 20)  # number of consonants
                ret += consonants[randid]
            else:
                randid = random.randint(0, 4)  # number of vowels
                ret += vowels[randid]
        return ret

    def n_part(slen):
        ret = ""
        for i in range(slen):
            randid = random.randint(0, 9)  # number of digits
            ret += digits[randid]
        return ret

    fpl = alpha / 2
    if alpha % 2:
        fpl = int(alpha / 2) + 1
    lpl = alpha - fpl

    start = a_part(fpl)
    mid = n_part(numeric)
    end = a_part(lpl)

    return "%s%s%s" % (start, mid, end)


def email_user(user, subject, text):
    send_mail(
        subject, text, "noreply@mathics.net", [user.username], fail_silently=False
    )


def login(request):
    if settings.DEBUG and not request.POST:
        request.POST = request.GET
    form = LoginForm(request.POST)
    result = ""
    general_errors = []
    if form.is_valid():
        email = form.cleaned_data["email"]
        password = form.cleaned_data["password"]
        if password:
            user = auth.authenticate(username=email, password=password)
            if user is None:
                general_errors = ["Invalid username and/or password."]
            else:
                result = "ok"
                auth.login(request, user)
        else:
            password = nicepass()
            try:
                user = User.objects.get(username=email)
                result = "reset"
                email_user(
                    user,
                    "Your password at mathics.net",
                    (
                        """You have reset your password at mathics.net.\n
Your password is: %s\n\nYours,\nThe Mathics team"""
                    )
                    % password,
                )
            except User.DoesNotExist:
                user = User(username=email, email=email)
                result = "created"
                email_user(
                    user,
                    "New account at mathics.net",
                    """Welcome to mathics.net!\n
Your password is: %s\n\nYours,\nThe Mathics team"""
                    % password,
                )
            user.set_password(password)
            user.save()

    return JsonResponse(
        {
            "result": result,
            "form": form.as_json(general_errors=general_errors),
        }
    )


def logout(request):
    auth.logout(request)
    return JsonResponse()


@require_ajax_login
def save(request):
    if settings.DEBUG and not request.POST:
        request.POST = request.GET
    if settings.REQUIRE_LOGIN and not is_authenticated(request.user):
        raise Http404
    form = SaveForm(request.POST)
    overwrite = request.POST.get("overwrite", False)
    result = ""
    if form.is_valid():
        content = request.POST.get("content", "")
        name = form.cleaned_data["name"]
        user = request.user
        if not is_authenticated(user):
            user = None
        try:
            worksheet = Worksheet.objects.get(user=user, name=name)
            if overwrite:
                worksheet.content = content
            else:
                result = "overwrite"
        except Worksheet.DoesNotExist:
            worksheet = Worksheet(user=user, name=name, content=content)
        worksheet.save()

    return JsonResponse(
        {
            "form": form.as_json(),
            "result": result,
        }
    )


def open(request):
    user = request.user
    if settings.REQUIRE_LOGIN and not is_authenticated(user):
        raise Http404
    name = request.POST.get("name", "")
    try:
        if is_authenticated(user):
            worksheet = user.worksheets.get(name=name)
        else:
            worksheet = Worksheet.objects.get(user__isnull=True, name=name)
        content = worksheet.content
    except Worksheet.DoesNotExist:
        content = ""

    return JsonResponse(
        {
            "content": content,
        }
    )


def get_worksheets(request):
    if settings.REQUIRE_LOGIN and not is_authenticated(request.user):
        result = []
    else:
        if is_authenticated(request.user):
            result = list(request.user.worksheets.order_by("name").values("name"))
        else:
            result = list(
                Worksheet.objects.filter(user__isnull=True)
                .order_by("name")
                .values("name")
            )
    return JsonResponse(
        {
            "worksheets": result,
        }
    )


def delete(request):
    user = request.user
    if settings.REQUIRE_LOGIN and not is_authenticated(user):
        raise Http404
    name = request.POST.get("name", "")
    try:
        if is_authenticated(user):
            deleted = user.worksheets.get(name=name).delete()
        else:
            deleted = Worksheet.objects.get(user__isnull=True, name=name).delete()
        content = str(deleted[0])
    except Worksheet.DoesNotExist:
        content = ""

    return JsonResponse(
        {
            "content": content,
        }
    )


# auxiliary function


def render_doc(request, template_name, context, data=None, ajax: str = ""):
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

    result = render(request, "doc/%s" % template_name, context)
    if not ajax:
        return result

    result = {
        "content": result.getvalue().decode("utf-8"),
    }
    if data is not None:
        result["data"] = data
    return JsonResponse(result)


def doc(request, ajax=""):
    return render_doc(
        request,
        "overview.html",
        {
            "title": "Documentation",
            "doc": documentation,
        },
        ajax=ajax,
    )


def doc_part(request, part, ajax=""):
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


def doc_chapter(request, part, chapter, ajax=""):
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


def doc_section(
    request, part: str, chapter: str, section: str, ajax=False, subsections=[]
):
    """
    Produces HTML via jinja templating for a section which is either:
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
    request, part: str, chapter: str, section: str, subsection: str, ajax=""
):
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


def doc_search(request):
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
