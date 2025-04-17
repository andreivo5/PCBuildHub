from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = "login"

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="home"), name="logout"),

    path("signup/", views.SignUpView.as_view(), name="signup"),

    path("profile/", views.profile, name="profile"),
]