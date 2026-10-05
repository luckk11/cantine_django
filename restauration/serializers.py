"""
Serializers : traduction entre objets Python et JSON.

- Sens sortie (sérialisation)    : objet Menu  ->  {"id": 1, "plat": "Poulet", ...}
- Sens entrée  (désérialisation) : {"plat": "Poulet"}  ->  objet Menu, APRÈS validation
"""
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Compte, Eleve, Menu, Service
from .permissions import role_de


class MenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = Menu
        fields = ["id", "service", "entree", "plat", "dessert"]


class ServiceSerializer(serializers.ModelSerializer):
    places_restantes = serializers.IntegerField(read_only=True)
    type_repas_libelle = serializers.CharField(source="get_type_repas_display", read_only=True)
    menu = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = [
            "id", "date", "type_repas", "type_repas_libelle",
            "capacite_max", "places_restantes", "heure_limite", "menu",
        ]

    def get_menu(self, obj):
        menu = getattr(obj, "menu", None)
        return MenuSerializer(menu).data if menu else None


class MonTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Personnalise le contenu du jeton JWT.

    SimpleJWT met par défaut l'identifiant de l'utilisateur dans le jeton.
    On y ajoute le rôle et le nom : l'application cliente peut ainsi adapter
    son affichage sans requête supplémentaire.

    ATTENTION : un JWT est SIGNÉ, pas CHIFFRÉ. N'importe qui peut lire son
    contenu ; personne ne peut le modifier sans invalider la signature.
    On n'y met donc jamais d'information secrète.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)          # le jeton standard
        token["username"] = user.username
        token["role"] = role_de(user) or ("GESTIONNAIRE" if user.is_staff else None)
        return token


class EnrolementSerializer(serializers.Serializer):
    """
    Enrôlement d'un élève (F1).

    Serializer « simple » (pas ModelSerializer) : les données entrantes ne
    correspondent pas à un seul modèle. On reçoit une référence d'attestation
    et des identifiants, on crée un User et on le relie à l'Eleve existant.
    """

    reference_attestation = serializers.CharField(max_length=40)
    username = serializers.CharField(max_length=150)
    # write_only : le mot de passe entre, mais ne ressort JAMAIS dans une réponse.
    # validate_password applique les règles d'AUTH_PASSWORD_VALIDATORS (settings.py).
    password = serializers.CharField(write_only=True, validators=[validate_password])

    # --- Validations champ par champ -------------------------------------
    # DRF appelle automatiquement validate_<nom_du_champ>() pour chacun.

    def validate_reference_attestation(self, value):
        if not Eleve.objects.filter(reference_attestation=value).exists():
            raise serializers.ValidationError("Référence d'attestation inconnue.")
        return value

    def validate_username(self, value):
        from django.contrib.auth import get_user_model
        if get_user_model().objects.filter(username=value).exists():
            raise serializers.ValidationError("Ce nom d'utilisateur est déjà pris.")
        return value

    # --- Création --------------------------------------------------------

    @transaction.atomic
    def create(self, validated_data):
        """
        transaction.atomic : les trois écritures (User, lien, Compte) réussissent
        ensemble ou sont toutes annulées. Jamais de User créé sans élève relié.
        """
        from django.contrib.auth import get_user_model

        # select_for_update : verrouille la ligne jusqu'à la fin de la transaction.
        # Deux requêtes simultanées avec la même référence ne peuvent pas
        # s'enrôler toutes les deux.
        eleve = (
            Eleve.objects.select_for_update()
            .get(reference_attestation=validated_data["reference_attestation"])
        )

        # On revérifie ICI, et pas seulement dans validate_() : entre la
        # validation et la création, une autre requête a pu passer.
        if eleve.utilisateur_id is not None:
            raise serializers.ValidationError(
                {"reference_attestation": "Cet élève est déjà enrôlé."}
            )

        user = get_user_model().objects.create_user(
            username=validated_data["username"],
            password=validated_data["password"],   # create_user hache le mot de passe
            email=eleve.email,
            first_name=eleve.prenom,
            last_name=eleve.nom,
        )

        eleve.utilisateur = user
        eleve.save(update_fields=["utilisateur"])

        # get_or_create : crée le compte s'il n'existe pas, le récupère sinon.
        Compte.objects.get_or_create(eleve=eleve, defaults={"solde": 0, "role": "ELEVE"})

        return eleve