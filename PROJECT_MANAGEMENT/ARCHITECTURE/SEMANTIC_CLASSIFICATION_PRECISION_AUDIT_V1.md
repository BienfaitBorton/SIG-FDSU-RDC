# Audit de précision — Classification sémantique CENI v1

## Verdict

L’audit porte sur 23 604 écoles et utilise un échantillonnage déterministe (`seed=20260716`). Les frontières de mots sont strictes et le moteur ne consulte que `source_name`; les propriétés brutes et identifiants ne participent pas à la détection. Aucun cas interdit EP/INST n’a été identifié dans la population classée. Ce contrôle lexical ne remplace pas une validation métier de terrain.

## Répartition exacte des écoles

| Famille lexicale | Nombre |
|---|---:|
| EP / E.P. | 17 387 |
| INST / INSTITUT | 4 684 |
| ÉCOLE | 129 |
| COMPLEXE SCOLAIRE | 371 |
| COLLÈGE | 669 |
| LYCÉE | 323 |
| UNIVERSITÉ | 10 |
| Autres règles | 31 |
| **Total** | **23 604** |

Répartition technique : `{'SCHOOL_EXPLICIT': 1422, 'CS_CONTEXT_SCOLAIRE': 19, 'SCHOOL_EP': 17387, 'SCHOOL_NAME': 3314, 'SCHOOL_INST': 1462}`.

## Contrôle des expressions courtes

- `EP` : motif de préfixe strict `^EP(?:\s|$)`; 17 387 occurrences conformes.
- `INST` : motif de préfixe strict `^INST(?:\s|$)`; 1 462 occurrences conformes.
- `CS` : jamais classé seul; contexte scolaire ou sanitaire supplémentaire obligatoire.
- `INSTALLATION`, `INSTITUTION PUBLIQUE`, `DEPARTEMENT` : aucune correspondance à EP/INST.
- Abréviation nue et identifiant technique : rejet explicite vers « Non classifié ».
- Faux positifs correspondant aux motifs interdits dans la population : **0**.

## Matrice de validation

| Niveau | Critère | Nombre | Action |
|---|---|---:|---|
| Classification certaine | Forme scolaire explicite ou mot complet ÉCOLE/INSTITUT | 4 736 | Contrôle métier par sondage |
| Classification probable | EP ou INST strictement en préfixe | 18 849 | Validation humaine par lot recommandée |
| À vérifier | CS désambiguïsé par un contexte scolaire | 19 | Revue individuelle obligatoire |
| Faux positif identifié | Collision lexicale démontrée | 0 | Annulation de la classification |

## Confiances corrigées

- forme explicite (`ÉCOLE PRIMAIRE`, `COMPLEXE SCOLAIRE`, `COLLÈGE`, `LYCÉE`) : 0,99;
- mot complet `ÉCOLE` ou `INSTITUT` : 0,97;
- `EP` strictement au début : **0,92**, abaissé de 0,95;
- `INST` strictement au début : **0,86**, abaissé de 0,92;
- `CS` avec contexte scolaire : 0,76 et « À vérifier »;
- conflit, abréviation nue, identifiant technique ou contexte insuffisant : 0 et « Non classifié ».

## Statistiques après durcissement

| Indicateur | Nombre |
|---|---:|
| Écoles confirmées | 4 736 |
| Écoles probables | 18 849 |
| À vérifier | 19 |
| Non classifiés | 6 959 |
| Classifications annulées comme faux positifs | 0 |

La précision lexicale observée sur les 160 objets échantillonnés est de 100 % au regard des critères formels des règles (préfixe ou mot complet). Cette valeur n’est pas une précision terrain : les 18 849 écoles probables doivent rester soumises à un contrôle métier par échantillonnage stratifié.

## Cas nommés et tests négatifs

- `EP. LOSONDJU` → École, règle EP, confiance 0,92.
- `INST. ELONGA` → École, règle INST, confiance 0,86.
- `INSTALLATION X`, `INSTITUTION PUBLIQUE`, `DEPARTEMENT X`, `CS`, nom vide et `CENI-EP-001` → Non classifié.
- Aucun nom du registre composé uniquement de `EP` ou `INST` n’a été observé.

## Échantillons contrôlés

### 50 objets classés par EP

