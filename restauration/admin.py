from django.contrib import admin

from .models import Compte, Eleve, Menu, Reservation, Service, Tarif, Transaction


# Version personnalisée : on choisit les colonnes et les filtres de la liste
@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("eleve", "service", "statut", "prix", "date_reservation")  # colonnes affichées
    list_filter = ("statut", "service__date")   # filtres à droite ; « __ » = traverser une relation


@admin.register(Eleve)
class EleveAdmin(admin.ModelAdmin):
    list_display = ("nom", "prenom", "classe", "email", "quotient_categorie")
    search_fields = ("nom", "prenom", "reference_attestation")   # ajoute une barre de recherche
    list_filter = ("classe",)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("date", "type_repas", "capacite_max", "places_restantes", "heure_limite")
    list_filter = ("type_repas",)


# Version simple : Django choisit tout seul l'affichage
admin.site.register([Compte, Menu, Tarif, Transaction])