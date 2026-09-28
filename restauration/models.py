"""
Modèles de l'application « restauration ».

Rappel : chaque classe = une table en base, chaque attribut = une colonne.
Django ajoute automatiquement une colonne « id » (clé primaire) à chaque table.
Tous les montants sont en CENTIMES (entiers), jamais en float.
"""
from django.db import models
from django.db.models import Q


class Eleve(models.Model):
    nom = models.CharField(max_length=80)
    prenom = models.CharField(max_length=80)
    classe = models.CharField(max_length=20)
    email = models.EmailField()
    # unique=True : la base refuse deux élèves avec la même référence
    reference_attestation = models.CharField(max_length=40, unique=True)
    # Catégorie de quotient familial, sert à trouver le bon Tarif
    quotient_categorie = models.CharField(max_length=10)

    class Meta:
        verbose_name = "élève"          # nom affiché dans l'admin
        ordering = ["nom", "prenom"]    # tri par défaut

    def __str__(self):
        # Texte affiché quand on « imprime » un élève (admin, shell…)
        return f"{self.prenom} {self.nom} ({self.classe})"


class Compte(models.Model):
    ROLES = [
        ("ELEVE", "Élève"),
        ("PERSONNEL", "Personnel"),
        ("GESTIONNAIRE", "Gestionnaire"),
    ]

    # Un élève <-> un compte. Accès inverse : eleve.compte
    eleve = models.OneToOneField(Eleve, on_delete=models.CASCADE)
    solde = models.IntegerField(default=0)  # centimes
    role = models.CharField(max_length=15, choices=ROLES, default="ELEVE")

    def __str__(self):
        return f"Compte de {self.eleve} : {self.solde / 100:.2f} €"


class Service(models.Model):
    """Un repas servi à une date donnée (ex. : le déjeuner du 3 octobre)."""

    TYPES_REPAS = [
        ("DEJEUNER", "Déjeuner"),
        ("DINER", "Dîner"),
    ]

    date = models.DateField()
    type_repas = models.CharField(max_length=15, choices=TYPES_REPAS, default="DEJEUNER")
    capacite_max = models.PositiveIntegerField()   # PositiveInteger : pas de nombre négatif
    heure_limite = models.DateTimeField()          # après cette heure, on ne réserve plus

    class Meta:
        ordering = ["date"]
        constraints = [
            # Pas deux « déjeuner » le même jour
            models.UniqueConstraint(fields=["date", "type_repas"], name="service_unique_par_jour"),
        ]

    def __str__(self):
        return f"{self.get_type_repas_display()} du {self.date:%d/%m/%Y}"

    def places_restantes(self):
        """Capacité moins le nombre de réservations confirmées (utilisé par RG5)."""
        confirmees = self.reservations.filter(statut="CONFIRMEE").count()
        return self.capacite_max - confirmees


class Menu(models.Model):
    """Ce qu'on mange lors d'un service. Un service <-> un menu."""

    service = models.OneToOneField(Service, on_delete=models.CASCADE, related_name="menu")
    entree = models.CharField(max_length=120, blank=True)   # blank=True : facultatif dans les formulaires
    plat = models.CharField(max_length=120)
    dessert = models.CharField(max_length=120, blank=True)

    def __str__(self):
        return f"Menu – {self.service}"


class Tarif(models.Model):
    """Prix d'un repas selon la catégorie de quotient, sur une période (utilisé par RG4)."""

    quotient_categorie = models.CharField(max_length=10)
    prix = models.PositiveIntegerField()                    # centimes
    date_debut = models.DateField()
    # null=True : la colonne peut être vide en base -> tarif toujours en vigueur
    date_fin = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["quotient_categorie", "-date_debut"]   # « - » = ordre décroissant

    def __str__(self):
        return f"Catégorie {self.quotient_categorie} : {self.prix / 100:.2f} €"


class Reservation(models.Model):
    STATUTS = [
        ("CONFIRMEE", "Confirmée"),
        ("ANNULEE", "Annulée"),
    ]

    # Un élève a plusieurs réservations. Accès inverse : eleve.reservations.all()
    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE, related_name="reservations")
    # PROTECT : impossible de supprimer un service qui a des réservations
    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name="reservations")
    statut = models.CharField(max_length=12, choices=STATUTS, default="CONFIRMEE")
    prix = models.IntegerField()                                  # centimes, prix payé au moment T
    date_reservation = models.DateTimeField(auto_now_add=True)    # rempli automatiquement à la création

    class Meta:
        ordering = ["-date_reservation"]
        constraints = [
            # Un élève ne peut avoir qu'UNE réservation confirmée par service.
            # (Il peut en revanche re-réserver après une annulation.)
            models.UniqueConstraint(
                fields=["eleve", "service"],
                condition=Q(statut="CONFIRMEE"),
                name="une_resa_confirmee_par_service",
            ),
        ]

    def __str__(self):
        return f"{self.eleve} – {self.service} ({self.get_statut_display()})"


class Transaction(models.Model):
    """Historique des mouvements d'argent sur un compte (comme un relevé bancaire)."""

    TYPES = [
        ("CREDIT", "Crédit"),
        ("DEBIT", "Débit"),
    ]
    MOYENS = [
        ("DEBIT_RESA", "Débit sur réservation"),
        ("CB", "Carte bancaire"),
        ("ESPECES", "Espèces"),
    ]

    # PROTECT : on ne supprime pas un compte qui a un historique comptable
    compte = models.ForeignKey(Compte, on_delete=models.PROTECT, related_name="transactions")
    type = models.CharField(max_length=6, choices=TYPES)
    montant = models.PositiveIntegerField()   # centimes, toujours positif ; le « type » donne le sens
    # Lien facultatif : un crédit n'a pas de réservation.
    # SET_NULL : si la réservation disparaît, la transaction reste mais sans lien.
    reservation = models.ForeignKey(Reservation, on_delete=models.SET_NULL, null=True, blank=True)
    moyen = models.CharField(max_length=15, choices=MOYENS)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        signe = "+" if self.type == "CREDIT" else "-"
        return f"{signe}{self.montant / 100:.2f} € ({self.get_moyen_display()})"