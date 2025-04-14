"""
Format Mathics3 objects
"""

from typing import Callable

from mathics.core.atoms import SymbolString
from mathics.core.expression import BoxError, Expression
from mathics.core.systemsymbols import (
    SymbolCompiledFunction,
    SymbolFullForm,
    SymbolGraphics,
    SymbolGraphics3D,
    SymbolInputForm,
    SymbolMathMLForm,
    SymbolOutputForm,
    SymbolStandardForm,
    SymbolTeXForm,
)
from mathics.session import get_settings_value

FORM_TO_FORMAT = {
    "System`MathMLForm": "xml",
    "System`TeXForm": "tex",
    "System`FullForm": "text",
    "System`OutputForm": "text",
}


def format_output(obj, expr, format=None):
    """
    Handle unformatted output using the *specific* capabilities \
    of mathics-django.

    evaluation.py format_output() from which this was derived is \
    similar but it can't make use of a front-ends \
    specific capabilities.
    """

    def eval_boxes(result, fn: Callable, obj, **options):
        options["evaluation"] = obj
        try:
            boxes = fn(**options)
            # print("XXX\n", boxes)
        except BoxError:
            boxes = None
            if not hasattr(obj, "seen_box_error"):
                obj.seen_box_error = True
                obj.message(
                    "General",
                    "notboxes",
                    Expression(SymbolFullForm, result).evaluate(obj),
                )

        return boxes

    if format is None:
        format = obj.format

    if isinstance(format, dict):
        return dict((k, obj.format_output(expr, f)) for k, f in format.items())

    # For some expressions, we want formatting to be different.
    # In particular for FullForm output, we don't want MathML, we want
    # plain-ol' text so we can cut and paste that.

    expr_type = expr.get_head_name()
    expr_head = expr.get_head()
    if expr_head in (SymbolMathMLForm, SymbolTeXForm):
        # For these forms, we strip off the outer "Form" part
        format = FORM_TO_FORMAT[expr_type]
        elements = expr.get_elements()
        if len(elements) == 1:
            expr = elements[0]

    if expr_head in (SymbolFullForm, SymbolOutputForm):
        result = expr.elements[0].format(obj, expr_type)
        return result.boxes_to_text()
    elif expr_head is SymbolGraphics:
        expr_sf = Expression(SymbolStandardForm, expr)
        result = expr_sf.format(obj, "System`MathMLForm")

    # This part was derived from and the same as evaluation.py format_output.

    use_quotes = get_settings_value(obj.definitions, "Settings`$QuotedStrings")

    if format == "text":
        result = expr.format(obj, SymbolOutputForm)
        result = eval_boxes(result, result.boxes_to_text, obj)

        if use_quotes:
            result = '"' + result + '"'

        return result
    elif format == "xml":
        expr_sf = Expression(SymbolStandardForm, expr)
        result = expr_sf.format(obj, "System`MathMLForm")
    elif format == "tex":
        expr_sf = Expression(SymbolStandardForm, expr)
        result = expr_sf.format(obj, "System`TeXForm")
    elif format == "unformatted":
        if expr_head is SymbolCompiledFunction:
            result = expr.format(obj, SymbolOutputForm)
        elif expr_head is SymbolString:
            result = expr.format(obj, SymbolInputForm)
            result = result.boxes_to_text()

            if not use_quotes:
                # Substring without the quotes
                result = result[1:-1]

            return result
        elif expr_head is SymbolGraphics3D:
            form_expr = Expression(SymbolStandardForm, expr)
            result = form_expr.format(obj, SymbolStandardForm)
            return eval_boxes(result, result.boxes_to_js, obj)
        elif expr_head is SymbolGraphics:
            form_expr = Expression(SymbolStandardForm, expr)
            result = form_expr.format(obj, SymbolStandardForm)
            return eval_boxes(result, result.boxes_to_svg, obj)
        else:
            result = Expression(SymbolStandardForm, expr).format(obj, SymbolMathMLForm)
    else:
        raise ValueError

    if result is None:
        return f"Error in evaluating {expr}"
    return eval_boxes(result, result.boxes_to_text, obj)
