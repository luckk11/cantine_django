"""
Permissions : « qu'avez-vous le DROIT de faire ? »

À ne pas confondre avec l'authentification (« qui êtes-vous ? »), qui est
assurée par les jetons JWT. DRF pose toujours les deux questions dans cet
ordre : d'abord il identifie, ensuite il autorise.

Une permission est une classe avec une méthode has_permission() qui renvoie
True (autorisé) ou False (refusé -> réponse 403).
"""
from rest_framework import permissions


def role_de(user):
    """
    Retrouve le rôle métier d'un utilisateur connecté.

    Le chemin suit les relations : User -> Eleve -> Compte -> role
    getattr(..., None) à chaque étape : un maillon manquant renvoie None
    au lieu de faire planter la requête.
    """
    if not user or not user.is_authenticated:
        return None
    eleve = getattr(user, "eleve", None)          # grâce à related_name="eleve"
    if eleve is None:
        return None
    compte = getattr(eleve, "compte", None)       # relation OneToOne Compte -> Eleve
    return compte.role if compte else None


class EstGestionnaire(permissions.BasePermission):
    """Autorise uniquement le personnel d'administration."""

    # Ce texte sera renvoyé au client dans le JSON d'erreur 403.
    message = "Action réservée aux gestionnaires."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        # is_staff : les superusers créés avec createsuperuser
        if user.is_staff:
            return True
        return role_de(user) == "GESTIONNAIRE"


class LectureAuthentifieeEcritureGestionnaire(permissions.BasePermission):
    """
    Tout utilisateur connecté peut LIRE ; seul un gestionnaire peut ÉCRIRE.

    C'est la règle des menus et des services : un élève consulte,
    le gestionnaire saisit.
    """

    message = "Seuls les gestionnaires peuvent modifier cette ressource."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # SAFE_METHODS = ("GET", "HEAD", "OPTIONS") : les verbes qui ne modifient rien
        if request.method in permissions.SAFE_METHODS:
            return True
        return EstGestionnaire().has_permission(request, view)