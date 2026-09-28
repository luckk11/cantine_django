"""
URL configuration for cantine project.

C'est l'aiguilleur principal : il regarde le début de l'adresse demandée
et transmet la suite au bon module.
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    # Tout ce qui commence par « api/ » est confié aux URLs de l'app restauration.
    # include() coupe le préfixe déjà consommé : /api/menus/ arrive là-bas comme « menus/ ».
    path('api/', include('restauration.urls')),
]