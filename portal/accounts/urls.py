from django.urls import path

from . import views

urlpatterns = [
    path("auth/login/", views.sign_in, name="login"),
    path("auth/logout/", views.sign_out, name="logout"),
    path("auth/invitations/<uuid:invitation_id>/<str:token>/", views.invitation_exchange, name="invitation-exchange"),
    path("auth/invitation/", views.invitation_accept, name="invitation-accept"),
    path("auth/recovery/", views.recovery, name="recovery"),
    path("auth/recovery/sent/", views.recovery_done, name="recovery-done"),
    path("auth/reset/<uuid:user_id>/<str:token>/", views.reset_exchange, name="reset-exchange"),
    path("auth/reset/", views.reset_confirm, name="reset-confirm"),
    path("admin/accounts/", views.directory, name="accounts"),
    path("admin/accounts/invite/", views.send_invitation, name="invite"),
    path("admin/accounts/invitations/<uuid:invitation_id>/resend/", views.resend_invitation, name="invite-resend"),
    path("admin/accounts/<uuid:user_id>/access/", views.change_access, name="account-access"),
]
