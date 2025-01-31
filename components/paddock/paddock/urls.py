"""paddock URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
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
from django.urls import include, path
from django.views.generic import TemplateView

from . import views

import paddock.pitcrew_app  # noqa: F401

urlpatterns = [
    # path("", views.index, name="home"),
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    # path('pitcrew', TemplateView.as_view(template_name='pitcrew.html'), name="pitcrew"),
    path("fastlap/<int:fastlap_id>", views.fastlap_view, name="fastlap"),
    path("pitcrew/<str:driver_name>", views.pitcrew_view, name="pitcrew"),
    path("pitcrew/", views.pitcrew_index, name="pitcrew_index"),
    # path("stewards/", include("stewards.urls")),
    path("admin/", admin.site.urls),
    path("explorer/", include("explorer.urls")),
    path("django_plotly_dash/", include("django_plotly_dash.urls")),
]