| Nom source | Règle | Mot-clé | Catégorie proposée | Confiance | Justification | Province | Territoire |
|---|---|---|---|---:|---|---|---|
| E.P NKAMBA | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Lomami | Luilu |
| E.P LISIETE | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Mongala | Lisala |
| EP. MBODI | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Sankuru | Katako-Kombe |
| EP KALUNDJA | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Sud-Kivu | Fizi |
| E.P. ITAPANYA | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Kasai | Mweka |
| E.P. DJEMA GARRY | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Tshuapa | Boende |
| EP NDUBA IMBA | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Tanganyika | Kongolo |
| E.P 2 NTALAJA | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Kasai Oriental | Kabeya-Kamwanga |
| EP 1 KAPATA | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Kwango | Kahemba |
| EP UKETHO II | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Ituri | Mahagi |
| E.P. KASIKA | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Sud-Kivu | Mwenga |
| E.P. GBITA | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Haut-Uele | Niangara |
| EP PONT KWANGO CAS | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Kwango | Kasongo-Lunda |
| EP BALOMOTWA | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Haut-Katanga | Mitwaba |
| E.P KEREKERE | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Ituri | Mahagi |
| E.P. GBANGBATI | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Haut-Uele | Dungu |
| E.P. MALAMBWE | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Haut-Katanga | Kasenga |
| E.P. KABAYA | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Lomami | Kabinda |
| E.P. NDEO MANONO | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Maniema | Kibombo |
| E.P. LAMPA | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Kongo Central | Tshela |
| E.P. KILOMBO | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Kongo Central | Mbanza-Ngungu |
| E.P. 3 KIMPESE | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Kongo Central | Mbanza-Ngungu |
| E.P. MUSANDJI/YELENGE | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Kwilu | Bulungu |
| E.P DIBUMBA/TSHIKAPA | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Kasai | Kamonia |
| EP KIMUMA | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Sankuru | Lubefu |
| EP AVAKUBI | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Tshopo | Bafwasende |
| E.P. MUBUNGI | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Kwilu | Bulungu |
| EP BURHINYI | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Sud-Kivu | Mwenga |
| E.P. TSHIJIBA II | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Kasai Oriental | Miabi |
| EP KIKIMI/CS MAYUMA | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Kinshasa | Non renseigné |
| EP LIKOSO | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Tshopo | Yahuma |
| E.P. KAPELEPELE | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Kasai Central | Dimbelenge |
| E.P. TSHILETA | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Sankuru | Lusambo |
| EP YAMOKONDU | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Mongala | Bumba |
| EP.KINKOSI/MABANZA | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Kwango | Kasongo-Lunda |
| E.P. ABBE EKOFO | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Tshuapa | Boende |
| EP KYMUL LA VICTOIRE | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Haut-Katanga | Kambove |
| E.P. KENGE | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Tshopo | Bafwasende |
| EP. LIBELA | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Mongala | Bumba |
| E.P KAMENANKELA | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Lualaba | Dilolo |
| E.P. KABENGA | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Kasai | Non renseigné |
| E.P. WANYA | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Sankuru | Kole |
| E.P. 2 ZOLANA | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Kongo Central | Tshela |
| EP BOKPAMBA | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Tshopo | Basoko |
| EP MBANDIKO | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Kinshasa | Non renseigné |
| EP BIONGUE | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Lomami | Lubao |
| EP KANGOLE | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Haut-Lomami | Malemba-Nkulu |
| E.P TSHINKOLO | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Kasai | Luebo |
| E.P. LOBANGA/NGELE | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Equateur | Ingende |
| E.P. MATAFA | SCHOOL_EP | EP | École | 0.92 | Le nom contient l’indice lexical français explicite « EP », associé à la catégorie « École ». | Haut-Uele | Faradje |
### 50 objets classés par INST

