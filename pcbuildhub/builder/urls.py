from django.urls import path
from .views import (
    create_build, view_build, new_build
)

urlpatterns = [
    path('', create_build, name='create_build'),
    path('new/', new_build, name='new_build'),
    path('<str:build_id>/', view_build, name='view_build'),
]