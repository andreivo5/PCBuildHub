from django.urls import path
from .views import main_page, create_build

urlpatterns = [
    path('', main_page, name='home'),
    path('create/', create_build, name='create_build'),
]
