# pylint: disable=C0103, C0301, missing-docstring
from django.urls import path, re_path

from . import views

urlpatterns = [
    re_path('^login/?$', views.LutrisLoginView.as_view(), name='login'),
    re_path('^logout/?$', views.LutrisLogoutView.as_view(), name='logout'),
    path('password/change', views.LutrisPasswordChangeView.as_view(), name='password_change'),
    path('password/change/done', views.LutrisPasswordChangeDoneView.as_view(), name='password_change_done'),
    path('password/reset', views.LutrisPasswordResetView.as_view(), name='password_reset'),
    path('password/reset/done', views.LutrisPasswordResetDoneView.as_view(), name="password_reset_done"),
    re_path(r'^password/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/?$',  # noqa
            views.LutrisPasswordResetConfirmView.as_view(),
            name='password_reset_confirm'),
    path('register', views.LutrisRegisterView.as_view(), name="register"),
    path('clear-auth-token/', views.clear_auth_token, name="clear_auth_token"),
    path('associate-steam/', views.associate_steam, name="associate_steam"),
    path('steam-disconnect', views.steam_disconnect, name="steam_disconnect"),
    path('<username>/library/', views.LibraryList.as_view(), name="library_list"),
    path('<username>/submissions/', views.SubmissionList.as_view(), name="submission_list"),
    path('<username>/installers/', views.InstallerList.as_view(), name="installer_list"),
    path('library/add/<slug:slug>/', views.library_add, name="add_to_library"),
    path('library/remove/<slug:slug>/', views.library_remove, name="remove_from_library"),
    path('library/steam-sync/', views.library_steam_sync, name="library_steam_sync"),
    path('profile', views.profile, name="profile"),
    path('send-confirmation', views.user_send_confirmation, name='user_send_confirmation'),
    path('require-confirmation', views.user_require_confirmation, name='user_require_confirmation'),
    path('confirm', views.user_email_confirm, name='user_email_confirm'),
    path('discourse-sso', views.discourse_sso, name='discourse_sso'),
    path('edit', views.ProfileUpdateView.as_view(), name='profile_edit'),
    path('<username>/delete', views.profile_delete, name='profile_delete'),
    path('<username>', views.user_account, name="user_account"),
]
