"""
Vues de l'API.

Un ViewSet reçoit la requête HTTP et décide quoi répondre.
C'est l'équivalent, côté API, de la classe ModelAdmin côté admin.

ReadOnlyModelViewSet ne fournit QUE la lecture :
    GET /api/services/     -> la liste
    GET /api/services/1/   -> un élément
Les verbes POST, PUT et DELETE renvoient 405 (« méthode non autorisée »),
car aucune authentification n'est encore en place (ce sera la séance 3).
"""
from rest_framework import viewsets

from .models import Menu, Service
from .serializers import MenuSerializer, ServiceSerializer


class MenuViewSet(viewsets.ReadOnlyModelViewSet):
    # queryset : QUELLES données sont concernées
    queryset = Menu.objects.all()
    # serializer_class : COMMENT les traduire en JSON
    serializer_class = MenuSerializer


class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
    # select_related("menu") : Django va chercher le service ET son menu
    # en UNE seule requête SQL, au lieu d'une requête par service.
    queryset = Service.objects.select_related("menu").all()
    serializer_class = ServiceSerializer