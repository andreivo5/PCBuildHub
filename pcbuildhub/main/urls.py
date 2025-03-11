from django.urls import path
from .views import (
    main_page, create_build, components_page, component_list, view_build
)

urlpatterns = [
    path('', main_page, name='home'),
    path('create/', create_build, name='create_build'),
    path('create/<uuid:build_id>/', view_build, name='view_build'),
    path('components/', components_page, name='components'),  
    path('components/<str:component_type>/', component_list, name='component'),
    path('components/<str:component_type>/<uuid:build_id>/', component_list, name='component_with_build'),
    path('components/<str:component_type>/<uuid:build_id>/<int:component_id>/', component_list, name='select_component'),
]