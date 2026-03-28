"""
Format Mathics3 objects
"""

from mathics.core.atoms import String
from mathics.core.systemsymbols import SymbolOutputForm, SymbolStandardForm
from mathics.format.box import format_element

FORM_TO_FORMAT = {
    "System`FullForm": "text",
    "System`InputForm": "text",
    #    "System`MathMLForm": "text",
    "System`OutputForm": "text",
    #    "System`TeXForm": "text",
    "System`String": "text",
}


def safe_html_string(value):
    """
    Escape characters in the
    """
    # TODO: check why the escaped characters are converted back to valid
    # HTML code and processed.
    return value  # mark_safe(escape_html(value))


def format_output(evaluation, expr, format=None):
    """
    Handle unformatted output using the *specific* capabilities \
    of mathics-django.

    evaluation.py format_output() from which this was derived is \
    similar but it can't make use of a front-ends \
    specific capabilities.
    """

    if format is None:
        format = evaluation.format

    if format == "unformatted":
        evaluation.exc_result = None
        return expr

    if isinstance(format, dict):
        return dict((k, evaluation.format_output(expr, f)) for k, f in format.items())

    # For some expressions, we want formatting to be different.
    # In particular for FullForm and InputForm output, we don't want
    # MathML, we want
    # plain-ol' text so we can cut and paste that.
    expr_type = expr.get_head_name()
    if expr_type in FORM_TO_FORMAT:
        # For these forms, we strip off the outer "Form" part
        format = FORM_TO_FORMAT[expr_type]

    # This part was derived from and the same as evaluation.py format_output.

    if format == "text":
        boxed = format_element(expr, evaluation, SymbolOutputForm)
        result = boxed.boxes_to_text()

        return safe_html_string(result)
    elif format == "xml":
        boxes = format_element(expr, evaluation, SymbolStandardForm)
        result = (
            '<math display="block">'
            f"{boxes.boxes_to_mathml(evaluation=evaluation)}"
            "</math>"
        )
        return safe_html_string(result)
    elif format == "tex":
        boxes = format_element(expr, evaluation, SymbolStandardForm)
        if isinstance(boxes, String):
            result = boxes.boxes_to_text()
        else:
            result = boxes.boxes_to_tex(evaluation=evaluation)
        return safe_html_string(result)

    raise ValueError
