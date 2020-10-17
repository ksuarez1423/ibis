"""
Shared functions for the SQL-based backends.

Eventually this should be converted to a base class inherited
from the SQL-based backends.
"""
import datetime
import math

import ibis.common.exceptions as com
import ibis.expr.operations as ops
import ibis.expr.types as ir
import ibis.sql.compiler as comp
from ibis.impala import identifiers


def _set_literal_format(translator, expr):
    value_type = expr.type().value_type

    formatted = [
        translator.translate(ir.literal(x, type=value_type))
        for x in expr.op().value
    ]

    return '(' + ', '.join(formatted) + ')'


def _boolean_literal_format(translator, expr):
    value = expr.op().value
    return 'TRUE' if value else 'FALSE'


def _string_literal_format(translator, expr):
    value = expr.op().value
    return "'{}'".format(value.replace("'", "\\'"))


def _number_literal_format(translator, expr):
    value = expr.op().value

    if math.isfinite(value):
        formatted = repr(value)
    else:
        if math.isnan(value):
            formatted_val = 'NaN'
        elif math.isinf(value):
            if value > 0:
                formatted_val = 'Infinity'
            else:
                formatted_val = '-Infinity'
        formatted = "CAST({!r} AS DOUBLE)".format(formatted_val)

    return formatted


def _interval_literal_format(translator, expr):
    return 'INTERVAL {} {}'.format(
        expr.op().value, expr.type().resolution.upper()
    )


def _date_literal_format(translator, expr):
    value = expr.op().value
    if isinstance(value, datetime.date):
        value = value.strftime('%Y-%m-%d')

    return repr(value)


def _timestamp_literal_format(translator, expr):
    value = expr.op().value
    if isinstance(value, datetime.datetime):
        value = value.strftime('%Y-%m-%d %H:%M:%S')

    return repr(value)


literal_formatters = {
    'boolean': _boolean_literal_format,
    'number': _number_literal_format,
    'string': _string_literal_format,
    'interval': _interval_literal_format,
    'timestamp': _timestamp_literal_format,
    'date': _date_literal_format,
    'set': _set_literal_format,
}


def literal(translator, expr):
    """Return the expression as its literal value."""
    if isinstance(expr, ir.BooleanValue):
        typeclass = 'boolean'
    elif isinstance(expr, ir.StringValue):
        typeclass = 'string'
    elif isinstance(expr, ir.NumericValue):
        typeclass = 'number'
    elif isinstance(expr, ir.DateValue):
        typeclass = 'date'
    elif isinstance(expr, ir.TimestampValue):
        typeclass = 'timestamp'
    elif isinstance(expr, ir.IntervalValue):
        typeclass = 'interval'
    elif isinstance(expr, ir.SetValue):
        typeclass = 'set'
    else:
        raise NotImplementedError

    return literal_formatters[typeclass](translator, expr)


def quote_identifier(name, quotechar='`', force=False):
    """Add quotes to the `name` identifier if needed."""
    if force or name.count(' ') or name in identifiers.impala_identifiers:
        return '{0}{1}{0}'.format(quotechar, name)
    else:
        return name


# TODO move the name method to comp.ExprTranslator and use that instead
class BaseExprTranslator(comp.ExprTranslator):
    """Base expression translator."""

    @staticmethod
    def _name_expr(formatted_expr, quoted_name):
        return '{} AS {}'.format(formatted_expr, quoted_name)

    def name(self, translated, name, force=True):
        """Return expression with its identifier."""
        return self._name_expr(translated, quote_identifier(name, force=force))


parenthesize = '({})'.format


def format_call(translator, func, *args):
    formatted_args = []
    for arg in args:
        fmt_arg = translator.translate(arg)
        formatted_args.append(fmt_arg)

    return '{}({})'.format(func, ', '.join(formatted_args))


def fixed_arity(func_name, arity):
    def formatter(translator, expr):
        op = expr.op()
        if arity != len(op.args):
            raise com.IbisError('incorrect number of args')
        return format_call(translator, func_name, *op.args)

    return formatter


