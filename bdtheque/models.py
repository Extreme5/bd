from django.db import models


class Winshlist(models.Model):
    """Stocke le contenu éditable de la page wishlist (singleton attendu)."""
    content = models.TextField(blank=True, default='')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Winshlist (mis à jour: {self.updated_at:%Y-%m-%d %H:%M:%S})"
