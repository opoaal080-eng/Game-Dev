from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

admin.site.site_header = "Nightwell Dev · Управление"
admin.site.site_title = "Nightwell Dev"
admin.site.index_title = "Администрирование"

urlpatterns = [
    path("control/", admin.site.urls),
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html", redirect_authenticated_user=True), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", include("portal.urls")),
]
