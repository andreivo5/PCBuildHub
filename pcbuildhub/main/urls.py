from django.urls import path
from .views import (
    main_page, create_build, components_page, cpu_list, gpu_list, case_list,
    cooler_list, ram_list, motherboard_list, psu_list, storage_list
)

urlpatterns = [
    path('', main_page, name='home'),
    path('create/', create_build, name='create_build'),
    path('components/', components_page, name='components'),  
    path('components/cpu/', cpu_list, name='cpu_list'),  
    path('components/gpu/', gpu_list, name='gpu_list'),  
    path('components/case/', case_list, name='case_list'),  
    path('components/cooler/', cooler_list, name='cooler_list'),
    path('components/ram/', ram_list, name='ram_list'),
    path('components/motherboard/', motherboard_list, name='motherboard_list'),
    path('components/psu/', psu_list, name='psu_list'),
    path('components/storage/', storage_list, name='storage_list'),
]