from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import sqlite3
from pathlib import Path


# Utilitaire : récupère la base de données utilisée par Django (chemin absolu)
def get_sqlite_path():
    db_name = settings.DATABASES['default'].get('NAME')
    # si c'est un Path ou un objet similaire, convertir en str
    return str(db_name)


def get_series_from_db():
    """Retourne un dictionnaire {serie: [tomes...]} basé sur la table tomes."""
    db_path = get_sqlite_path()
    series = {}
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT serie, tome FROM tomes")
        rows = cur.fetchall()
        for serie, tome in rows:
            series.setdefault(serie, []).append(tome)
    finally:
        try:
            conn.close()
        except Exception:
            pass
    return series

def home(request):
    series = get_series_from_db()
    # fallback minimal si la table est vide
    if not series:
        series = {}
    print(series)
    return render(request, 'home.html', {"series": series})

def serie(request, serie):
    series = get_series_from_db()
    tomes = series.get(serie, [])
    # fournir aussi une séquence 1..50 au template (on ne peut pas appeler range() dans les templates)
    tomes_range = list(range(1, 51))
    return render(request, 'serie.html', {"serie": serie, "tomes": tomes, "tomes_range": tomes_range})

@csrf_exempt
def toggle_tome(request, serie, num):
    num = int(num)
    # bascule le flag outof pour la paire (serie, num) dans la BDD
    db_path = get_sqlite_path()
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        # Vérifie si la ligne existe déjà
        cur.execute("SELECT 1 FROM tomes WHERE serie = ? AND tome = ?", (serie, num))
        exists = cur.fetchone()

        # Si elle n'existe pas → on l'insère
        if not exists:
            cur.execute("INSERT INTO tomes (serie, tome) VALUES (?, ?)", (serie, num))
            conn.commit()
        else:
            cur.execute("DELETE FROM tomes WHERE serie = ? AND tome = ?", (serie, num))
            conn.commit()
    finally:
        try:
            conn.close()
        except Exception:
            pass
    return HttpResponse(status=204)