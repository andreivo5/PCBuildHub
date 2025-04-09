from django.urls import path
from . import views

urlpatterns = [
    path('', views.smart_builder_home, name='smart_builder'),
]