def needs_parens(op):
    if isinstance(op, ir.Expr):
        op = op.op()
    op_klass = type(op)
    # function calls don't need parens
    return op_klass in binary_infix_ops or op_klass in {
        ops.Negate,
        ops.IsNull,
        ops.NotNull,
    }


def binary_infix_op(infix_sym):
    def formatter(translator, expr):
        op = expr.op()

        left, right = op.args

        left_arg = translator.translate(left)
        right_arg = translator.translate(right)
        if needs_parens(left):
            left_arg = parenthesize(left_arg)

        if needs_parens(right):
            right_arg = parenthesize(right_arg)

        return '{} {} {}'.format(left_arg, infix_sym, right_arg)

    return formatter


def identical_to(translator, expr):
    op = expr.op()
    if op.args[0].equals(op.args[1]):
        return 'TRUE'

    left_expr = op.left
    right_expr = op.right
    left = translator.translate(left_expr)
    right = translator.translate(right_expr)

    if needs_parens(left_expr):
        left = parenthesize(left)
    if needs_parens(right_expr):
        right = parenthesize(right)
    return '{} IS NOT DISTINCT FROM {}'.format(left, right)


def xor(translator, expr):
    op = expr.op()

    left_arg = translator.translate(op.left)
    right_arg = translator.translate(op.right)

    if needs_parens(op.left):
        left_arg = parenthesize(left_arg)

    if needs_parens(op.right):
        right_arg = parenthesize(right_arg)

    return '({0} OR {1}) AND NOT ({0} AND {1})'.format(left_arg, right_arg)


def unary(func_name):
    return fixed_arity(func_name, 1)


def ifnull_workaround(translator, expr):
    op = expr.op()
    a, b = op.args

    # work around per #345, #360
    if isinstance(a, ir.DecimalValue) and isinstance(b, ir.IntegerValue):
        b = b.cast(a.type())

    return format_call(translator, 'isnull', a, b)


binary_infix_ops = {
    # Binary operations
    ops.Add: binary_infix_op('+'),
    ops.Subtract: binary_infix_op('-'),
    ops.Multiply: binary_infix_op('*'),
    ops.Divide: binary_infix_op('/'),
    ops.Power: fixed_arity('pow', 2),
    ops.Modulus: binary_infix_op('%'),
    # Comparisons
    ops.Equals: binary_infix_op('='),
    ops.NotEquals: binary_infix_op('!='),
    ops.GreaterEqual: binary_infix_op('>='),
    ops.Greater: binary_infix_op('>'),
    ops.LessEqual: binary_infix_op('<='),
    ops.Less: binary_infix_op('<'),
    ops.IdenticalTo: identical_to,
    # Boolean comparisons
    ops.And: binary_infix_op('AND'),
    ops.Or: binary_infix_op('OR'),
    ops.Xor: xor,
}


def _not(translator, expr):
    (arg,) = expr.op().args
    formatted_arg = translator.translate(arg)
    if needs_parens(arg):
        formatted_arg = parenthesize(formatted_arg)
    return 'NOT {}'.format(formatted_arg)


def not_null(translator, expr):
    formatted_arg = translator.translate(expr.op().args[0])
    return '{} IS NOT NULL'.format(formatted_arg)


def is_null(translator, expr):
    formatted_arg = translator.translate(expr.op().args[0])
    return '{} IS NULL'.format(formatted_arg)


def negate(translator, expr):
    arg = expr.op().args[0]
    formatted_arg = translator.translate(arg)
    if isinstance(expr, ir.BooleanValue):
        return _not(translator, expr)
    else:
        if needs_parens(arg):
            formatted_arg = parenthesize(formatted_arg)
        return '-{}'.format(formatted_arg)


operation_registry = {
    # Unary operations
    ops.NotNull: not_null,
    ops.IsNull: is_null,
    ops.Negate: negate,
    ops.Not: _not,
    ops.IsNan: unary('is_nan'),
    ops.IsInf: unary('is_inf'),
    ops.IfNull: ifnull_workaround,
    ops.NullIf: fixed_arity('nullif', 2),
    ops.ZeroIfNull: unary('zeroifnull'),
    ops.NullIfZero: unary('nullifzero'),
}
