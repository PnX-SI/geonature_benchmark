#!/usr/bin/env python3
"""
Script de comparaison des résultats de benchmark Locust

Usage:
    python3 compare_benchmarks.py results/run1/stats.csv results/run2/stats.csv ...

    Cela va comparer les fichiers stats.csv de plusieurs lancements Locust
    et afficher un rapport de comparaison avec temps moyen par tâche.

Note:
    Les fichiers CSV doivent être générés par Locust avec:
    locust -f run_benchmark.py --csv=results/run1 ...
"""

import os
from posixpath import basename
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple

# Importer matplotlib de manière optionnelle
try:
    import matplotlib.pyplot as plt

    MATPLOTLIB_AVAILABLE = True
except (ImportError, AttributeError):
    MATPLOTLIB_AVAILABLE = False


def load_stats_file(filepath: str) -> pd.DataFrame:
    """Charge un fichier stats.csv de Locust"""
    try:
        df = pd.read_csv(filepath)
        return df
    except FileNotFoundError:
        print(f"❌ Fichier introuvable : {filepath}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur en lisant {filepath} : {e}")
        sys.exit(1)


def extract_task_stats(df: pd.DataFrame, run_name: str) -> pd.DataFrame:
    """
    Extrait les stats par tâche (exclut les résumés globaux)
    Retourne un DataFrame avec les colonnes: task_name, run_name, avg_time, min_time, max_time, median_time, requests, failures
    """
    # Nettoyage : supprimer les whitespaces dans les noms de colonnes
    df.columns = df.columns.str.strip()

    # Filtrer pour exclure les lignes de résumé
    # (Type vide, ou Name contenant 'Total' ou 'Aggregated')
    df_tasks = df[
        (df.get("Type", "").fillna("").str.strip() != "")
        & (df.get("Name", "").fillna("").str.strip() != "")
        & (~df.get("Name", "").str.contains("Total|Aggregated", case=False, na=False))
    ].copy()

    # Nettoyage des valeurs texte
    df_tasks = df_tasks.fillna("")

    # Normaliser les noms de colonnes pour gérer les variations
    col_mapping = {
        "Name": "task_name",
        "Average Response Time": "avg_time",
        "Median Response Time": "median_time",
        "Min Response Time": "min_time",
        "Max Response Time": "max_time",
        "Request Count": "requests",
        "Failure Count": "failures",
        "Average": "avg_time",
        "Median": "median_time",
        "Min": "min_time",
        "Max": "max_time",
        "Requests": "requests",
        "Failures": "failures",
        "# requests": "requests",
        "# failures": "failures",
    }

    # Renommer les colonnes disponibles
    rename_dict = {
        old: new for old, new in col_mapping.items() if old in df_tasks.columns
    }
    df_tasks.rename(columns=rename_dict, inplace=True)

    # Ajouter la colonne run_name
    df_tasks["run_name"] = run_name

    # Garder seulement les colonnes pertinentes qui existent
    cols_to_keep = [
        "task_name",
        "run_name",
        "avg_time",
        "median_time",
        "min_time",
        "max_time",
        "requests",
        "failures",
    ]
    cols_available = [c for c in cols_to_keep if c in df_tasks.columns]
    numeric_cols = [
        "avg_time",
        "median_time",
        "min_time",
        "max_time",
        "requests",
        "failures",
    ]
    for col in numeric_cols:
        if col in df_tasks.columns:
            df_tasks[col] = pd.to_numeric(df_tasks[col], errors="coerce")

    return df_tasks[cols_available]


def print_task_comparison(task_stats_list: List[pd.DataFrame]) -> None:
    """Affiche une comparaison détaillée par tâche"""

    print("\n" + "=" * 140)
    print("COMPARAISON PAR TÂCHE — TEMPS MOYEN (ms)")
    print("=" * 140)

    # Fusionner tous les stats en un seul DataFrame
    all_stats = pd.concat(task_stats_list, ignore_index=True)

    # Obtenir les tâches uniques
    unique_tasks = sorted(all_stats["task_name"].unique())

    # Créer un pivot pour faciliter la comparaison
    pivot_avg = all_stats.pivot_table(
        values="avg_time", index="task_name", columns="run_name", aggfunc="first"
    )

    print("\n📊 TEMPS MOYEN PAR TÂCHE\n")
    print(pivot_avg.to_string())

    # Afficher les variations vs baseline (première colonne)
    if len(pivot_avg.columns) > 1:
        baseline_col = pivot_avg.columns[0]
        baseline_values = pivot_avg[baseline_col]

        print(f"\n\n📈 VARIATIONS PAR RAPPORT À '{baseline_col}'\n")

        for col in pivot_avg.columns[1:]:
            print(f"\n  vs {col}:")
            for task in pivot_avg.index:
                baseline = baseline_values[task]
                current = pivot_avg.loc[task, col]

                if pd.notna(baseline) and pd.notna(current):
                    diff = current - baseline
                    pct = (diff / baseline) * 100 if baseline != 0 else 0
                    sign = "📈" if diff > 0 else "📉" if diff < 0 else "⏸️ "

                    print(f"    {sign} {task:<50} : {pct:>+7.1f}% ({diff:>+7.2f} ms)")


