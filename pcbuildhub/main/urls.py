from django.urls import path
from .views import main_page, create_build, components_page, cpu_list, gpu_list

urlpatterns = [
    path('', main_page, name='home'),
    path('create/', create_build, name='create_build'),
    path('components/', components_page, name='components'),  
    path('components/cpu/', cpu_list, name='cpu_list'),  
    path('components/gpu/', gpu_list, name='gpu_list'),  
]
