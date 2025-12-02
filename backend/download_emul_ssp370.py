#!/usr/bin/env python3
"""
Script pour lister et télécharger les fichiers EMUL ssp370 pour pr et tas depuis data.gouv.fr
Usage: poetry run python download_emul_ssp370.py [--download]
"""

import sys
import csv
import argparse
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import shutil

def generate_emul_ssp370_urls(runs: list = None, variables: list = ["prAdjust", "tasAdjust"]):
    """
    Génère les URLs pour tous les fichiers EMUL ssp370 disponibles.
    
    Args:
        runs: Liste des runs à télécharger (par défaut: r1i1p1f1 à r10i1p1f1)
        variables: Liste des variables à rechercher (par défaut: prAdjust, tasAdjust)
    
    Returns:
        Liste de dictionnaires avec les informations des fichiers
    """
    if runs is None:
        # Générer tous les membres d'ensemble possibles (r1 à r10)
        runs = [f"r{i}i1p1f1" for i in range(1, 11)]
    
    files = []
    base_url = "https://object.files.data.gouv.fr/meteofrance-drias/SocleM-Climat-2025/EMULATEUR/METROPOLE/ALPX-12/MPI-ESM1-2-LR"
    rcm = "CNRM-ALADIN63-emul-CNRM-UNET11-tP22"
    version = "version-hackathon-102025"
    
    # Patterns de noms de fichiers
    filename_patterns = {
        "prAdjust": "prAdjust_FR-Metro_MPI-ESM1-2-LR_ssp370_{run}_CNRM_{rcm}_v1-r1_MF-CDFt-SAFRAN-1985-2014_day_20150101-21001231.nc",
        "tasAdjust": "tasAdjust_FR-Metro_MPI-ESM1-2-LR_ssp370_{run}_CNRM_{rcm}_v1-r1_MF-CDFt-ANASTASIA-SAFRAN-1985-2014_day_20150101-21001231.nc"
    }
    
    for run in runs:
        for variable in variables:
            filename = filename_patterns[variable].format(run=run, rcm=rcm)
            url = f"{base_url}/{run}/{rcm}/ssp370/day/{variable}/{version}/{filename}"
            
            files.append({
                'variable': variable,
                'gcm': 'MPI-ESM1-2-LR',
                'run': run,
                'rcm': rcm,
                'url': url,
                'filename': filename
            })
    
    return files


def check_url_exists(url: str) -> bool:
    """
    Vérifie si une URL existe en faisant une requête HEAD.
    
    Args:
        url: URL à vérifier
    
    Returns:
        True si l'URL existe, False sinon
    """
    try:
        req = Request(url, method='HEAD')
        req.add_header('User-Agent', 'Mozilla/5.0')
        with urlopen(req) as response:
            return response.status == 200
    except (URLError, HTTPError):
        return False


def find_emul_ssp370_files(catalog_path: Path = None, variables: list = ["prAdjust", "tasAdjust"], check_availability: bool = True):
    """
    Trouve tous les fichiers EMUL ssp370 pour les variables spécifiées.
    Génère les URLs pour tous les membres d'ensemble (r1 à r10) car le catalogue peut être incomplet.
    
    Args:
        catalog_path: Chemin vers le fichier CSV du catalogue (optionnel, utilisé pour référence)
        variables: Liste des variables à rechercher (par défaut: prAdjust, tasAdjust)
        check_availability: Si True, vérifie que les URLs existent réellement
    
    Returns:
        Liste de dictionnaires avec les informations des fichiers trouvés
    """
    # Toujours générer les URLs pour tous les membres (r1 à r10)
    # Le catalogue peut être incomplet
    print("📝 Génération des URLs pour tous les membres d'ensemble (r1 à r10)...")
    files = generate_emul_ssp370_urls(variables=variables)
    
    # Vérifier la disponibilité des fichiers si demandé
    if check_availability:
        print(f"🔍 Vérification de la disponibilité de {len(files)} fichiers...")
        available_files = []
        for i, file_info in enumerate(files, 1):
            print(f"   [{i}/{len(files)}] Vérification: {file_info['filename']}", end=' ... ', flush=True)
            if check_url_exists(file_info['url']):
                available_files.append(file_info)
                print("✅")
            else:
                print("❌")
        files = available_files
        print(f"\n✅ {len(files)} fichier(s) disponible(s) sur {len(generate_emul_ssp370_urls(variables=variables))}")
    
    return files