def print_slowest_tasks(task_stats_list: List[pd.DataFrame], top_n: int = 5) -> None:
    """Affiche les tâches les plus lentes"""

    print("\n" + "=" * 140)
    print(f"TOP {top_n} — TÂCHES LES PLUS LENTES")
    print("=" * 140)

    all_stats = pd.concat(task_stats_list, ignore_index=True)

    # Grouper par tâche et calculer le temps moyen sur tous les lancements
    avg_by_task = (
        all_stats.groupby("task_name")["avg_time"].mean().sort_values(ascending=False)
    )

    print("\n")
    for i, (task, avg_time) in enumerate(avg_by_task.head(top_n).items(), 1):
        print(f"  {i}. {task:<50} : {avg_time:>8.2f} ms")


def print_fastest_tasks(task_stats_list: List[pd.DataFrame], top_n: int = 5) -> None:
    """Affiche les tâches les plus rapides"""

    print("\n" + "=" * 140)
    print(f"TOP {top_n} — TÂCHES LES PLUS RAPIDES")
    print("=" * 140)

    all_stats = pd.concat(task_stats_list, ignore_index=True)

    # Grouper par tâche et calculer le temps moyen sur tous les lancements
    avg_by_task = (
        all_stats.groupby("task_name")["avg_time"].mean().sort_values(ascending=True)
    )

    print("\n")
    for i, (task, avg_time) in enumerate(avg_by_task.head(top_n).items(), 1):
        print(f"  {i}. {task:<50} : {avg_time:>8.2f} ms")


def generate_task_comparison_chart(task_stats_list: List[pd.DataFrame]) -> None:
    """Génère des graphiques de comparaison par tâche"""
    if not MATPLOTLIB_AVAILABLE:
        print("⚠️  matplotlib non disponible, graphiques non générés")
        return

    all_stats = pd.concat(task_stats_list, ignore_index=True)

    # Créer un pivot pour faciliter la comparaison
    pivot_avg = all_stats.pivot_table(
        values="avg_time", index="task_name", columns="run_name", aggfunc="first"
    )

    # Créer le graphique
    fig, ax = plt.subplots(figsize=(14, max(6, len(pivot_avg) * 0.3)))

    # Graphique horizontal pour mieux lire les noms de tâches
    pivot_avg.plot(kind="barh", ax=ax, width=0.8)

    ax.set_xlabel("Temps moyen (ms)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Tâche", fontsize=11, fontweight="bold")
    ax.set_title(
        "Comparaison des temps moyens par tâche", fontsize=13, fontweight="bold"
    )
    ax.legend(title="Lancement", bbox_to_anchor=(1.05, 1), loc="upper left")
    ax.grid(axis="x", alpha=0.3)

    plt.tight_layout()
    plt.savefig("task_comparison.png", dpi=100, bbox_inches="tight")
    print(f"\n📈 Graphique sauvegardé : task_comparison.png")


def generate_detailed_csv_export(task_stats_list: List[pd.DataFrame]) -> None:
    """Exporte les statistiques détaillées par tâche en CSV"""

    all_stats = pd.concat(task_stats_list, ignore_index=True)

    # Trier et exporter
    output_file = "task_comparison_detailed.csv"
    all_stats.sort_values(["task_name", "run_name"]).to_csv(output_file, index=False)
    print(f"💾 Détails exportés : {output_file}")

    # Créer aussi un pivot
    pivot_avg = all_stats.pivot_table(
        values="avg_time", index="task_name", columns="run_name", aggfunc="first"
    )

    output_pivot = "task_comparison_pivot.csv"
    pivot_avg.to_csv(output_pivot)
    print(f"💾 Pivot exporté : {output_pivot}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nUsage:")
        print("  python3 compare_benchmarks.py <file1.csv> <file2.csv> [file3.csv] ...")
        print("\nExemple:")
        print(
            "  python3 compare_benchmarks.py results/run1/stats.csv results/run2/stats.csv"
        )
        sys.exit(1)

    # Charger les fichiers
    csv_files = sys.argv[1:]
    print(f"📂 Chargement de {len(csv_files)} fichier(s)...")

    task_stats_list = []
    for filepath in csv_files:
        # Utiliser le nom du dossier parent comme identifiant du lancement
        run_name = os.path.basename(filepath)
        print(f"  ✓ {run_name} ({filepath})")

        df = load_stats_file(filepath)
        task_stats = extract_task_stats(df, run_name)
        task_stats_list.append(task_stats)

    # Afficher les résultats
    print_task_comparison(task_stats_list)
    print_slowest_tasks(task_stats_list, top_n=5)
    print_fastest_tasks(task_stats_list, top_n=5)

    # Générer les graphiques et exports
    generate_task_comparison_chart(task_stats_list)
    generate_detailed_csv_export(task_stats_list)

    print("\n" + "=" * 140)
    print("✅ Comparaison terminée")
    print("=" * 140 + "\n")


if __name__ == "__main__":
    main()
