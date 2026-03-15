from django.urls import path
from .views import SendNotificationEmailView, UsersListView

urlpatterns = [
    path('send-email/', SendNotificationEmailView.as_view(), name='send-notification-email'),
    path('users-list/', UsersListView.as_view(), name='users-list-for-notifications'),
]
