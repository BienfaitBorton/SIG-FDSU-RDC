from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import psycopg2

from app.config import DATABASE_URL

SOURCE = "pilote_demo"


@dataclass(frozen=True)
class PilotProfile:
    population: int
    couverture_2g: bool
    couverture_3g: bool
    couverture_4g: bool
    couverture_5g: bool
    centre_sante: bool
    ecole_secondaire: bool
    activite_principale: str
    activite_secondaire: str
    potentiel_agricole: str
    potentiel_commercial: str
    score_connectivite: float
    score_potentiel: float
    score_priorite_fdsu: float
    niveau_enclavement: str
    recommandation: str


LOCALITY_PROFILES = [
    PilotProfile(8200, True, True, False, False, True, True, "Agriculture vivriere", "Commerce local", "fort", "moyen", 22, 84, 92, "fort", "Priorite CCN: localite peuplee, services presents, 4G absente."),
    PilotProfile(6400, True, False, False, False, True, True, "Cacao et cultures vivrieres", "Petit commerce", "fort", "moyen", 18, 81, 89, "fort", "Priorite CCN: potentiel agricole fort et connectivite faible."),
    PilotProfile(5100, True, True, False, False, True, True, "Riziculture", "Marche rural", "fort", "fort", 28, 78, 86, "moyen", "Priorite CCN: bassin agricole avec relais social existant."),
    PilotProfile(4300, True, False, False, False, True, True, "Elevage", "Agriculture vivriere", "fort", "moyen", 20, 76, 84, "fort", "Priorite CCN: absence 4G et potentiel productif."),
    PilotProfile(3900, True, True, False, False, True, True, "Manioc", "Peche", "fort", "moyen", 32, 74, 80, "moyen", "Priorite CCN: localite eligible apres verification terrain."),
    PilotProfile(12500, True, True, True, False, True, True, "Commerce frontalier", "Agriculture", "moyen", "fort", 62, 82, 68, "faible", "Temoin non prioritaire localite: 4G deja presente."),
    PilotProfile(2800, True, False, False, False, True, True, "Agriculture vivriere", "Artisanat", "fort", "faible", 24, 70, 58, "moyen", "Temoin: population sous le seuil de 3000 habitants."),
    PilotProfile(7200, True, True, False, False, False, True, "Cafe", "Commerce local", "fort", "moyen", 25, 79, 63, "fort", "Temoin: centre de sante a completer avant priorisation."),
    PilotProfile(5700, True, False, False, False, True, False, "Mais", "Petit commerce", "fort", "moyen", 21, 75, 61, "fort", "Temoin: ecole secondaire a completer avant priorisation."),
    PilotProfile(9300, True, True, False, False, True, True, "Palmier a huile", "Transformation artisanale", "fort", "fort", 26, 86, 94, "fort", "Priorite CCN: fort potentiel productif et absence 4G."),
    PilotProfile(4600, True, True, False, False, True, True, "Peche", "Agriculture", "fort", "moyen", 34, 73, 78, "moyen", "Priorite CCN secondaire: couverture a renforcer."),
    PilotProfile(6800, True, False, False, False, True, True, "Coton", "Commerce rural", "fort", "fort", 19, 83, 91, "fort", "Priorite CCN: connectivite tres faible et services de base presents."),
]

TERRITORY_PROFILES = [
    PilotProfile(540000, True, True, False, False, True, True, "Agriculture et commerce rural", "Transformation agricole", "fort", "fort", 24, 88, 93, "fort", "Territoire prioritaire: potentiel economique fort et faible connectivite."),
    PilotProfile(420000, True, False, False, False, True, True, "Agriculture vivriere", "Exploitation forestiere artisanale", "fort", "moyen", 19, 82, 90, "fort", "Territoire prioritaire: deficit connectivite et potentiel productif."),
    PilotProfile(610000, True, True, False, False, True, True, "Commerce regional", "Agriculture", "moyen", "fort", 35, 85, 87, "moyen", "Territoire prioritaire: connectivite encore faible pour l'activite economique."),
    PilotProfile(390000, True, True, True, False, True, True, "Agriculture", "Commerce", "fort", "fort", 58, 86, 64, "faible", "Temoin: connectivite moins faible, priorite reduite."),
    PilotProfile(280000, True, False, False, False, True, True, "Elevage", "Agriculture", "fort", "moyen", 31, 76, 81, "fort", "Territoire prioritaire secondaire: besoin de verification terrain."),
    PilotProfile(730000, True, True, False, False, True, True, "Commerce fluvial", "Agriculture", "fort", "fort", 27, 89, 95, "fort", "Territoire prioritaire: corridor economique peu connecte."),
]