| Nom source | Règle | Mot-clé | Catégorie proposée | Confiance | Justification | Province | Territoire |
|---|---|---|---|---:|---|---|---|
| INST. TECH. AGRICOLE MONDONGO | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Mongala | Lisala |
| INST. TECH. COM. DE KANANGA | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Kasai Central | Non renseigné |
| INST. SCIENTIFIQUE KIMVUKA | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Kwilu | Gungu |
| INST. COL. MAYU | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Kwilu | Bulungu |
| INST. TECH. PROF. KASANGUNDA | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Kwilu | Idiofa |
| INST, NKONGO-MBENZA | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Kongo Central | Seke-Banza |
| INST. KABONGO DIBWE | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Haut-Lomami | Kabongo |
| INST. NSIENZUNU | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Kwilu | Bulungu |
| INST. PROFESSIONNEL MOGOYA | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Tshopo | Isangi |
| INST.LUNUNGU | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Kwango | Kasongo-Lunda |
| INST. AM"WENU | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Kasai Oriental | Tshilenge |
| INST. MATONDO | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Kwilu | Bulungu |
| INST. INERA | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Haut-Lomami | Kaniama |
| INST. NTO MBANDU MBEKO | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Kwilu | Masi-Manimba |
| INST. MALAVU | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Kinshasa | Non renseigné |
| INST. MIKA MPERE/ZABA | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Kwilu | Bulungu |
| INST. LINGOMO | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Kinshasa | Non renseigné |
| INST. TECH. AGRICOLE DIKOMBO | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Kasai Oriental | Kabeya-Kamwanga |
| INST. LOWA | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Nord-Kivu | Walikale |
| INST. PROFESSIONNEL BINGA | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Mongala | Lisala |
| INST. KABAMBA | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Kasai Central | Demba |
| INST. TECH. AGRICOLE DILUBA | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Haut-Lomami | Bukama |
| INST, IWONDO/NKOKOMAMBA | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Kwango | Kasongo-Lunda |
| INST. TUSAIDIANE | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Lualaba | Mutshatsha |
| INST. MAKIAMBI | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Nord-Kivu | Walikale |
| INST LUGHENDO | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Nord-Kivu | Oicha |
| INST.2 DIZOLELE | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Kongo Central | Moanda |
| INST.MANGA | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Nord-Kivu | Lubero |
| INST. LE PROGRES | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Kinshasa | Non renseigné |
| INST. KABUNDA | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Kasai Central | Dimbelenge |
| INST, NKONGO-MBENZA | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Kongo Central | Seke-Banza |
| INST DE KATWA | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Nord-Kivu | Non renseigné |
| INST. DES ANGES | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Kwilu | Idiofa |
| INST. KIBWIMI | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Kwilu | Bulungu |
| INST DIKWATELE | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Kwango | Kahemba |
| INST. KABAMBA | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Kwilu | Bulungu |
| INST. TECHN. SOCIAL KYONDO KYA MBIDI | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Haut-Lomami | Kabongo |
| INST MASIYA BOLINGO | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Equateur | Bikoro |
| INST. MUKOKO III | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Kwilu | Bulungu |
| INST. TECH. AGRICOLE MFUMU NDIMI | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Kwango | Kasongo-Lunda |
| INST. TUMAINI | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Sud-Kivu | Non renseigné |
| INST. KAZAMBA | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Kwilu | Masi-Manimba |
| INST. KILUMBE II | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Haut-Lomami | Bukama |
| INST. MIBALAYI | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Kasai | Ilebo |
| INST. KINTWALA | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Kwilu | Bulungu |
| INST. PEDAGOGIQUE ALFAJIRI | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Lualaba | Dilolo |
| INST. NTONDO | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Haut-Katanga | Pweto |
| INST. LUTAMBI | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Kasai Central | Dimbelenge |
| INST. MWANA MOKE | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Kwilu | Idiofa |
| INST,BUSHUJU | SCHOOL_INST | INST | École | 0.86 | Le nom contient l’indice lexical français explicite « INST », associé à la catégorie « École ». | Sud-Kivu | Uvira |
### 30 objets classés par COMPLEXE SCOLAIRE

| Nom source | Règle | Mot-clé | Catégorie proposée | Confiance | Justification | Province | Territoire |
|---|---|---|---|---:|---|---|---|
| COMPLEXE SCOLAIRE VILLAGE MERE AGNESSE MANZONI | SCHOOL_EXPLICIT | COMPLEXE SCOLAIRE | École | 0.99 | Le nom contient l’indice lexical français explicite « COMPLEXE SCOLAIRE », associé à la catégorie « École ». | Kinshasa | Non renseigné |
| COMPLEXE SCOLAIRE BISIMA | SCHOOL_EXPLICIT | COMPLEXE SCOLAIRE | École | 0.99 | Le nom contient l’indice lexical français explicite « COMPLEXE SCOLAIRE », associé à la catégorie « École ». | Kinshasa | Non renseigné |
| COMPLEXE SCOLAIRE ELAKA | SCHOOL_EXPLICIT | COMPLEXE SCOLAIRE | École | 0.99 | Le nom contient l’indice lexical français explicite « COMPLEXE SCOLAIRE », associé à la catégorie « École ». | Kinshasa | Non renseigné |
| COMPLEXE SCOLAIRE KIDIANGO | SCHOOL_EXPLICIT | COMPLEXE SCOLAIRE | École | 0.99 | Le nom contient l’indice lexical français explicite « COMPLEXE SCOLAIRE », associé à la catégorie « École ». | Kinshasa | Non renseigné |
| COMPLEXE SCOLAIRE SAINT MICHEL | SCHOOL_EXPLICIT | COMPLEXE SCOLAIRE | École | 0.99 | Le nom contient l’indice lexical français explicite « COMPLEXE SCOLAIRE », associé à la catégorie « École ». | Kinshasa | Non renseigné |
| COMPLEXE SCOLAIRE LA FLEURETTE | SCHOOL_EXPLICIT | COMPLEXE SCOLAIRE | École | 0.99 | Le nom contient l’indice lexical français explicite « COMPLEXE SCOLAIRE », associé à la catégorie « École ». | Kinshasa | Non renseigné |
| COMPLEXE SCOLAIRE FUNDA SCOOL | SCHOOL_EXPLICIT | COMPLEXE SCOLAIRE | École | 0.99 | Le nom contient l’indice lexical français explicite « COMPLEXE SCOLAIRE », associé à la catégorie « École ». | Haut-Lomami | Kamina |
| COMPLEXE SCOLAIRE BALIBANGA | SCHOOL_EXPLICIT | COMPLEXE SCOLAIRE | École | 0.99 | Le nom contient l’indice lexical français explicite « COMPLEXE SCOLAIRE », associé à la catégorie « École ». | Kinshasa | Non renseigné |
| COMPLEXE SCOLAIRE MASANDJOLI | SCHOOL_EXPLICIT | COMPLEXE SCOLAIRE | École | 0.99 | Le nom contient l’indice lexical français explicite « COMPLEXE SCOLAIRE », associé à la catégorie « École ». | Kinshasa | Non renseigné |
| COMPLEXE SCOLAIRE SAGESSE DIVINE | SCHOOL_EXPLICIT | COMPLEXE SCOLAIRE | École | 0.99 | Le nom contient l’indice lexical français explicite « COMPLEXE SCOLAIRE », associé à la catégorie « École ». | Kinshasa | Non renseigné |
| COMPLEXE SCOLAIRE DE NIOKI | SCHOOL_EXPLICIT | COMPLEXE SCOLAIRE | École | 0.99 | Le nom contient l’indice lexical français explicite « COMPLEXE SCOLAIRE », associé à la catégorie « École ». | Mai-ndombe | Non renseigné |
| COMPLEXE SCOLAIRE NOTRE DAME DES ANGES | SCHOOL_EXPLICIT | COMPLEXE SCOLAIRE | École | 0.99 | Le nom contient l’indice lexical français explicite « COMPLEXE SCOLAIRE », associé à la catégorie « École ». | Kinshasa | Non renseigné |
| COMPLEXE SCOLAIRE MAMAN DELE | SCHOOL_EXPLICIT | COMPLEXE SCOLAIRE | École | 0.99 | Le nom contient l’indice lexical français explicite « COMPLEXE SCOLAIRE », associé à la catégorie « École ». | Kinshasa | Non renseigné |
| COMPLEXE SCOLAIRE LA PAIX | SCHOOL_EXPLICIT | COMPLEXE SCOLAIRE | École | 0.99 | Le nom contient l’indice lexical français explicite « COMPLEXE SCOLAIRE », associé à la catégorie « École ». | Kasai | Ilebo |
| COMPLEXE SCOLAIRE LA TRIOMPHANTE SAVOIR FAIRE | SCHOOL_EXPLICIT | COMPLEXE SCOLAIRE | École | 0.99 | Le nom contient l’indice lexical français explicite « COMPLEXE SCOLAIRE », associé à la catégorie « École ». | Kasai | Non renseigné |
| COMPLEXE SCOLAIRE VILLAGE MERE AGNESSE MANZONI | SCHOOL_EXPLICIT | COMPLEXE SCOLAIRE | École | 0.99 | Le nom contient l’indice lexical français explicite « COMPLEXE SCOLAIRE », associé à la catégorie « École ». | Kinshasa | Non renseigné |
| COMPLEXE SCOLAIRE MAMAN BIKELA | SCHOOL_EXPLICIT | COMPLEXE SCOLAIRE | École | 0.99 | Le nom contient l’indice lexical français explicite « COMPLEXE SCOLAIRE », associé à la catégorie « École ». | Kinshasa | Non renseigné |
| COMPLEXE SCOLAIRE SAINT JOSEPH | SCHOOL_EXPLICIT | COMPLEXE SCOLAIRE | École | 0.99 | Le nom contient l’indice lexical français explicite « COMPLEXE SCOLAIRE », associé à la catégorie « École ». | Kinshasa | Non renseigné |
| COMPLEXE SCOLAIRE LES BAMBINS | SCHOOL_EXPLICIT | COMPLEXE SCOLAIRE | École | 0.99 | Le nom contient l’indice lexical français explicite « COMPLEXE SCOLAIRE », associé à la catégorie « École ». | Kinshasa | Non renseigné |
| COMPLEXE SCOLAIRE MARCELLO KADIEBUE | SCHOOL_EXPLICIT | COMPLEXE SCOLAIRE | École | 0.99 | Le nom contient l’indice lexical français explicite « COMPLEXE SCOLAIRE », associé à la catégorie « École ». | Kinshasa | Non renseigné |
| COMPLEXE SCOLAIRE .REV. KABULA 2 | SCHOOL_EXPLICIT | COMPLEXE SCOLAIRE | École | 0.99 | Le nom contient l’indice lexical français explicite « COMPLEXE SCOLAIRE », associé à la catégorie « École ». | Kinshasa | Non renseigné |
| COMPLEXE SCOLAIRE SAINT PAUL I | SCHOOL_EXPLICIT | COMPLEXE SCOLAIRE | École | 0.99 | Le nom contient l’indice lexical français explicite « COMPLEXE SCOLAIRE », associé à la catégorie « École ». | Kinshasa | Non renseigné |
| COMPLEXE SCOLAIRE VILLAGE MERE AGNESSE MANZONI | SCHOOL_EXPLICIT | COMPLEXE SCOLAIRE | École | 0.99 | Le nom contient l’indice lexical français explicite « COMPLEXE SCOLAIRE », associé à la catégorie « École ». | Kinshasa | Non renseigné |
| COMPLEXE SCOLAIRE LES ETOILES | SCHOOL_EXPLICIT | COMPLEXE SCOLAIRE | École | 0.99 | Le nom contient l’indice lexical français explicite « COMPLEXE SCOLAIRE », associé à la catégorie « École ». | Kinshasa | Non renseigné |
| COMPLEXE SCOLAIRE AMISH | SCHOOL_EXPLICIT | COMPLEXE SCOLAIRE | École | 0.99 | Le nom contient l’indice lexical français explicite « COMPLEXE SCOLAIRE », associé à la catégorie « École ». | Kasai | Kamonia |
| COMPLEXE SCOLAIRE ROVATU-ROVA | SCHOOL_EXPLICIT | COMPLEXE SCOLAIRE | École | 0.99 | Le nom contient l’indice lexical français explicite « COMPLEXE SCOLAIRE », associé à la catégorie « École ». | Kinshasa | Non renseigné |
| COMPLEXE SCOLAIRE MAISHA | SCHOOL_EXPLICIT | COMPLEXE SCOLAIRE | École | 0.99 | Le nom contient l’indice lexical français explicite « COMPLEXE SCOLAIRE », associé à la catégorie « École ». | Kinshasa | Non renseigné |
| COMPLEXE SCOLAIRE MONTALI | SCHOOL_EXPLICIT | COMPLEXE SCOLAIRE | École | 0.99 | Le nom contient l’indice lexical français explicite « COMPLEXE SCOLAIRE », associé à la catégorie « École ». | Kinshasa | Non renseigné |
| COMPLEXE SCOLAIRE SAGESSE DIVINE | SCHOOL_EXPLICIT | COMPLEXE SCOLAIRE | École | 0.99 | Le nom contient l’indice lexical français explicite « COMPLEXE SCOLAIRE », associé à la catégorie « École ». | Kinshasa | Non renseigné |
| COMPLEXE SCOLAIRE AKTO | SCHOOL_EXPLICIT | COMPLEXE SCOLAIRE | École | 0.99 | Le nom contient l’indice lexical français explicite « COMPLEXE SCOLAIRE », associé à la catégorie « École ». | Kinshasa | Non renseigné |
### 30 objets classés par COLLÈGE / LYCÉE

| Nom source | Règle | Mot-clé | Catégorie proposée | Confiance | Justification | Province | Territoire |
|---|---|---|---|---:|---|---|---|
| COLLEGE ALFAJIRI | SCHOOL_EXPLICIT | COLLEGE | École | 0.99 | Le nom contient l’indice lexical français explicite « COLLEGE », associé à la catégorie « École ». | Kinshasa | Non renseigné |
| COLLEGE PRINCE 1 | SCHOOL_EXPLICIT | COLLEGE | École | 0.99 | Le nom contient l’indice lexical français explicite « COLLEGE », associé à la catégorie « École ». | Kinshasa | Non renseigné |
| LYCEE MAMA LEONA | SCHOOL_EXPLICIT | LYCEE | École | 0.99 | Le nom contient l’indice lexical français explicite « LYCEE », associé à la catégorie « École ». | Nord-Ubangi | Yakoma |
| COLLEGE MONT DES OLIVIERS | SCHOOL_EXPLICIT | COLLEGE | École | 0.99 | Le nom contient l’indice lexical français explicite « COLLEGE », associé à la catégorie « École ». | Haut-Katanga | Non renseigné |
| LYCEE BAYA WAYA | SCHOOL_EXPLICIT | LYCEE | École | 0.99 | Le nom contient l’indice lexical français explicite « LYCEE », associé à la catégorie « École ». | Kasai Central | Dimbelenge |
| LYCEE MONANO | SCHOOL_EXPLICIT | LYCEE | École | 0.99 | Le nom contient l’indice lexical français explicite « LYCEE », associé à la catégorie « École ». | Mongala | Lisala |
| LYCEE LES ARCHANGES | SCHOOL_EXPLICIT | LYCEE | École | 0.99 | Le nom contient l’indice lexical français explicite « LYCEE », associé à la catégorie « École ». | Kinshasa | Non renseigné |
| LYCEE ANUARITE | SCHOOL_EXPLICIT | LYCEE | École | 0.99 | Le nom contient l’indice lexical français explicite « LYCEE », associé à la catégorie « École ». | Mongala | Lisala |
| COLLEGE ST BARTELEMY | SCHOOL_EXPLICIT | COLLEGE | École | 0.99 | Le nom contient l’indice lexical français explicite « COLLEGE », associé à la catégorie « École ». | Kinshasa | Non renseigné |
| COLLEGE MONT DES OLIVIERS | SCHOOL_EXPLICIT | COLLEGE | École | 0.99 | Le nom contient l’indice lexical français explicite « COLLEGE », associé à la catégorie « École ». | Haut-Katanga | Non renseigné |
| COLLEGE BONSOMI | SCHOOL_EXPLICIT | COLLEGE | École | 0.99 | Le nom contient l’indice lexical français explicite « COLLEGE », associé à la catégorie « École ». | Kinshasa | Non renseigné |
| COLLEGE ST PIE X | SCHOOL_EXPLICIT | COLLEGE | École | 0.99 | Le nom contient l’indice lexical français explicite « COLLEGE », associé à la catégorie « École ». | Kinshasa | Non renseigné |
| COLLEGE NOTRE DAME DE MBANZA-MBOMA | SCHOOL_EXPLICIT | COLLEGE | École | 0.99 | Le nom contient l’indice lexical français explicite « COLLEGE », associé à la catégorie « École ». | Kongo Central | Madimba |
| COLLEGE LA SAGESSE | SCHOOL_EXPLICIT | COLLEGE | École | 0.99 | Le nom contient l’indice lexical français explicite « COLLEGE », associé à la catégorie « École ». | Kinshasa | Non renseigné |
| LYCEE PERE RENE TIBAX | SCHOOL_EXPLICIT | LYCEE | École | 0.99 | Le nom contient l’indice lexical français explicite « LYCEE », associé à la catégorie « École ». | Kinshasa | Non renseigné |
| LYCEE BAHEKE | SCHOOL_EXPLICIT | LYCEE | École | 0.99 | Le nom contient l’indice lexical français explicite « LYCEE », associé à la catégorie « École ». | Kwilu | Idiofa |
| COLLEGE NZO KAYALA | SCHOOL_EXPLICIT | COLLEGE | École | 0.99 | Le nom contient l’indice lexical français explicite « COLLEGE », associé à la catégorie « École ». | Kinshasa | Non renseigné |
| COLLEGE MILLENAIRE | SCHOOL_EXPLICIT | COLLEGE | École | 0.99 | Le nom contient l’indice lexical français explicite « COLLEGE », associé à la catégorie « École ». | Kinshasa | Non renseigné |
| COLLEGE SAINT LEON | SCHOOL_EXPLICIT | COLLEGE | École | 0.99 | Le nom contient l’indice lexical français explicite « COLLEGE », associé à la catégorie « École ». | Kasai Oriental | Non renseigné |
| COLLEGE SAINT MARTIN | SCHOOL_EXPLICIT | COLLEGE | École | 0.99 | Le nom contient l’indice lexical français explicite « COLLEGE », associé à la catégorie « École ». | Kasai Central | Demba |
| LYCEE II ET III KASA-VUBU | SCHOOL_EXPLICIT | LYCEE | École | 0.99 | Le nom contient l’indice lexical français explicite « LYCEE », associé à la catégorie « École ». | Kinshasa | Non renseigné |
| COLLEGE SAINTE MARIE | SCHOOL_EXPLICIT | COLLEGE | École | 0.99 | Le nom contient l’indice lexical français explicite « COLLEGE », associé à la catégorie « École ». | Kinshasa | Non renseigné |
| LYCEE NOTRE DAME DE FATIMA | SCHOOL_EXPLICIT | LYCEE | École | 0.99 | Le nom contient l’indice lexical français explicite « LYCEE », associé à la catégorie « École ». | Lomami | Non renseigné |
| COLLEGE MONT DES OLIVIERS | SCHOOL_EXPLICIT | COLLEGE | École | 0.99 | Le nom contient l’indice lexical français explicite « COLLEGE », associé à la catégorie « École ». | Haut-Katanga | Non renseigné |
| COLLEGE JOHN-MONICA | SCHOOL_EXPLICIT | COLLEGE | École | 0.99 | Le nom contient l’indice lexical français explicite « COLLEGE », associé à la catégorie « École ». | Kinshasa | Non renseigné |
| COLLEGE SAINT AMAND | SCHOOL_EXPLICIT | COLLEGE | École | 0.99 | Le nom contient l’indice lexical français explicite « COLLEGE », associé à la catégorie « École ». | Kinshasa | Non renseigné |
| LYCEE STEIN | SCHOOL_EXPLICIT | LYCEE | École | 0.99 | Le nom contient l’indice lexical français explicite « LYCEE », associé à la catégorie « École ». | Kinshasa | Non renseigné |
| COLLEGE SAINTE TRINITE | SCHOOL_EXPLICIT | COLLEGE | École | 0.99 | Le nom contient l’indice lexical français explicite « COLLEGE », associé à la catégorie « École ». | Kinshasa | Non renseigné |
| COLLEGE ELISI | SCHOOL_EXPLICIT | COLLEGE | École | 0.99 | Le nom contient l’indice lexical français explicite « COLLEGE », associé à la catégorie « École ». | Equateur | Bomongo |
| COLLEGE SAINT ETIENNE | SCHOOL_EXPLICIT | COLLEGE | École | 0.99 | Le nom contient l’indice lexical français explicite « COLLEGE », associé à la catégorie « École ». | Kinshasa | Non renseigné |
### Tous les cas de confiance inférieure à 0,85

