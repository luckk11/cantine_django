"""
URLs de l'application restauration.

Le routeur DRF fabrique automatiquement les adresses à partir des ViewSets,
comme admin.site.urls le fait pour l'admin.

router.register(r"services", ServiceViewSet) produit :
    /services/      -> la liste      (nom de route : service-list)
    /services/1/    -> un élément    (nom de route : service-detail)
"""
from rest_framework.routers import DefaultRouter

from .views import MenuViewSet, ServiceViewSet

router = DefaultRouter()
# basename : préfixe des noms de routes générés
router.register(r"menus", MenuViewSet, basename="menu")
router.register(r"services", ServiceViewSet, basename="service")

# DefaultRouter ajoute aussi une page d'accueil à la racine de l'API,
# qui liste les points d'entrée disponibles.
urlpatterns = router.urls