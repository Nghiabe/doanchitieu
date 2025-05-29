from django import template
import math

register = template.Library()

@register.filter
def addcommas(value):
    try:
        formatted_value = "{:,.0f}".format(value).replace(",", ".")  # Thay dấu phẩy thành dấu chấm cho Việt Nam
        return f"{formatted_value} VND"  # Thêm VND phía sau
    except (ValueError, TypeError):
        return value
