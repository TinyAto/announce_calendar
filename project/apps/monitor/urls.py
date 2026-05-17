from django.urls import path

from . import views

urlpatterns = [
    path("", views.message_list, name="message_list"),
    path("channel/<str:channel_id>/", views.channel_messages, name="channel_messages"),
    path("search/", views.message_search, name="message_search"),
    path("channels/", views.channel_list, name="channel_list"),
    path("api/announcements/", views.announcements_api, name="announcements_api"),
]
