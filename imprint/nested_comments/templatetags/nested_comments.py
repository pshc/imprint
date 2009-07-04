from django.template import Library

register = Library()

@register.filter
def multiply(num, factor):
    return int(num) * int(factor)

# vi: set sw=4 ts=4 sts=4 tw=79 ai et nocindent:
