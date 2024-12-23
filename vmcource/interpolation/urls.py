from django.urls import path
from . import views

urlpatterns = [
    path('input/', views.input_data, name='input_data'),
    path('result/', views.result, name='result'),
]