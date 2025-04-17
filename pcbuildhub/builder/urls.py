from django.urls import path
from .views import (
    create_build, view_build, new_build, save_build, rename_build, delete_build
)

urlpatterns = [
    path('', create_build, name='create_build'),
    path('new/', new_build, name='new_build'),
    path('<str:build_id>/', view_build, name='view_build'),
    path('save/<str:build_id>/', save_build, name='save_build'),
    path('build/<str:build_id>/rename/', rename_build, name='rename_build'),
    path('build/<str:build_id>/delete/', delete_build, name="delete_build"),
]