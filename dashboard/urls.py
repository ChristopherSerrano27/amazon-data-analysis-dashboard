from django.urls import path
from . import views

urlpatterns = [
    path('', views.general_dashboard, name='general_dashboard'),
]