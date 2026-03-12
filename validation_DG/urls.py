from django.contrib import admin
from django.urls import path, include  # ✅ include doit être importé

urlpatterns = [
    path('admin/', admin.site.urls), 
    path('dashboard/', include('dashboard.urls')),     # facultatif, pour accéder à l'admin
    path('', include('login.urls')),
]