| Nom source | Règle | Mot-clé | Catégorie proposée | Confiance | Justification | Province | Territoire |
|---|---|---|---|---:|---|---|---|
| C.S. LUMBA (INSTITUT) | CS_CONTEXT_SCOLAIRE | CS | École | 0.76 | L’abréviation « CS » est désambiguïsée par un indice explicite de contexte scolaire. | Kasai Oriental | Non renseigné |
| C.S. LUMBA (INSTITUT) | CS_CONTEXT_SCOLAIRE | CS | École | 0.76 | L’abréviation « CS » est désambiguïsée par un indice explicite de contexte scolaire. | Kasai Oriental | Non renseigné |
| C.S. LUMBA (INSTITUT) | CS_CONTEXT_SCOLAIRE | CS | École | 0.76 | L’abréviation « CS » est désambiguïsée par un indice explicite de contexte scolaire. | Kasai Oriental | Non renseigné |
| C.S. LUMBA (INSTITUT) | CS_CONTEXT_SCOLAIRE | CS | École | 0.76 | L’abréviation « CS » est désambiguïsée par un indice explicite de contexte scolaire. | Kasai Oriental | Non renseigné |
| C.S.LYCEE MUA BANA | CS_CONTEXT_SCOLAIRE | CS | École | 0.76 | L’abréviation « CS » est désambiguïsée par un indice explicite de contexte scolaire. | Kasai Oriental | Non renseigné |
| C.S.LYCEE MUA BANA | CS_CONTEXT_SCOLAIRE | CS | École | 0.76 | L’abréviation « CS » est désambiguïsée par un indice explicite de contexte scolaire. | Kasai Oriental | Non renseigné |
| C.S.LYCEE MUA BANA | CS_CONTEXT_SCOLAIRE | CS | École | 0.76 | L’abréviation « CS » est désambiguïsée par un indice explicite de contexte scolaire. | Kasai Oriental | Non renseigné |
| C.S.LYCEE MUA BANA | CS_CONTEXT_SCOLAIRE | CS | École | 0.76 | L’abréviation « CS » est désambiguïsée par un indice explicite de contexte scolaire. | Kasai Oriental | Non renseigné |
| CS EP WATA ET INSTITUT REVEREND MWANZA | CS_CONTEXT_SCOLAIRE | CS | École | 0.76 | L’abréviation « CS » est désambiguïsée par un indice explicite de contexte scolaire. | Kinshasa | Non renseigné |
| CS EP WATA ET INSTITUT REVEREND MWANZA | CS_CONTEXT_SCOLAIRE | CS | École | 0.76 | L’abréviation « CS » est désambiguïsée par un indice explicite de contexte scolaire. | Kinshasa | Non renseigné |
| CS EP WATA ET INSTITUT REVEREND MWANZA | CS_CONTEXT_SCOLAIRE | CS | École | 0.76 | L’abréviation « CS » est désambiguïsée par un indice explicite de contexte scolaire. | Kinshasa | Non renseigné |
| CS EP WATA ET INSTITUT REVEREND MWANZA | CS_CONTEXT_SCOLAIRE | CS | École | 0.76 | L’abréviation « CS » est désambiguïsée par un indice explicite de contexte scolaire. | Kinshasa | Non renseigné |
| CS LYCEE MERE FRANCISCA | CS_CONTEXT_SCOLAIRE | CS | École | 0.76 | L’abréviation « CS » est désambiguïsée par un indice explicite de contexte scolaire. | Haut-Katanga | Sakania |
| CS LYCEE MERE FRANCISCA | CS_CONTEXT_SCOLAIRE | CS | École | 0.76 | L’abréviation « CS » est désambiguïsée par un indice explicite de contexte scolaire. | Haut-Katanga | Sakania |
| CS LYCEE MERE FRANCISCA | CS_CONTEXT_SCOLAIRE | CS | École | 0.76 | L’abréviation « CS » est désambiguïsée par un indice explicite de contexte scolaire. | Haut-Katanga | Sakania |
| CS LYCEE MERE FRANCISCA | CS_CONTEXT_SCOLAIRE | CS | École | 0.76 | L’abréviation « CS » est désambiguïsée par un indice explicite de contexte scolaire. | Haut-Katanga | Sakania |
| INSTITUT KASINDI/CS KANGAUKA | CS_CONTEXT_SCOLAIRE | CS | École | 0.76 | L’abréviation « CS » est désambiguïsée par un indice explicite de contexte scolaire. | Nord-Kivu | Oicha |
| INSTITUT KASINDI/CS KANGAUKA | CS_CONTEXT_SCOLAIRE | CS | École | 0.76 | L’abréviation « CS » est désambiguïsée par un indice explicite de contexte scolaire. | Nord-Kivu | Oicha |
| INSTITUT KASINDI/CS KANGAUKA | CS_CONTEXT_SCOLAIRE | CS | École | 0.76 | L’abréviation « CS » est désambiguïsée par un indice explicite de contexte scolaire. | Nord-Kivu | Oicha |

## Intégrité et recommandations

- KMZ officiel : `C3762911DF483D0B291145AF31CF612A30332039BB3D7BFD86FA894C650ABE9D`.
- `case_history.json` : `B4BBE00BA55E4735D6E474DDE2654317A868338A0DD54E43095AA0E43EF64BB1`.
- La source brute n’est ni réécrite ni corrigée.
- Faire valider séparément les lots EP et INST par province, avec suréchantillonnage des noms courts.
- Traiter individuellement les 19 cas CS.
- Conserver les codes internes uniquement dans les contrats techniques et les libellés français dans l’interface.
- Versionner toute future modification de règle et comparer systématiquement les populations avant/après.
