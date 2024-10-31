from django.urls import path
from . import views

urlpatterns = [
    path("", views.home_view, name="home"),
    path("login/", views.login_view, name="login"),
    path("callback/", views.callback_view, name="callback"),
    path("logout/", views.logout_view, name="logout"),
    path("prueba/", views.prueba_view, name="prueba"),
]
