from django.urls import path

urlpatterns = [
    path("", include("apps.monitor.urls")),
]
