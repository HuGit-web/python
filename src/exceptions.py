class ErreurBibliotheque(Exception):
    """Exception racine pour les erreurs de la bibliotheque / gestion de fichiers."""
    def __init__(self, message: str, code_erreur: int = 0):
        super().__init__(message)
        self.code_erreur = code_erreur

raise ErreurBibliotheque(
    "ISBN deja existant", 
    code_erreur=1001
    )
