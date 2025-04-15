from django.urls import path
from .views import smart_builder_home, smart_builder_submit

urlpatterns = [
    path('', smart_builder_home, name='smart_builder'),
    path('submit/', smart_builder_submit, name='smart_builder_submit'),
]