from django import views
from django.urls import path,include
from .views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", home, name="home"),
    path("serie/<str:serie>/", serie, name="serie"),
    path('toggle_tome/<str:serie>/<int:num>', toggle_tome, name='toggle_tome'),
]