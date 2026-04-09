"""
Format Mathics3 objects
"""

from mathics.core.atoms import String
from mathics.core.systemsymbols import (
    SymbolAborted,
    SymbolFailed,
    SymbolInterpretationBox,
    SymbolOutputForm,
    SymbolStandardForm,
    SymbolTeXForm,
)
from mathics.format.box import format_element

# Maps a Form to a kind of rendering process
FORM_TO_RENDER = {
    "System`FullForm": "text",
    "System`InputForm": "text",
    # "System`MathMLForm": "mathml",
    "System`OutputForm": "text",
    "System`TeXForm": "tex",
    "System`String": "text",
}


def safe_html_string(value):
    """
    Escape characters in the
    """
    # TODO: check why the escaped characters are converted back to valid
    # HTML code and processed.
    return value  # mark_safe(escape_html(value))


def format_output(evaluation, expr, render=None):
    """
    Handle unformatted output using the *specific* capabilities \
    of mathics-django.

    evaluation.py format_output() from which this was derived is \
    similar but it can't make use of a front-ends \
    specific capabilities.
    """

    if render is None:
        render = evaluation.format

    if render == "unformatted":
        evaluation.exc_result = None
        return expr

    if isinstance(render, dict):
        return dict((k, evaluation.format_output(expr, f)) for k, f in render.items())

    if expr is SymbolAborted:
        return "$Aborted"
    elif expr is SymbolFailed:
        return "$Failed"

    # For some expressions, we want formatting to be different.
    # In particular for FullForm and InputForm output, we don't want
    # MathML, we want
    # plain-ol' text so we can cut and paste that.
    expr_type = expr.get_head_name()
    if expr_type in FORM_TO_RENDER:
        # For these forms, we strip off the outer "Form" part
        render = FORM_TO_RENDER[expr_type]

    # This part was derived from and the same as evaluation.py format_output.

    if render == "text":
        boxed = format_element(expr, evaluation, SymbolOutputForm)
        result = boxed.boxes_to_text()

        return safe_html_string(result)
    elif render == "xml":
        boxed = format_element(expr, evaluation, SymbolStandardForm)
        if (
            hasattr(boxed, "head")
            and boxed.head is SymbolInterpretationBox
            and (box_value := boxed.elements[0].value).startswith('"<math ')
        ):
            # FIXME: [1:-1] is to strip quotes.
            # We should probably address a long-standing mistake where strings
            # have quotes in them.
            return box_value[1:-1]

        # THINK ABOUT: This probably no longer happens
        result = (
            '<math display="block">'
            f"{boxed.to_mathml(evaluation=evaluation)}"
            "</math>"
        )
        return safe_html_string(result)
    elif render == "tex":
        boxed = format_element(expr, evaluation, SymbolTeXForm)
        if hasattr(boxed, "head") and boxed.head is SymbolInterpretationBox:
            # FIXME: [1:-1] is to strip quotes.
            # We should probably address a long-standing mistake where strings
            # have quotes in them.
            box_str_sans_quotes = boxed.elements[0].value[1:-1]
            return f"$${box_str_sans_quotes}$$"

        # THINK ABOUT: This probably no longer happens
        if isinstance(boxed, String):
            result = boxed.to_text()
        else:
            result = boxed.to_tex(evaluation=evaluation)
        return safe_html_string(result)

    raise ValueError
