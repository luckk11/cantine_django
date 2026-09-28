"""
Serializers : traduction entre objets Python et JSON.

- Sens sortie (sérialisation)    : objet Menu  ->  {"id": 1, "plat": "Poulet", ...}
- Sens entrée  (désérialisation) : {"plat": "Poulet"}  ->  objet Menu, APRÈS validation

ModelSerializer déduit les champs et les règles de validation à partir du modèle :
un CharField(max_length=120) devient automatiquement une validation « 120 caractères max ».
"""
from rest_framework import serializers

from .models import Menu, Service


class MenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = Menu
        # Seuls ces champs sortent dans le JSON. Un champ absent d'ici est invisible.
        fields = ["id", "service", "entree", "plat", "dessert"]


class ServiceSerializer(serializers.ModelSerializer):
    # Champ CALCULÉ : n'existe pas en base. DRF voit que places_restantes est une
    # méthode du modèle, l'appelle, et met son résultat dans le JSON.
    # read_only : ce champ sort, mais un client ne peut pas l'envoyer.
    places_restantes = serializers.IntegerField(read_only=True)

    # Le libellé lisible (« Déjeuner ») en plus de la valeur stockée (« DEJEUNER »).
    # source=... indique quelle méthode de l'objet fournit la valeur.
    type_repas_libelle = serializers.CharField(source="get_type_repas_display", read_only=True)

    # IMBRICATION : au lieu d'un simple numéro, on insère le menu complet dans le JSON.
    # Une app mobile obtient ainsi le service ET son menu en une seule requête.
    # SerializerMethodField : la valeur est produite par la méthode get_<nom> ci-dessous.
    menu = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = [
            "id",
            "date",
            "type_repas",
            "type_repas_libelle",
            "capacite_max",
            "places_restantes",
            "heure_limite",
            "menu",
        ]

    def get_menu(self, obj):
        """Renvoie le menu du service, ou None si aucun menu n'a encore été saisi."""
        # getattr(..., None) : un service sans menu ne fait pas planter l'API,
        # le JSON contiendra simplement "menu": null.
        menu = getattr(obj, "menu", None)
        return MenuSerializer(menu).data if menu else None