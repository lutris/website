# pylint: disable=C0103, C0301, missing-docstring
from django.contrib.auth import views as auth_views
from django.urls import path, re_path

from . import forms, views

urlpatterns = [
    path('login/',
         auth_views.LoginView.as_view(
             template_name='accounts/login.html',
             authentication_form=forms.LoginForm
         ),
        name='login'),
    path('logout/',
         auth_views.LogoutView.as_view(
             template_name='accounts/logout.html'
         ),
        name='logout'),
    path('password/change/',
        auth_views.PasswordChangeView.as_view(
            template_name='accounts/password_change.html'
        ),
        name='password_change'),
    path('password/change/done/',
         auth_views.PasswordChangeDoneView.as_view(
             template_name='accounts/password_change_done.html'
         ),
        name='password_change_done'),
    path('password/reset/',
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset.html'
         ),
        name='password_reset'),
    re_path(r'^password/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',  # noqa
        auth_views.PasswordResetConfirmView.as_view(
            template_name='accounts/password_reset_confirm.html'
        ),
        name='password_reset_confirm'),
    path('password/reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html'
         ),
        name='password_reset_done'),
    path('password/reset/complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html'
         ),
        name='password_reset_complete'),

    path('register/', views.register, name="register"),
    path('clear-auth-token/', views.clear_auth_token, name="clear_auth_token"),
    path('associate-steam/', views.associate_steam, name="associate_steam"),
    path('steam-disconnect/', views.steam_disconnect, name="steam_disconnect"),
    path('<username>/library/', views.LibraryList.as_view(), name="library_show"),
    path('library/add/<slug:slug>/', views.library_add, name="add_to_library"),
    path('library/remove/<slug:slug>/', views.library_remove, name="remove_from_library"),
    path('library/steam-sync/', views.library_steam_sync, name="library_steam_sync"),
    path('profile/', views.profile, name="profile"),
    path('send-confirmation/', views.user_send_confirmation, name='user_send_confirmation'),
    path('require-confirmation/', views.user_require_confirmation, name='user_require_confirmation'),
    path('confirm/', views.user_email_confirm, name='user_email_confirm'),
    path('discourse-sso/', views.discourse_sso, name='discourse_sso'),
    path('<username>/edit/', views.profile_edit, name='profile_edit'),
    path('<username>/delete/', views.profile_delete, name='profile_delete'),
    path('<username>/', views.user_account, name="user_account"),
]
