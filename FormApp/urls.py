from django.contrib import admin
from django.urls import path
from FormApp import views

urlpatterns = [
    path('', views.index, name="Home"),
    path('EventForm', views.createForm, name="Form"),
    path('create', views.createImage),
    path('temp_1', views.temp_1),   
]