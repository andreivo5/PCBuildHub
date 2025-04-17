from django.urls import path, include
from .views import (
    main_page
)

urlpatterns = [
    path('', main_page, name='home'),
    path('components/', include('components.urls')),
    path('create/', include('builder.urls')),
    path('smartbuild/', include('smartbuilder.urls')),
    path('upgrade/', include('upgrade.urls')),
    path('accounts/', include('login.urls')),
]