def fetch_localities(cur, limit: int) -> list[dict[str, Any]]:
    cur.execute(
        """
        SELECT l.id, l.nom, t.nom AS territoire, p.nom AS province, z.code AS zone
        FROM localites l
        JOIN groupements g ON g.id = l.parent_id
        JOIN collectivites c ON c.id = g.parent_id
        JOIN territoires t ON t.id = c.parent_id
        JOIN provinces p ON p.id = t.parent_id
        JOIN zones z ON z.id = p.parent_id
        WHERE z.code IN ('ND', 'ET', 'SD', 'OT')
        ORDER BY
            CASE z.code WHEN 'ND' THEN 1 WHEN 'ET' THEN 2 WHEN 'SD' THEN 3 ELSE 4 END,
            t.nom,
            l.nom
        LIMIT %s
        """,
        (limit,),
    )
    return [
        {"id": row[0], "nom": row[1], "territoire": row[2], "province": row[3], "zone": row[4]}
        for row in cur.fetchall()
    ]


def fetch_territories(cur, limit: int) -> list[dict[str, Any]]:
    cur.execute(
        """
        SELECT t.id, t.nom, p.nom AS province, z.code AS zone
        FROM territoires t
        JOIN provinces p ON p.id = t.parent_id
        JOIN zones z ON z.id = p.parent_id
        WHERE z.code = 'ND'
        ORDER BY t.nom
        LIMIT %s
        """,
        (limit,),
    )
    return [{"id": row[0], "nom": row[1], "province": row[2], "zone": row[3]} for row in cur.fetchall()]


def clear_previous_seed(cur) -> None:
    for table in [
        "fdsu_priority_scores",
        "economic_activities",
        "public_services",
        "connectivity_profiles",
        "development_challenges",
        "territorial_profiles",
    ]:
        cur.execute(f"DELETE FROM {table} WHERE source = %s", (SOURCE,))


def insert_profile(cur, *, localite_id: int | None, territoire_id: int | None, profile: PilotProfile) -> None:
    cur.execute(
        """
        INSERT INTO territorial_profiles
            (localite_id, territoire_id, population, niveau_enclavement, source, observation)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (localite_id, territoire_id, profile.population, profile.niveau_enclavement, SOURCE, "Profil pilote de demonstration."),
    )
    cur.execute(
        """
        INSERT INTO connectivity_profiles
            (localite_id, territoire_id, couverture_2g, couverture_3g, couverture_4g, couverture_5g,
             score_connectivite, source, observation)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            localite_id,
            territoire_id,
            profile.couverture_2g,
            profile.couverture_3g,
            profile.couverture_4g,
            profile.couverture_5g,
            profile.score_connectivite,
            SOURCE,
            "Profil pilote de demonstration.",
        ),
    )
    cur.execute(
        """
        INSERT INTO public_services
            (localite_id, territoire_id, centre_sante, ecole_primaire, ecole_secondaire,
             marche, electricite, source, observation)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (localite_id, territoire_id, profile.centre_sante, None, profile.ecole_secondaire, None, None, SOURCE, "Profil pilote de demonstration."),
    )
    cur.execute(
        """
        INSERT INTO economic_activities
            (localite_id, territoire_id, activite_principale, activite_secondaire,
             potentiel_agricole, potentiel_minier, potentiel_commercial, potentiel_numerique,
             score_potentiel, source, observation)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            localite_id,
            territoire_id,
            profile.activite_principale,
            profile.activite_secondaire,
            profile.potentiel_agricole,
            None,
            profile.potentiel_commercial,
            None,
            profile.score_potentiel,
            SOURCE,
            "Profil pilote de demonstration.",
        ),
    )
    cur.execute(
        """
        INSERT INTO development_challenges
            (localite_id, territoire_id, niveau_enclavement, defis, source, observation)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (localite_id, territoire_id, profile.niveau_enclavement, "Connectivite et acces aux services a verifier.", SOURCE, "Profil pilote de demonstration."),
    )
    cur.execute(
        """
        INSERT INTO fdsu_priority_scores
            (localite_id, territoire_id, score_connectivite, score_potentiel,
             score_priorite_fdsu, recommandation, source, observation)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            localite_id,
            territoire_id,
            profile.score_connectivite,
            profile.score_potentiel,
            profile.score_priorite_fdsu,
            profile.recommandation,
            SOURCE,
            "Profil pilote de demonstration.",
        ),
    )


def main() -> None:
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            localities = fetch_localities(cur, len(LOCALITY_PROFILES))
            territories = fetch_territories(cur, len(TERRITORY_PROFILES))
            if len(localities) < len(LOCALITY_PROFILES):
                raise RuntimeError("Nombre insuffisant de localites existantes pour le pilote.")
            if len(territories) < len(TERRITORY_PROFILES):
                raise RuntimeError("Nombre insuffisant de territoires existants pour le pilote.")

            clear_previous_seed(cur)
            for entity, profile in zip(localities, LOCALITY_PROFILES):
                insert_profile(cur, localite_id=entity["id"], territoire_id=None, profile=profile)
            for entity, profile in zip(territories, TERRITORY_PROFILES):
                insert_profile(cur, localite_id=None, territoire_id=entity["id"], profile=profile)
        conn.commit()

    print(f"Seed decision pilot termine: {len(LOCALITY_PROFILES)} localites, {len(TERRITORY_PROFILES)} territoires, source={SOURCE}")


if __name__ == "__main__":
    main()
