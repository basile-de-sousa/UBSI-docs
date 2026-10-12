from django import template

from core.assets import frontend_assets

register = template.Library()


@register.simple_tag
def portal_assets():
    return frontend_assets()
