from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib import messages
import sqlite3
from django import forms
import os
from .models import Winshlist


class NameForm(forms.Form):
    your_name = forms.CharField(label="Your name", max_length=100)


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

        #trier par ordre alphabétique
        sorted_keys = sorted(series.keys())
        series = {k: series[k] for k in sorted_keys} 

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

    # Calcul du total d'albums : compter les lignes dans `tomes` où `tome` n'est pas NULL
    total_albums = 0
    db_path = get_sqlite_path()
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        row = cur.execute("SELECT COUNT(*) FROM tomes WHERE tome IS NOT NULL").fetchone()
        if row and row[0] is not None:
            total_albums = int(row[0])
    except Exception:
        # fallback : calcul approximatif depuis la structure chargée en mémoire
        try:
            total_albums = sum(max(0, len(tomes) - 1) for tomes in series.values())
        except Exception:
            total_albums = 0
    finally:
        try:
            conn.close()
        except Exception:
            pass

    return render(request, 'home.html', {"series": series, "total_albums": total_albums+12})


def add_serie(request):
    """Endpoint AJAX : ajoute une série côté client et renvoie JSON.

    NOTE: Pour l'instant on n'ajoute pas de ligne dans la table `tomes` (pas de tomes)
    afin d'éviter d'insérer des lignes incomplètes. Le front-end ajoutera la carte
    dynamiquement et la persistance pourra être implémentée si vous créez une
    table `series` dédiée ou modifiez le modèle.
    """
    if request.method == 'POST':
        serie_name = request.POST.get('serie_name') or request.GET.get('serie_name')
        if serie_name:
            return JsonResponse({'ok': True, 'serie': serie_name, 'tomes_count': 0})
    return JsonResponse({'ok': False}, status=400)

def serie(request, serie):
    series = get_series_from_db()
    tomes = series.get(serie, [])

    # fournir aussi une séquence 1..total au template
    db_path = get_sqlite_path()
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        tomes_range = cur.execute("SELECT total FROM totaux WHERE serie = ?", (serie,)).fetchone()[0]
        tomes_range = range(1, tomes_range + 1)
        conn.commit()
    finally:
        conn.close()

    return render(request, 'serie.html', {"serie": serie, "tomes": tomes, "tomes_range": tomes_range})

def wishlist(request):
    db_path = get_sqlite_path()
    content = ''

    if request.method == 'POST':
        content = request.POST.get('content', '')
        try:
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            # tenter de mettre à jour la ligne existante
            cur.execute("UPDATE wishlist SET wishlist = ?", (content,))
            if cur.rowcount == 0:
                # si aucune ligne mise à jour, insérer
                cur.execute("INSERT INTO wishlist (wishlist) VALUES (?)", (content,))
            conn.commit()
            messages.success(request, '✔ Contenu sauvegardé')
        except Exception:
            messages.error(request, 'Erreur lors de la sauvegarde')
        finally:
            conn.close()
        return HttpResponseRedirect(request.path)

    # GET : lire la valeur si elle existe
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        row = cur.execute("SELECT wishlist FROM wishlist LIMIT 1").fetchone()
        if row:
            content = row[0] or ''
    except Exception:
        content = ''
    finally:
        try:
            conn.close()
        except Exception:
            pass

    return render(request, 'wishlist.html', {'content': content})


def delete_serie(request, serie):
    """Delete all tomes rows for a serie. Expects POST (AJAX) and returns JSON."""
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST required'}, status=400)
    db_path = get_sqlite_path()
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("DELETE FROM tomes WHERE serie = ?", (serie,))
        cur.execute("DELETE FROM totaux WHERE serie = ?", (serie,))
        conn.commit()
    finally:
        try:
            conn.close()
        except Exception:
            pass
    return JsonResponse({'ok': True})


def add_tome(request, serie):
    """AJAX endpoint: increment the total number of tomes for a serie.

    Returns JSON: {'ok': True, 'new_total': int}
    """
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST required'}, status=400)
    db_path = get_sqlite_path()
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        # check existing total
        cur.execute("SELECT total FROM totaux WHERE serie = ?", (serie,))
        row = cur.fetchone()
        if row:
            new_total = row[0] + 1
            cur.execute("UPDATE totaux SET total = ? WHERE serie = ?", (new_total, serie))
        else:
            new_total = 1
            cur.execute("INSERT INTO totaux (serie, total) VALUES (?, ?)", (serie, new_total))
        conn.commit()
    finally:
        try:
            conn.close()
        except Exception:
            pass
    return JsonResponse({'ok': True, 'new_total': new_total})

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

def add(request):

    added = False
    # handle classic POST add (server-side) -> redirect with flag to show popup
    if request.method == 'POST':
        new_serie = request.POST.get('serie_name')
        tot = request.POST.get('total')
        if new_serie:
            db_path = get_sqlite_path()
            try:
                conn = sqlite3.connect(db_path)
                cur = conn.cursor()
                cur.execute("SELECT 1 FROM tomes WHERE serie = ?", (new_serie,))
                exists = cur.fetchone()
                if not exists:
                    cur.execute("INSERT INTO tomes (serie) VALUES (?)", (new_serie,))
                    cur.execute("INSERT INTO totaux (serie, total) VALUES (?, ?)", (new_serie, tot))
                    added = True
                conn.commit()
            finally:
                try:
                    conn.close()
                except Exception:
                    pass
            if added:
                messages.success(request, '✔ Série ajoutée !')
                return HttpResponseRedirect(request.path)
            else:
                messages.success(request, 'Série déjà existante !')
                return HttpResponseRedirect(request.path)

    return render(request, 'add.html')