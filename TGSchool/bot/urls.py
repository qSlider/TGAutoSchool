from django.urls import path
from .views import AddQuestionView, CheckRegister, delete_registration, send_email
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('add_question/', AddQuestionView.as_view(), name='add_question'),
    path('check_register/', CheckRegister.as_view(), name='check_register'),
    path('delete/<int:registration_id>/', delete_registration, name='delete_registration'),
    path('send_email/<int:registration_id>/', send_email, name='send_email'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
