from django.urls import path
from .views import AddQuestionView , CheckRegister
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('add_question/', AddQuestionView.as_view(), name='add_question'),
    path('check_register/', CheckRegister.as_view(), name='check_register'),
]
