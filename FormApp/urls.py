from django.contrib import admin
from django.urls import path
from FormApp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name="Home"),
    path('EventForm', views.createForm, name="Form")
]