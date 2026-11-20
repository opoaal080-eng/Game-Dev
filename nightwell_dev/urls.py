from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path, reverse_lazy

admin.site.site_header = "Nightwell Dev · Управление"
admin.site.site_title = "Nightwell Dev"
admin.site.index_title = "Администрирование"

urlpatterns = [
    path("api/v1/", include("portal.api_urls")),
    path("control/", admin.site.urls),
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html", redirect_authenticated_user=True), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("account/password/", auth_views.PasswordChangeView.as_view(template_name="registration/password_change_form.html", success_url=reverse_lazy("password_change_done")), name="password_change"),
    path("account/password/changed/", auth_views.PasswordChangeDoneView.as_view(template_name="registration/password_change_done.html"), name="password_change_done"),
    path("", include("portal.urls")),
]
