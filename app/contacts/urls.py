from django.urls import path
from .views import ContactFormView

urlpatterns = [
    path('send/', ContactFormView.as_view(), name='contact-send'),
]
