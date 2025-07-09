from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return '' 

@register.filter
def add_and_multiply(value, args):
    """ args should be a string like "4,0.1" """
    try:
        add_val, mul_val = map(float, args.split(','))
        return (float(value) + add_val) * mul_val
    except:
        return ''