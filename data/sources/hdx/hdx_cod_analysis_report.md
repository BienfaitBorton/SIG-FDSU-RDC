# HDX COD Administrative Boundaries Analysis

## Coverage
- GeoJSON layers: 11
- Shapefile members: 55
- XLSX sheets: 11

## Levels
- cod_admincapitals: 42 entités, géométries={'Point': 42}, Pcodes=adm0_pcode, adm1_pcode, adm2_pcode, adm3_pcode, loc_pcode
- cod_adminlines: 515 entités, géométries={'LineString': 515}, Pcodes=
- cod_adminpoints: 735 entités, géométries={'Point': 735}, Pcodes=adm0_pcode, adm1_pcode, adm2_pcode, adm3_pcode, adm4_pcode
- cod_admin1_em: 26 entités, géométries={'Polygon': 18, 'MultiPolygon': 8}, Pcodes=adm0_pcode, adm1_pcode
- cod_admin3_em: 519 entités, géométries={'Polygon': 491, 'MultiPolygon': 28}, Pcodes=adm0_pcode, adm1_pcode, adm2_pcode, adm3_pcode
- cod_admin1: 26 entités, géométries={'Polygon': 19, 'MultiPolygon': 7}, Pcodes=adm0_pcode, adm1_pcode
- cod_admin0_em: 1 entités, géométries={'MultiPolygon': 1}, Pcodes=adm0_pcode
- cod_admin0: 1 entités, géométries={'Polygon': 1}, Pcodes=adm0_pcode
- cod_admin2_em: 164 entités, géométries={'Polygon': 150, 'MultiPolygon': 14}, Pcodes=adm0_pcode, adm1_pcode, adm2_pcode
- cod_admin2: 164 entités, géométries={'Polygon': 152, 'MultiPolygon': 12}, Pcodes=adm0_pcode, adm1_pcode, adm2_pcode
- cod_admin3: 519 entités, géométries={'Polygon': 496, 'MultiPolygon': 23}, Pcodes=adm0_pcode, adm1_pcode, adm2_pcode, adm3_pcode

## Comparison
- FDSU province matches: 26
- FDSU local matches against admin2/admin3: 175
- KMZ Zones name matches: 196
- KMZ Collectivités name matches: 87

## Compatibility
- HDX COD fournit des Pcodes, des géométries et une hiérarchie tabulaire exploitable pour un staging national.
- Le mapping devra rester prudent car les niveaux HDX s'arrêtent ici à admin3 dans les couches surfaciques observées.