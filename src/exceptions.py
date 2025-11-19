class ErreurBibliotheque(Exception):
    """Exception racine pour les erreurs de la bibliotheque / gestion de fichiers."""
    pass


class ErreurFichier(ErreurBibliotheque):
    """Erreurs liées aux operations sur les fichiers (I/O, JSON, CSV)."""
    pass
