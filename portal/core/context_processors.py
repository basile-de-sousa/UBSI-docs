from django.conf import settings


def environment(request):
    return {"development_preview": settings.DEBUG and not settings.PRODUCTION}
