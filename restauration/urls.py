"""
URLs de l'application restauration.

Deux sortes de routes cohabitent :
- celles fabriquées automatiquement par le routeur DRF (les ViewSets) ;
- celles écrites à la main avec path(), pour les vues qui ne sont pas des ViewSets.
"""
from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from .views import EnrolementView, MenuViewSet, MonTokenObtainPairView, ServiceViewSet

router = DefaultRouter()
router.register(r"menus", MenuViewSet, basename="menu")
router.register(r"services", ServiceViewSet, basename="service")

urlpatterns = [
    # Authentification
    path("token/", MonTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    # Enrôlement (F1)
    path("eleves/enrolement/", EnrolementView.as_view(), name="enrolement"),
] + router.urls   # on concatène les routes du routeur