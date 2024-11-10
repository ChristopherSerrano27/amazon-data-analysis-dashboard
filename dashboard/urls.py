from django.urls import path
from . import views

urlpatterns = [
    path('general/', views.general_dashboard, name='general_dashboard'),
]