from django.urls import path
from .views import AddQuestionView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('add_question/', AddQuestionView.as_view(), name='add_question'),
]
