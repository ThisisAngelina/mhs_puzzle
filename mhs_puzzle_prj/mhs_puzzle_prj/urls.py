"""
URL configuration for mhs_puzzle_prj project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.views import defaults
from django.conf import settings
from django.urls import path, include
import debug_toolbar

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('puzzle_app.urls')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns


# Set Django's built-in error handlers with custom templates
handler400 = lambda request, exception: defaults.bad_request(request, exception, template_name="puzzle_app/400.html")
handler403 = lambda request, exception: defaults.permission_denied(request, exception, template_name="puzzle_app/403.html")
handler404 = lambda request, exception: defaults.page_not_found(request, exception, template_name="puzzle_app/404.html")
handler500 = lambda request: defaults.server_error(request, template_name="puzzle_app/500.html")