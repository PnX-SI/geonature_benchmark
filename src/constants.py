TASK_NAMES = {
    "general_stats": "home/general_stats | Accueil · Statistiques générales",
    "acq_frameworks": "meta/acquisition_frameworks | Métadonnées · Cadres d'acquisition",
    "datasets": "meta/datasets | Métadonnées · Jeux de données",
    "obs_bbox": "synthese/for_web?geom=bbox | Synthèse · Filtre bbox",
    "obs_complex_poly": "synthese/for_web?geom=complex_polygon | Synthèse · Filtre polygone complexe",
    "obs_commune": "synthese/for_web?area=COM | Synthèse · Filtre commune",
    "obs_dep": "synthese/for_web?area=DEP | Synthèse · Filtre département",
    "obs_reg": "synthese/for_web?area=REG | Synthèse · Filtre région",
    "obs_tree_taxon": "synthese/for_web?filter=tree_taxon | Synthèse · Filtre arbre taxonomique",
    "obs_regulation": "synthese/for_web?filter=regulation | Synthèse · Filtre réglementation",
    "export_csv_1000": "synthese/export_observations?format=csv&n=1000 | Synthèse · Export CSV 1 000 obs",
    "export_status": "synthese/export_statuts | Synthèse · Export statuts",
    "export_taxons": "synthese/export_taxons | Synthèse · Export taxons",
    "default_nomenclatures": "synthese/defaultsNomenclatures | Synthèse · Nomenclatures par défault",
    "occtax_releves": "occtax/releves | OccTax · Liste des relevés",
    "geo_areas_with_geom": "geo/areas?geom=true | Ref Geo · Aires avec géométrie",
    "geo_areas_without_geom": "geo/areas?geom=false | Ref Geo · Aires sans géométrie",
    "validation_obs": "validation/observations?limit=1000 | Validation · 1 000 obs à valider",
    "validation_last": "validation?sort=validation_date:desc | Validation · Dernières validations",
    "monitorings_modules": "monitorings/modules | Monitorings · Liste des modules",
}

# ---------------------------------------------------------------------------
# Synthèse
# ---------------------------------------------------------------------------

SYNTHESE_OBS_URL = "/synthese/for_web"
SYNTHESE_EXPORT_URL = "/synthese/export_observations"
SYNTHESE_EXPORT_STATUS_URL = "/synthese/export_statuts"
SYNTHESE_EXPORT_TAXON_URL = "/synthese/export_taxons"