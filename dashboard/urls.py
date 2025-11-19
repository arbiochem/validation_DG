from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.dashboard_home, name='dashboard_home'),
    path('modifier_ligne/<int:id>/', views.modifier_ligne, name='modifier_ligne'),
    path('change_statut/', views.change_statut, name='change_statut'),
    path('<str:do_piece>/', views.lignes_view, name='lignes_view'),
    path('logout/', views.logout_view, name='logout'),
]
