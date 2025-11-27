from django.urls import path
from . import views

urlpatterns = [
    path('', views.input_data, name='input_data'),
]
