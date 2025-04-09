from django.urls import path
from . import views

urlpatterns = [
    path('', views.upgrade_build_home, name='upgrade_build'),
]