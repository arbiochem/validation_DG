from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.dashboard_home, name='dashboard_home'),  # vue principale
    path('<str:do_piece>/', views.lignes_view, name='lignes_view'),
    path('<str:do_piece>/', views.ligne_modifier, name='modifier_ligne'),
    path('<str:do_piece>/', views.ligne_supprimer, name='lignessuppr'),
    path('logout/', views.logout_view, name='logout'),
]