def download_file(url: str, output_path: Path, chunk_size: int = 8192 * 8):
    """
    Télécharge un fichier avec barre de progression simple.
    
    Args:
        url: URL du fichier à télécharger
        output_path: Chemin de destination
        chunk_size: Taille des chunks pour le téléchargement
    
    Returns:
        True si succès, False sinon
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Créer une requête avec User-Agent pour éviter les blocages
        req = Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0')
        
        # Télécharger le fichier
        with urlopen(req) as response:
            total_size = int(response.headers.get('Content-Length', 0))
            
            with open(output_path, 'wb') as f:
                downloaded = 0
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    # Afficher la progression si la taille est connue
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\r   Progression: {downloaded / (1024*1024):.1f} MB / {total_size / (1024*1024):.1f} MB ({percent:.1f}%)", end='', flush=True)
                    else:
                        print(f"\r   Téléchargé: {downloaded / (1024*1024):.1f} MB", end='', flush=True)
        
        print()  # Nouvelle ligne après la progression
        return True
    except URLError as e:
        print(f"\n❌ Erreur URL lors du téléchargement de {url}: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Erreur lors du téléchargement de {url}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Lister et télécharger les fichiers EMUL ssp370 pour pr et tas"
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help="Télécharger les fichiers trouvés (sinon, seulement les lister)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data",
        help="Répertoire de destination pour les téléchargements (défaut: data)"
    )
    parser.add_argument(
        "--catalog",
        type=str,
        default="data/meteofrance_drias_catalog.csv",
        help="Chemin vers le fichier catalogue CSV (défaut: data/meteofrance_drias_catalog.csv)"
    )
    parser.add_argument(
        "--no-check",
        action="store_true",
        help="Ne pas vérifier la disponibilité des URLs (plus rapide mais peut télécharger des fichiers inexistants)"
    )
    args = parser.parse_args()
    
    # Chemins
    script_dir = Path(__file__).parent
    catalog_path = script_dir / args.catalog
    output_dir = script_dir / args.output_dir
    
    print("🔍 Recherche des fichiers EMUL ssp370 pour pr et tas...")
    if catalog_path.exists():
        print(f"📁 Catalogue: {catalog_path}")
    else:
        print("📝 Génération des URLs depuis le pattern connu")
    print()
    
    # Trouver les fichiers
    files = find_emul_ssp370_files(
        catalog_path if catalog_path.exists() else None,
        variables=["prAdjust", "tasAdjust"],
        check_availability=not args.no_check
    )
    
    if not files:
        print("❌ Aucun fichier trouvé")
        sys.exit(1)
    
    # Grouper par variable
    pr_files = [f for f in files if f['variable'] == 'prAdjust']
    tas_files = [f for f in files if f['variable'] == 'tasAdjust']
    
    print(f"📊 Fichiers trouvés:")
    print(f"   - prAdjust: {len(pr_files)} fichier(s)")
    print(f"   - tasAdjust: {len(tas_files)} fichier(s)")
    print()
    
    # Afficher les détails
    print("📋 Détails des fichiers:")
    print()
    
    all_files = pr_files + tas_files
    for i, file_info in enumerate(all_files, 1):
        print(f"{i}. {file_info['variable']}")
        print(f"   GCM: {file_info['gcm']}")
        print(f"   Run: {file_info['run']}")
        print(f"   RCM: {file_info['rcm']}")
        print(f"   Fichier: {file_info['filename']}")
        print(f"   URL: {file_info['url']}")
        print()
    
    # Télécharger si demandé
    if args.download:
        print(f"⬇️  Téléchargement vers: {output_dir}")
        print()
        
        success_count = 0
        fail_count = 0
        
        for file_info in all_files:
            output_path = output_dir / file_info['filename']
            
            # Vérifier si le fichier existe déjà
            if output_path.exists():
                print(f"⏭️  Fichier déjà présent: {file_info['filename']}")
                success_count += 1
                continue
            
            print(f"⬇️  Téléchargement: {file_info['filename']}")
            if download_file(file_info['url'], output_path):
                success_count += 1
                print(f"✅ Téléchargé: {file_info['filename']}")
            else:
                fail_count += 1
                print(f"❌ Échec: {file_info['filename']}")
            print()
        
        print(f"📊 Résumé:")
        print(f"   ✅ Succès: {success_count}")
        print(f"   ❌ Échecs: {fail_count}")
    else:
        print("💡 Pour télécharger les fichiers, utilisez l'option --download")
        print(f"   Exemple: poetry run python {Path(__file__).name} --download")


if __name__ == "__main__":
    main()

