from django.urls import path
from .views import (
    components_page, component_list
)

urlpatterns = [
    path('', components_page, name='components'),  
    path('<str:component_type>/', component_list, name='component'),
    path('<str:component_type>/<str:build_id>/', component_list, name='component_with_build'),
    path('<str:component_type>/<str:build_id>/<int:component_id>/', component_list, name='select_component'),
]