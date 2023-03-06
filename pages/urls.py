from django.urls import path
from . import views

app_name = 'pages'
urlpatterns = [
    path('', views.index, name="index"),
    path('add_donations', views.add_donations, name="add_donations"),
    path('login', views.login, name="login"),
]
