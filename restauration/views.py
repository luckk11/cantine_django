"""
Vues de l'API.

Un ViewSet reçoit la requête HTTP et décide quoi répondre.
C'est l'équivalent, côté API, de la classe ModelAdmin côté admin.
"""
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Menu, Service
from .permissions import LectureAuthentifieeEcritureGestionnaire
from .serializers import (
    EnrolementSerializer,
    MenuSerializer,
    MonTokenObtainPairSerializer,
    ServiceSerializer,
)


class MonTokenObtainPairView(TokenObtainPairView):
    """POST /api/token/ : échange identifiant + mot de passe contre deux jetons."""
    serializer_class = MonTokenObtainPairSerializer


class MenuViewSet(viewsets.ModelViewSet):
    # ModelViewSet (et non plus ReadOnlyModelViewSet) : l'écriture est désormais
    # possible, mais la permission ci-dessous la réserve aux gestionnaires.
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer
    permission_classes = [LectureAuthentifieeEcritureGestionnaire]


class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.select_related("menu").all()
    serializer_class = ServiceSerializer
    permission_classes = [LectureAuthentifieeEcritureGestionnaire]


class EnrolementView(generics.CreateAPIView):
    """
    POST /api/eleves/enrolement/ (F1)

    AllowAny : c'est la SEULE route ouverte à un visiteur non connecté, et pour
    cause — on ne peut pas exiger un jeton de quelqu'un qui n'a pas encore de
    compte. C'est une exception assumée au « refus par défaut ».
    """

    serializer_class = EnrolementSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        # raise_exception=True : en cas de données invalides, DRF renvoie
        # automatiquement une 400 avec le détail des erreurs par champ.
        serializer.is_valid(raise_exception=True)
        eleve = serializer.save()
        return Response(
            {
                "detail": "Enrôlement réussi. Vous pouvez maintenant demander un jeton.",
                "eleve_id": eleve.id,
                "username": eleve.utilisateur.username,
            },
            status=status.HTTP_201_CREATED,
        )