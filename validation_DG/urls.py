from django.contrib import admin
from django.urls import path, include  # ✅ include doit être importé

urlpatterns = [
    path('admin/', admin.site.urls),      # facultatif, pour accéder à l'admin
    path('', include('dashboard.urls')),  # le dashboard devient la page principale
]
