# online/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('classes/', views.online_class_list, name='class_list'),
    path('class/<int:class_id>/', views.class_detail, name='class_detail'),
    path('session/<int:session_id>/', views.session_detail, name='session_detail'),
    path('attend/<int:session_id>/', views.attend_session, name='attend_session'),
]
