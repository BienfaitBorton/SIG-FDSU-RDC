# Audit de classification des entités extraites depuis zones_fdsu.kmz

- Nombre total analysé: 156
- Nombre de territoires: 145
- Nombre de villes: 0
- Nombre de communes: 11
- Nombre d'autres objets: 0

## Explication de l'écart 156 vs 145

- Attendu officiel: 145
- Extrait: 156
- Différence: 11
- Cause principale: 11 objets de type attributaire 'Communes' sont physiquement rangés dans des dossiers 'Territoires' du KMZ, donc ils ont été captés par une lecture purement hiérarchique.

## Liste des 11 objets supplémentaires

| Nom | Type détecté | Province | Zone | Dossier parent | Hypothèse | Pourquoi capté |
|---|---|---|---|---|---|---|
| Kananga | Commune | Kasai Central | CE | Territoires | Ville | Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Communes'. Type détecté pour audit = 'Commune'. |
| Mbuji-Mayi | Commune | Kasai Oriental | CE | Territoires | Ville | Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Communes'. Type détecté pour audit = 'Commune'. |
| Mwene Ditu | Commune | Lomami | CE | Territoires | Ville | Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Communes'. Type détecté pour audit = 'Commune'. |
| Likasi | Commune | Haut-Katanga | SD | Territoires | Ville | Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Communes'. Type détecté pour audit = 'Commune'. |
| Lubumbashi | Commune | Haut-Katanga | SD | Territoires | Ville | Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Communes'. Type détecté pour audit = 'Commune'. |
| Kolwezi | Commune | Lualaba | SD | Territoires | Ville | Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Communes'. Type détecté pour audit = 'Commune'. |
| Butembo | Commune | Nord-Kivu | ET | Territoires | Ville | Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Communes'. Type détecté pour audit = 'Commune'. |
| Beni | Commune | Nord-Kivu | ET | Territoires | Ville | Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Communes'. Type détecté pour audit = 'Commune'. |
| Goma | Commune | Nord-Kivu | ET | Territoires | Ville | Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Communes'. Type détecté pour audit = 'Commune'. |
| Bukavu | Commune | Sud-Kivu | ET | Territoires | Ville | Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Communes'. Type détecté pour audit = 'Commune'. |
| Kindu | Commune | Maniema | ET | Territoires | Ville | Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Communes'. Type détecté pour audit = 'Commune'. |

## Territoires officiellement reconnus

- Rungu | Haut-Uele | ND | ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Haut-Uele -> Territoire -> Rungu
- Niangara | Haut-Uele | ND | ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Haut-Uele -> Territoire -> Niangara
- Dungu | Haut-Uele | ND | ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Haut-Uele -> Territoire -> Dungu
- Faradje | Haut-Uele | ND | ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Haut-Uele -> Territoire -> Faradje
- Watsa | Haut-Uele | ND | ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Haut-Uele -> Territoire -> Watsa
- Wamba | Haut-Uele | ND | ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Haut-Uele -> Territoire -> Wamba
- Buta | Bas-Uele | ND | ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Bas-Uele -> Territoires -> Buta
- Aketi | Bas-Uele | ND | ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Bas-Uele -> Territoires -> Aketi
- Bondo | Bas-Uele | ND | ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Bas-Uele -> Territoires -> Bondo
- Ango | Bas-Uele | ND | ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Bas-Uele -> Territoires -> Ango
- Bambesa | Bas-Uele | ND | ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Bas-Uele -> Territoires -> Bambesa
- Poko | Bas-Uele | ND | ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Bas-Uele -> Territoires -> Poko
- Banalia | Tshopo | ND | ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Tshopo -> Territoire -> Banalia
- Bafwasende | Tshopo | ND | ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Tshopo -> Territoire -> Bafwasende
- Ubundu | Tshopo | ND | ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Tshopo -> Territoire -> Ubundu
- Opala | Tshopo | ND | ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Tshopo -> Territoire -> Opala
- Isangi | Tshopo | ND | ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Tshopo -> Territoire -> Isangi
- Yahuma | Tshopo | ND | ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Tshopo -> Territoire -> Yahuma
- Basoko | Tshopo | ND | ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Tshopo -> Territoire -> Basoko
- Bokungu | Tshuapa | ND | ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Tshuapa -> Territoire -> Bokungu
- Boende | Tshuapa | ND | ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Tshuapa -> Territoire -> Boende
- Befale | Tshuapa | ND | ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Tshuapa -> Territoire -> Befale
- Djolu | Tshuapa | ND | ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Tshuapa -> Territoire -> Djolu
- Ikela | Tshuapa | ND | ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Tshuapa -> Territoire -> Ikela
- Monkoto | Tshuapa | ND | ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Tshuapa -> Territoire -> Monkoto
- Lisala | Mongala | ND | ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Mongala -> Territoires -> Lisala
- Bumba | Mongala | ND | ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Mongala -> Territoires -> Bumba
- Bondanganga | Mongala | ND | ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Mongala -> Territoires -> Bondanganga
- Mobayi-Mbongo | Nord-Ubangi | ND | ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Nord-Ubangi -> Territoires -> Mobayi-Mbongo
- Yakoma | Nord-Ubangi | ND | ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Nord-Ubangi -> Territoires -> Yakoma
- Businga | Nord-Ubangi | ND | ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Nord-Ubangi -> Territoires -> Businga
- Basobolo | Nord-Ubangi | ND | ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Nord-Ubangi -> Territoires -> Basobolo
- Gemena | Sud-Ubangi | ND | ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Sud-Ubangi -> Territoires -> Gemena
- Budjala | Sud-Ubangi | ND | ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Sud-Ubangi -> Territoires -> Budjala
- Kungu | Sud-Ubangi | ND | ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Sud-Ubangi -> Territoires -> Kungu
- Libenge | Sud-Ubangi | ND | ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Sud-Ubangi -> Territoires -> Libenge
- Basankusu | Equateur | ND | ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Equateur -> Territoire -> Basankusu
- Bolomba | Equateur | ND | ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Equateur -> Territoire -> Bolomba
- Ingende | Equateur | ND | ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Equateur -> Territoire -> Ingende
- Bikoro | Equateur | ND | ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Equateur -> Territoire -> Bikoro
- Lukolela | Equateur | ND | ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Equateur -> Territoire -> Lukolela
- Mankanza | Equateur | ND | ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Equateur -> Territoire -> Mankanza
- Bomongo | Equateur | ND | ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Equateur -> Territoire -> Bomongo
- Kenge | Kwango | OT | ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Kwango -> Territoires -> Kenge
- Feshi | Kwango | OT | ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Kwango -> Territoires -> Feshi
- Kahemba | Kwango | OT | ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Kwango -> Territoires -> Kahemba
- Kasongo-Lunda | Kwango | OT | ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Kwango -> Territoires -> Kasongo-Lunda
- Popokabaka | Kwango | OT | ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Kwango -> Territoires -> Popokabaka
- Bulungu | Kwilu | OT | ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Kwilu -> Territoires -> Bulungu
- Masi-Manimba | Kwilu | OT | ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Kwilu -> Territoires -> Masi-Manimba
- Bagata | Kwilu | OT | ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Kwilu -> Territoires -> Bagata
- Idiofa | Kwilu | OT | ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Kwilu -> Territoires -> Idiofa
- Gungu | Kwilu | OT | ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Kwilu -> Territoires -> Gungu
- Moanda | Kongo Central | OT | ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Kongo Central -> Territoires -> Moanda
- Tshela | Kongo Central | OT | ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Kongo Central -> Territoires -> Tshela
- Seke-Banza | Kongo Central | OT | ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Kongo Central -> Territoires -> Seke-Banza
- Lukula | Kongo Central | OT | ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Kongo Central -> Territoires -> Lukula
- Mbanza-Ngungu | Kongo Central | OT | ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Kongo Central -> Territoires -> Mbanza-Ngungu
- Songololo | Kongo Central | OT | ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Kongo Central -> Territoires -> Songololo
- Luozi | Kongo Central | OT | ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Kongo Central -> Territoires -> Luozi
- Madimba | Kongo Central | OT | ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Kongo Central -> Territoires -> Madimba
- Kasangulu | Kongo Central | OT | ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Kongo Central -> Territoires -> Kasangulu
- Kimvula | Kongo Central | OT | ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Kongo Central -> Territoires -> Kimvula
- Bolobo | Maindombe | OT | ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Maindombe -> Territoire -> Bolobo
- Kwamouth | Maindombe | OT | ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Maindombe -> Territoire -> Kwamouth
- Mushie | Maindombe | OT | ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Maindombe -> Territoire -> Mushie
- Yumbi | Maindombe | OT | ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Maindombe -> Territoire -> Yumbi
- Inongo | Maindombe | OT | ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Maindombe -> Territoire -> Inongo
- Kiri | Maindombe | OT | ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Maindombe -> Territoire -> Kiri
- Oshwe | Maindombe | OT | ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Maindombe -> Territoire -> Oshwe
- Kutu | Maindombe | OT | ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Maindombe -> Territoire -> Kutu
- Luebo | Kasai | CE | ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Kasai -> Territoires -> Luebo
- Kamonia | Kasai | CE | ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Kasai -> Territoires -> Kamonia
- Ilebo | Kasai | CE | ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Kasai -> Territoires -> Ilebo
- Mweka | Kasai | CE | ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Kasai -> Territoires -> Mweka
- Dekese | Kasai | CE | ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Kasai -> Territoires -> Dekese
- Dibaya | Kasai Central | CE | ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Kasai Central -> Territoires -> Dibaya
- Luiza | Kasai Central | CE | ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Kasai Central -> Territoires -> Luiza
- Kazumba | Kasai Central | CE | ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Kasai Central -> Territoires -> Kazumba
- Demba | Kasai Central | CE | ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Kasai Central -> Territoires -> Demba
- Dimbelenge | Kasai Central | CE | ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Kasai Central -> Territoires -> Dimbelenge
- Miabi | Kasai Oriental | CE | ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Kasai Oriental -> Territoires -> Miabi
- Kabeya-Kamwanga | Kasai Oriental | CE | ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Kasai Oriental -> Territoires -> Kabeya-Kamwanga
- Lupatapata | Kasai Oriental | CE | ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Kasai Oriental -> Territoires -> Lupatapata
- Katanda | Kasai Oriental | CE | ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Kasai Oriental -> Territoires -> Katanda
- Tshilenge | Kasai Oriental | CE | ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Kasai Oriental -> Territoires -> Tshilenge
- Luilu | Lomami | CE | ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Lomami -> Territoires -> Luilu
- Kamiji | Lomami | CE | ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Lomami -> Territoires -> Kamiji
- Ngandajika | Lomami | CE | ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Lomami -> Territoires -> Ngandajika
- Kabinda | Lomami | CE | ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Lomami -> Territoires -> Kabinda
- Lubao | Lomami | CE | ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Lomami -> Territoires -> Lubao
- Lusambo | Sankuru | CE | ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Sankuru -> Territoires -> Lusambo
- Kole | Sankuru | CE | ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Sankuru -> Territoires -> Kole
- Lomela | Sankuru | CE | ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Sankuru -> Territoires -> Lomela
- Katako-Kombe | Sankuru | CE | ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Sankuru -> Territoires -> Katako-Kombe
- Lubefu | Sankuru | CE | ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Sankuru -> Territoires -> Lubefu
- Lodja | Sankuru | CE | ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Sankuru -> Territoires -> Lodja
- Kipushi | Haut-Katanga | SD | ZONES.kmz -> ZONES -> ZONE SUD -> Provinces -> Haut-Katanga -> Territoires -> Kipushi
- Sakania | Haut-Katanga | SD | ZONES.kmz -> ZONES -> ZONE SUD -> Provinces -> Haut-Katanga -> Territoires -> Sakania
- Kasenga | Haut-Katanga | SD | ZONES.kmz -> ZONES -> ZONE SUD -> Provinces -> Haut-Katanga -> Territoires -> Kasenga
- Pweto | Haut-Katanga | SD | ZONES.kmz -> ZONES -> ZONE SUD -> Provinces -> Haut-Katanga -> Territoires -> Pweto
- Kambove | Haut-Katanga | SD | ZONES.kmz -> ZONES -> ZONE SUD -> Provinces -> Haut-Katanga -> Territoires -> Kambove
- Mitwaba | Haut-Katanga | SD | ZONES.kmz -> ZONES -> ZONE SUD -> Provinces -> Haut-Katanga -> Territoires -> Mitwaba
- Kalemie | Tanganyika | SD | ZONES.kmz -> ZONES -> ZONE SUD -> Provinces -> Tanganyika -> Territoires -> Kalemie
- Moba | Tanganyika | SD | ZONES.kmz -> ZONES -> ZONE SUD -> Provinces -> Tanganyika -> Territoires -> Moba
- Manono | Tanganyika | SD | ZONES.kmz -> ZONES -> ZONE SUD -> Provinces -> Tanganyika -> Territoires -> Manono
- Kabalo | Tanganyika | SD | ZONES.kmz -> ZONES -> ZONE SUD -> Provinces -> Tanganyika -> Territoires -> Kabalo
- Kongolo | Tanganyika | SD | ZONES.kmz -> ZONES -> ZONE SUD -> Provinces -> Tanganyika -> Territoires -> Kongolo
- Nyunzu | Tanganyika | SD | ZONES.kmz -> ZONES -> ZONE SUD -> Provinces -> Tanganyika -> Territoires -> Nyunzu
- Kamina | Haut-Lomami | SD | ZONES.kmz -> ZONES -> ZONE SUD -> Provinces -> Haut-Lomami -> Territoires -> Kamina
- Kaniama | Haut-Lomami | SD | ZONES.kmz -> ZONES -> ZONE SUD -> Provinces -> Haut-Lomami -> Territoires -> Kaniama
- Kabongo | Haut-Lomami | SD | ZONES.kmz -> ZONES -> ZONE SUD -> Provinces -> Haut-Lomami -> Territoires -> Kabongo
- Malemba-Nkulu | Haut-Lomami | SD | ZONES.kmz -> ZONES -> ZONE SUD -> Provinces -> Haut-Lomami -> Territoires -> Malemba-Nkulu
- Bukama | Haut-Lomami | SD | ZONES.kmz -> ZONES -> ZONE SUD -> Provinces -> Haut-Lomami -> Territoires -> Bukama
- Mutshatsha | Lualaba | SD | ZONES.kmz -> ZONES -> ZONE SUD -> Provinces -> Lualaba -> Territoires -> Mutshatsha
- Lubudi | Lualaba | SD | ZONES.kmz -> ZONES -> ZONE SUD -> Provinces -> Lualaba -> Territoires -> Lubudi
- Dilolo | Lualaba | SD | ZONES.kmz -> ZONES -> ZONE SUD -> Provinces -> Lualaba -> Territoires -> Dilolo
- Sandoa | Lualaba | SD | ZONES.kmz -> ZONES -> ZONE SUD -> Provinces -> Lualaba -> Territoires -> Sandoa
- Kapanga | Lualaba | SD | ZONES.kmz -> ZONES -> ZONE SUD -> Provinces -> Lualaba -> Territoires -> Kapanga
- Irumu | Ituri | ET | ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Ituri -> Territoires -> Irumu
- Mambasa | Ituri | ET | ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Ituri -> Territoires -> Mambasa
- Djugu | Ituri | ET | ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Ituri -> Territoires -> Djugu
- Mahagi | Ituri | ET | ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Ituri -> Territoires -> Mahagi
- Aru | Ituri | ET | ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Ituri -> Territoires -> Aru
- Nyiragongo | Nord-Kivu | ET | ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Nord-Kivu -> Territoires -> Nyiragongo
- Walikale | Nord-Kivu | ET | ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Nord-Kivu -> Territoires -> Walikale
- Lubero | Nord-Kivu | ET | ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Nord-Kivu -> Territoires -> Lubero
- Oicha | Nord-Kivu | ET | ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Nord-Kivu -> Territoires -> Oicha
- Rutshuru | Nord-Kivu | ET | ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Nord-Kivu -> Territoires -> Rutshuru
- Masisi | Nord-Kivu | ET | ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Nord-Kivu -> Territoires -> Masisi
- Walungu | Sud-Kivu | ET | ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Sud-Kivu -> Territoires -> Walungu
- Uvira | Sud-Kivu | ET | ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Sud-Kivu -> Territoires -> Uvira
- Fizi | Sud-Kivu | ET | ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Sud-Kivu -> Territoires -> Fizi
- Mwenga | Sud-Kivu | ET | ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Sud-Kivu -> Territoires -> Mwenga
- Shabunda | Sud-Kivu | ET | ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Sud-Kivu -> Territoires -> Shabunda
- Kalehe | Sud-Kivu | ET | ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Sud-Kivu -> Territoires -> Kalehe
- Idjwi | Sud-Kivu | ET | ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Sud-Kivu -> Territoires -> Idjwi
- Kabare | Sud-Kivu | ET | ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Sud-Kivu -> Territoires -> Kabare
- Kabambare | Maniema | ET | ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Maniema -> Territoires -> Kabambare
- Kibombo | Maniema | ET | ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Maniema -> Territoires -> Kibombo
- Lubutu | Maniema | ET | ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Maniema -> Territoires -> Lubutu
- Pangi | Maniema | ET | ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Maniema -> Territoires -> Pangi
- Kasongo | Maniema | ET | ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Maniema -> Territoires -> Kasongo
- Kailo | Maniema | ET | ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Maniema -> Territoires -> Kailo
- Punia | Maniema | ET | ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Maniema -> Territoires -> Punia

## Territoires officiels absents

- Aucun territoire officiel absent dans l'ensemble de 145 territoires.

## Détail complet des 156 entités analysées

### Rungu

- Type détecté: Territoire
- Province: Haut-Uele
- Zone FDSU: ND
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Haut-Uele -> Territoire -> Rungu
- Dossier parent: Territoire
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoire' dans la branche Zone -> Province -> Territoire. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Rungu", "TYPE": "Territoire", "CODE_INS": "5041", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "9405.604934", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone ND\nProvince 05\nTerritoire 005"}
- Hypothèse supplémentaire: Non applicable

### Niangara

- Type détecté: Territoire
- Province: Haut-Uele
- Zone FDSU: ND
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Haut-Uele -> Territoire -> Niangara
- Dossier parent: Territoire
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoire' dans la branche Zone -> Province -> Territoire. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Niangara", "TYPE": "Territoire", "CODE_INS": "5042", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "9368.649491", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone ND\nProvince 05\nTerritoire 004"}
- Hypothèse supplémentaire: Non applicable

### Dungu

- Type détecté: Territoire
- Province: Haut-Uele
- Zone FDSU: ND
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Haut-Uele -> Territoire -> Dungu
- Dossier parent: Territoire
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoire' dans la branche Zone -> Province -> Territoire. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Dungu", "TYPE": "Territoire", "CODE_INS": "5043", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "33887.344287", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone ND\nProvince 05\nTerritoire 002"}
- Hypothèse supplémentaire: Non applicable

### Faradje

- Type détecté: Territoire
- Province: Haut-Uele
- Zone FDSU: ND
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Haut-Uele -> Territoire -> Faradje
- Dossier parent: Territoire
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoire' dans la branche Zone -> Province -> Territoire. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Faradje", "TYPE": "Territoire", "CODE_INS": "5044", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "12702.318809", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone ND\nProvince 05\nTerritoire 003"}
- Hypothèse supplémentaire: Non applicable

### Watsa

- Type détecté: Territoire
- Province: Haut-Uele
- Zone FDSU: ND
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Haut-Uele -> Territoire -> Watsa
- Dossier parent: Territoire
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoire' dans la branche Zone -> Province -> Territoire. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Watsa", "TYPE": "Territoire", "CODE_INS": "5045", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "16462.535308", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone ND\nProvince 05\nTerritoire 007"}
- Hypothèse supplémentaire: Non applicable

### Wamba

- Type détecté: Territoire
- Province: Haut-Uele
- Zone FDSU: ND
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Haut-Uele -> Territoire -> Wamba
- Dossier parent: Territoire
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoire' dans la branche Zone -> Province -> Territoire. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Wamba", "TYPE": "Territoire", "CODE_INS": "5046", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "9838.442281", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone ND\nProvince 05\nTerritoire 006"}
- Hypothèse supplémentaire: Non applicable

### Buta

- Type détecté: Territoire
- Province: Bas-Uele
- Zone FDSU: ND
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Bas-Uele -> Territoires -> Buta
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Buta", "TYPE": "Territoire", "CODE_INS": "5031", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "17584.276483", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone ND\nProvince 01\nTerritoire 006"}
- Hypothèse supplémentaire: Non applicable

### Aketi

- Type détecté: Territoire
- Province: Bas-Uele
- Zone FDSU: ND
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Bas-Uele -> Territoires -> Aketi
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Aketi", "TYPE": "Territoire", "CODE_INS": "5032", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "27380.474116", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone ND\nProvince 01\nTerritoire 002"}
- Hypothèse supplémentaire: Non applicable

### Bondo

- Type détecté: Territoire
- Province: Bas-Uele
- Zone FDSU: ND
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Bas-Uele -> Territoires -> Bondo
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Bondo", "TYPE": "Territoire", "CODE_INS": "5033", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "37844.357209", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone ND\nProvince 01\nTerritoire 005"}
- Hypothèse supplémentaire: Non applicable

### Ango

- Type détecté: Territoire
- Province: Bas-Uele
- Zone FDSU: ND
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Bas-Uele -> Territoires -> Ango
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Ango", "TYPE": "Territoire", "CODE_INS": "5034", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "34522.976662", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone ND\nProvince 01\nTerritoire 003"}
- Hypothèse supplémentaire: Non applicable

### Bambesa

- Type détecté: Territoire
- Province: Bas-Uele
- Zone FDSU: ND
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Bas-Uele -> Territoires -> Bambesa
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Bambesa", "TYPE": "Territoire", "CODE_INS": "5035", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "9915.850629", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone ND\nProvince 01\nTerritoire 004"}
- Hypothèse supplémentaire: Non applicable

### Poko

- Type détecté: Territoire
- Province: Bas-Uele
- Zone FDSU: ND
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Bas-Uele -> Territoires -> Poko
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Poko", "TYPE": "Territoire", "CODE_INS": "5036", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "21984.017936", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone ND\nProvince 01\nTerritoire 007"}
- Hypothèse supplémentaire: Non applicable

### Banalia

- Type détecté: Territoire
- Province: Tshopo
- Zone FDSU: ND
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Tshopo -> Territoire -> Banalia
- Dossier parent: Territoire
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoire' dans la branche Zone -> Province -> Territoire. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Banalia", "TYPE": "Territoire", "CODE_INS": "5021", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "23630.594179", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone ND\nProvince 25\nTerritoire 009"}
- Hypothèse supplémentaire: Non applicable

### Bafwasende

- Type détecté: Territoire
- Province: Tshopo
- Zone FDSU: ND
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Tshopo -> Territoire -> Bafwasende
- Dossier parent: Territoire
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoire' dans la branche Zone -> Province -> Territoire. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Bafwasende", "TYPE": "Territoire", "CODE_INS": "5022", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "48817.557352", "ORIGINE": "Numerisation Saint Moulin / Image satellite"}, "description_values": {}, "description_html": "Zone ND\nProvince 25\nTerritoire 008"}
- Hypothèse supplémentaire: Non applicable

### Ubundu

- Type détecté: Territoire
- Province: Tshopo
- Zone FDSU: ND
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Tshopo -> Territoire -> Ubundu
- Dossier parent: Territoire
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoire' dans la branche Zone -> Province -> Territoire. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Ubundu", "TYPE": "Territoire", "CODE_INS": "5023", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "41536.669057", "ORIGINE": "Numerisation Saint Moulin / Image satellite"}, "description_values": {}, "description_html": "Zone ND\nProvince 25\nTerritoire 013"}
- Hypothèse supplémentaire: Non applicable

### Opala

- Type détecté: Territoire
- Province: Tshopo
- Zone FDSU: ND
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Tshopo -> Territoire -> Opala
- Dossier parent: Territoire
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoire' dans la branche Zone -> Province -> Territoire. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Opala", "TYPE": "Territoire", "CODE_INS": "5024", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "26453.14379", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone ND\nProvince 25\nTerritoire 012"}
- Hypothèse supplémentaire: Non applicable

### Isangi

- Type détecté: Territoire
- Province: Tshopo
- Zone FDSU: ND
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Tshopo -> Territoire -> Isangi
- Dossier parent: Territoire
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoire' dans la branche Zone -> Province -> Territoire. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Isangi", "TYPE": "Territoire", "CODE_INS": "5025", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "13768.869529", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone ND\n\nProvince 25\nTerritoire 011"}
- Hypothèse supplémentaire: Non applicable

### Yahuma

- Type détecté: Territoire
- Province: Tshopo
- Zone FDSU: ND
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Tshopo -> Territoire -> Yahuma
- Dossier parent: Territoire
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoire' dans la branche Zone -> Province -> Territoire. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Yahuma", "TYPE": "Territoire", "CODE_INS": "5026", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "21482.006585", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone ND\nProvince 25\nTerritoire 014"}
- Hypothèse supplémentaire: Non applicable

### Basoko

- Type détecté: Territoire
- Province: Tshopo
- Zone FDSU: ND
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Tshopo -> Territoire -> Basoko
- Dossier parent: Territoire
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoire' dans la branche Zone -> Province -> Territoire. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Basoko", "TYPE": "Territoire", "CODE_INS": "5027", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "22677.242672", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone ND\nProvince 25\nTerritoire 010"}
- Hypothèse supplémentaire: Non applicable

### Bokungu

- Type détecté: Territoire
- Province: Tshuapa
- Zone FDSU: ND
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Tshuapa -> Territoire -> Bokungu
- Dossier parent: Territoire
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoire' dans la branche Zone -> Province -> Territoire. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Bokungu", "TYPE": "Territoire", "CODE_INS": "4075", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "20310.031691", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone ND\nProvince 26\nTerritoire 004"}
- Hypothèse supplémentaire: Non applicable

### Boende

- Type détecté: Territoire
- Province: Tshuapa
- Zone FDSU: ND
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Tshuapa -> Territoire -> Boende
- Dossier parent: Territoire
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoire' dans la branche Zone -> Province -> Territoire. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Boende", "TYPE": "Territoire", "CODE_INS": "4071", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "18608.838775", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone ND\nProvince 26\nTerritoire 002"}
- Hypothèse supplémentaire: Non applicable

### Befale

- Type détecté: Territoire
- Province: Tshuapa
- Zone FDSU: ND
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Tshuapa -> Territoire -> Befale
- Dossier parent: Territoire
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoire' dans la branche Zone -> Province -> Territoire. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Befale", "TYPE": "Territoire", "CODE_INS": "4072", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "17820.629743", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone ND\nProvince 26\nTerritoire 001"}
- Hypothèse supplémentaire: Non applicable

### Djolu

- Type détecté: Territoire
- Province: Tshuapa
- Zone FDSU: ND
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Tshuapa -> Territoire -> Djolu
- Dossier parent: Territoire
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoire' dans la branche Zone -> Province -> Territoire. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Djolu", "TYPE": "Territoire", "CODE_INS": "4073", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "18852.117751", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone ND\nProvince 26\nTerritoire 005"}
- Hypothèse supplémentaire: Non applicable

### Ikela

- Type détecté: Territoire
- Province: Tshuapa
- Zone FDSU: ND
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Tshuapa -> Territoire -> Ikela
- Dossier parent: Territoire
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoire' dans la branche Zone -> Province -> Territoire. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Ikela", "TYPE": "Territoire", "CODE_INS": "4074", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "21568.876388", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone ND\nProvince 26\nTerritoire 006"}
- Hypothèse supplémentaire: Non applicable

### Monkoto

- Type détecté: Territoire
- Province: Tshuapa
- Zone FDSU: ND
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Tshuapa -> Territoire -> Monkoto
- Dossier parent: Territoire
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoire' dans la branche Zone -> Province -> Territoire. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Monkoto", "TYPE": "Territoire", "CODE_INS": "4076", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "35820.615104", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone ND\nProvince 26\nTerritoire 007"}
- Hypothèse supplémentaire: Non applicable

### Lisala

- Type détecté: Territoire
- Province: Mongala
- Zone FDSU: ND
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Mongala -> Territoires -> Lisala
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Lisala", "TYPE": "Territoire", "CODE_INS": "4061", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "16024.468265", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone ND\nProvince 18\nTerritoire 003"}
- Hypothèse supplémentaire: Non applicable

### Bumba

- Type détecté: Territoire
- Province: Mongala
- Zone FDSU: ND
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Mongala -> Territoires -> Bumba
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Bumba", "TYPE": "Territoire", "CODE_INS": "4062", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "15933.725052", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone ND\nProvince 18\nTerritoire 001"}
- Hypothèse supplémentaire: Non applicable

### Bondanganga

- Type détecté: Territoire
- Province: Mongala
- Zone FDSU: ND
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Mongala -> Territoires -> Bondanganga
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Bongandanga", "TYPE": "Territoire", "CODE_INS": "4063", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "24293.366584", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone ND\nProvince 18\nTerritoire 002"}
- Hypothèse supplémentaire: Non applicable

### Mobayi-Mbongo

- Type détecté: Territoire
- Province: Nord-Ubangi
- Zone FDSU: ND
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Nord-Ubangi -> Territoires -> Mobayi-Mbongo
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Mobayi-Mbongo", "TYPE": "Territoire", "CODE_INS": "4051", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "8598.752637", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone ND\nProvince 20\nTerritoire 004"}
- Hypothèse supplémentaire: Non applicable

### Yakoma

- Type détecté: Territoire
- Province: Nord-Ubangi
- Zone FDSU: ND
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Nord-Ubangi -> Territoires -> Yakoma
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Yakoma", "TYPE": "Territoire", "CODE_INS": "4052", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "16314.793844", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone ND\nProvince 20\nTerritoire 005"}
- Hypothèse supplémentaire: Non applicable

### Businga

- Type détecté: Territoire
- Province: Nord-Ubangi
- Zone FDSU: ND
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Nord-Ubangi -> Territoires -> Businga
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Businga", "TYPE": "Territoire", "CODE_INS": "4053", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "15512.152689", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone ND\nProvince 20\nTerritoire 003"}
- Hypothèse supplémentaire: Non applicable

### Basobolo

- Type détecté: Territoire
- Province: Nord-Ubangi
- Zone FDSU: ND
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Nord-Ubangi -> Territoires -> Basobolo
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Bosobolo", "TYPE": "Territoire", "CODE_INS": "4054", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "12763.852124", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone ND\nProvince 20\nTerritoire 002"}
- Hypothèse supplémentaire: Non applicable

### Gemena

- Type détecté: Territoire
- Province: Sud-Ubangi
- Zone FDSU: ND
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Sud-Ubangi -> Territoires -> Gemena
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Gemena", "TYPE": "Territoire", "CODE_INS": "4031", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "13158.382733", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone ND\nProvince 23\nTerritoire 002"}
- Hypothèse supplémentaire: Non applicable

### Budjala

- Type détecté: Territoire
- Province: Sud-Ubangi
- Zone FDSU: ND
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Sud-Ubangi -> Territoires -> Budjala
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Budjala", "TYPE": "Territoire", "CODE_INS": "4032", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "13387.422788", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone ND\nProvince 23\nTerritoire 001"}
- Hypothèse supplémentaire: Non applicable

### Kungu

- Type détecté: Territoire
- Province: Sud-Ubangi
- Zone FDSU: ND
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Sud-Ubangi -> Territoires -> Kungu
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Kungu", "TYPE": "Territoire", "CODE_INS": "4033", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "12164.479298", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone ND\nProvince 23\nTerritoire 004"}
- Hypothèse supplémentaire: Non applicable

### Libenge

- Type détecté: Territoire
- Province: Sud-Ubangi
- Zone FDSU: ND
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Sud-Ubangi -> Territoires -> Libenge
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Libenge", "TYPE": "Territoire", "CODE_INS": "4034", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "12724.951822", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone ND \nProvince 23\nTerritoire 005"}
- Hypothèse supplémentaire: Non applicable

### Basankusu

- Type détecté: Territoire
- Province: Equateur
- Zone FDSU: ND
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Equateur -> Territoire -> Basankusu
- Dossier parent: Territoire
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoire' dans la branche Zone -> Province -> Territoire. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Basankusu", "TYPE": "Territoire", "CODE_INS": "4021", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "16667.786654", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone ND\nProvince 02\nTerritoire 002"}
- Hypothèse supplémentaire: Non applicable

### Bolomba

- Type détecté: Territoire
- Province: Equateur
- Zone FDSU: ND
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Equateur -> Territoire -> Bolomba
- Dossier parent: Territoire
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoire' dans la branche Zone -> Province -> Territoire. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Bolomba", "TYPE": "Territoire", "CODE_INS": "4022", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "23647.391603", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone ND\nProvince 02\nTerritoire 004"}
- Hypothèse supplémentaire: Non applicable

### Ingende

- Type détecté: Territoire
- Province: Equateur
- Zone FDSU: ND
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Equateur -> Territoire -> Ingende
- Dossier parent: Territoire
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoire' dans la branche Zone -> Province -> Territoire. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Ingende", "TYPE": "Territoire", "CODE_INS": "4023", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "16953.988278", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone ND\nProvince 02\nTerritoire 006"}
- Hypothèse supplémentaire: Non applicable

### Bikoro

- Type détecté: Territoire
- Province: Equateur
- Zone FDSU: ND
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Equateur -> Territoire -> Bikoro
- Dossier parent: Territoire
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoire' dans la branche Zone -> Province -> Territoire. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Bikoro", "TYPE": "Territoire", "CODE_INS": "4024", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "11882.916911", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone ND \nProvince 02\nTerritoire 003"}
- Hypothèse supplémentaire: Non applicable

### Lukolela

- Type détecté: Territoire
- Province: Equateur
- Zone FDSU: ND
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Equateur -> Territoire -> Lukolela
- Dossier parent: Territoire
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoire' dans la branche Zone -> Province -> Territoire. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Lukolela", "TYPE": "Territoire", "CODE_INS": "4025", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "8543.703792", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone ND\nProvince 02\nTerritoire 007"}
- Hypothèse supplémentaire: Non applicable

### Mankanza

- Type détecté: Territoire
- Province: Equateur
- Zone FDSU: ND
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Equateur -> Territoire -> Mankanza
- Dossier parent: Territoire
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoire' dans la branche Zone -> Province -> Territoire. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Makanza", "TYPE": "Territoire", "CODE_INS": "4026", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "7042.509241", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone ND\nProvince 02\nTerritoire 008"}
- Hypothèse supplémentaire: Non applicable

### Bomongo

- Type détecté: Territoire
- Province: Equateur
- Zone FDSU: ND
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE NORD -> Provinces -> Equateur -> Territoire -> Bomongo
- Dossier parent: Territoire
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoire' dans la branche Zone -> Province -> Territoire. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Bomongo", "TYPE": "Territoire", "CODE_INS": "4027", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "16641.946976", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone ND\nProvince 02\nTerritoire 005"}
- Hypothèse supplémentaire: Non applicable

### Kenge

- Type détecté: Territoire
- Province: Kwango
- Zone FDSU: OT
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Kwango -> Territoires -> Kenge
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Kenge", "TYPE": "Territoire", "CODE_INS": "3051", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "18662.39401", "ORIGINE": "Numerisation Saint Moulin / Image satellite"}, "description_values": {}, "description_html": "Zone OT\nProvince 12\nTerritoire 005"}
- Hypothèse supplémentaire: Non applicable

### Feshi

- Type détecté: Territoire
- Province: Kwango
- Zone FDSU: OT
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Kwango -> Territoires -> Feshi
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Feshi", "TYPE": "Territoire", "CODE_INS": "3052", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "19036.446891", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone OT\nProvince 12\nTerritoire 001"}
- Hypothèse supplémentaire: Non applicable

### Kahemba

- Type détecté: Territoire
- Province: Kwango
- Zone FDSU: OT
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Kwango -> Territoires -> Kahemba
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Kahemba", "TYPE": "Territoire", "CODE_INS": "3053", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "20005.370667", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone OT\nProvince 12\nTerritoire 002"}
- Hypothèse supplémentaire: Non applicable

### Kasongo-Lunda

- Type détecté: Territoire
- Province: Kwango
- Zone FDSU: OT
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Kwango -> Territoires -> Kasongo-Lunda
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Kasongo-Lunda", "TYPE": "Territoire", "CODE_INS": "3054", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "27117.060118", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone OT\nProvince 12\nTerritoire 003"}
- Hypothèse supplémentaire: Non applicable

### Popokabaka

- Type détecté: Territoire
- Province: Kwango
- Zone FDSU: OT
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Kwango -> Territoires -> Popokabaka
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Popokabaka", "TYPE": "Territoire", "CODE_INS": "3055", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "6281.630218", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone OT\nProvince 12\nTerritoire 006"}
- Hypothèse supplémentaire: Non applicable

### Bulungu

- Type détecté: Territoire
- Province: Kwilu
- Zone FDSU: OT
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Kwilu -> Territoires -> Bulungu
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Bulungu", "TYPE": "Territoire", "CODE_INS": "3031", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "13253.246802", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone OT\nProvince 13\nTerritoire 003"}
- Hypothèse supplémentaire: Non applicable

### Masi-Manimba

- Type détecté: Territoire
- Province: Kwilu
- Zone FDSU: OT
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Kwilu -> Territoires -> Masi-Manimba
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Masi-Manimba", "TYPE": "Territoire", "CODE_INS": "3032", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "14492.290604", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone OT\nProvince 13\nTerritoire 006"}
- Hypothèse supplémentaire: Non applicable

### Bagata

- Type détecté: Territoire
- Province: Kwilu
- Zone FDSU: OT
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Kwilu -> Territoires -> Bagata
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Bagata", "TYPE": "Territoire", "CODE_INS": "3033", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "17318.855034", "ORIGINE": "Numerisation Saint Moulin / Image satellite"}, "description_values": {}, "description_html": "Zone OT\nProvince 13\nTerritoire 002"}
- Hypothèse supplémentaire: Non applicable

### Idiofa

- Type détecté: Territoire
- Province: Kwilu
- Zone FDSU: OT
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Kwilu -> Territoires -> Idiofa
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Idiofa", "TYPE": "Territoire", "CODE_INS": "3034", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "19283.445356", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone OT\nProvince 13\nTerritoire 005"}
- Hypothèse supplémentaire: Non applicable

### Gungu

- Type détecté: Territoire
- Province: Kwilu
- Zone FDSU: OT
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Kwilu -> Territoires -> Gungu
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Gungu", "TYPE": "Territoire", "CODE_INS": "3035", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "14953.90675", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone OT\nProvince 13\nTerritoire 004"}
- Hypothèse supplémentaire: Non applicable

### Moanda

- Type détecté: Territoire
- Province: Kongo Central
- Zone FDSU: OT
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Kongo Central -> Territoires -> Moanda
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Moanda", "TYPE": "Territoire", "CODE_INS": "2024", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "4005.775338", "ORIGINE": "Numerisation Saint Moulin / Image satellite"}, "description_values": {"zone": "OT Province : 11 Territoire : 009"}, "description_html": "Zone : OT\nProvince : 11\nTerritoire : 009"}
- Hypothèse supplémentaire: Non applicable

### Tshela

- Type détecté: Territoire
- Province: Kongo Central
- Zone FDSU: OT
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Kongo Central -> Territoires -> Tshela
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Tshela", "TYPE": "Territoire", "CODE_INS": "2031", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "3338.585614", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "OT Province : 11 Territoire : 012 Surface : 3338.585614"}, "description_html": "Zone : OT\nProvince : 11\nTerritoire : 012\nSurface : 3338.585614"}
- Hypothèse supplémentaire: Non applicable

### Seke-Banza

- Type détecté: Territoire
- Province: Kongo Central
- Zone FDSU: OT
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Kongo Central -> Territoires -> Seke-Banza
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Seke-Banza", "TYPE": "Territoire", "CODE_INS": "2032", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "3663.54461", "ORIGINE": "Numerisation Saint Moulin / Image satellite"}, "description_values": {"zone": "OT Province : 11 Territoire : 010 Surface : 3663.54461"}, "description_html": "Zone : OT\nProvince : 11\nTerritoire : 010\nSurface : 3663.54461"}
- Hypothèse supplémentaire: Non applicable

### Lukula

- Type détecté: Territoire
- Province: Kongo Central
- Zone FDSU: OT
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Kongo Central -> Territoires -> Lukula
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Lukula", "TYPE": "Territoire", "CODE_INS": "2033", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "3611.720257", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "OT Province : 11 Territoire : 005 Surface : 3611.720257"}, "description_html": "Zone : OT\nProvince : 11\nTerritoire : 005\nSurface : 3611.720257"}
- Hypothèse supplémentaire: Non applicable

### Mbanza-Ngungu

- Type détecté: Territoire
- Province: Kongo Central
- Zone FDSU: OT
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Kongo Central -> Territoires -> Mbanza-Ngungu
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Mbanza-Ngungu", "TYPE": "Territoire", "CODE_INS": "2041", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "8742.470574", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "OT Province : 11 Territoire : 008 Superficie : 3611.720257"}, "description_html": "Zone : OT\nProvince : 11\nTerritoire : 008\nSuperficie : 3611.720257"}
- Hypothèse supplémentaire: Non applicable

### Songololo

- Type détecté: Territoire
- Province: Kongo Central
- Zone FDSU: OT
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Kongo Central -> Territoires -> Songololo
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Songololo", "TYPE": "Territoire", "CODE_INS": "2042", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "8113.800339", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone ot province": "11 Territoire : 011"}, "description_html": "Zone OT\nProvince : 11\nTerritoire : 011"}
- Hypothèse supplémentaire: Non applicable

### Luozi

- Type détecté: Territoire
- Province: Kongo Central
- Zone FDSU: OT
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Kongo Central -> Territoires -> Luozi
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Luozi", "TYPE": "Territoire", "CODE_INS": "2043", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "7260.397041", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone ot province": "11 Territoire : 006"}, "description_html": "Zone OT\nProvince : 11\nTerritoire : 006"}
- Hypothèse supplémentaire: Non applicable

### Madimba

- Type détecté: Territoire
- Province: Kongo Central
- Zone FDSU: OT
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Kongo Central -> Territoires -> Madimba
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Madimba", "TYPE": "Territoire", "CODE_INS": "2051", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "7863.037237", "ORIGINE": "Numerisation Saint Moulin / Image satellite"}, "description_values": {}, "description_html": "Zone OT\nProvince 11\nTerritoire 007"}
- Hypothèse supplémentaire: Non applicable

### Kasangulu

- Type détecté: Territoire
- Province: Kongo Central
- Zone FDSU: OT
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Kongo Central -> Territoires -> Kasangulu
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Kasangulu", "TYPE": "Territoire", "CODE_INS": "2052", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "3816.745487", "ORIGINE": "Numerisation Saint Moulin / Image satellite"}, "description_values": {}, "description_html": "Zone OT\nProvince 11\nTerritoire 003"}
- Hypothèse supplémentaire: Non applicable

### Kimvula

- Type détecté: Territoire
- Province: Kongo Central
- Zone FDSU: OT
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Kongo Central -> Territoires -> Kimvula
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Kimvula", "TYPE": "Territoire", "CODE_INS": "2053", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "3871.960681", "ORIGINE": "Numerisation Saint Moulin / Image satellite"}, "description_values": {}, "description_html": "Zone OT\nProvince 11\nTerritoire 004"}
- Hypothèse supplémentaire: Non applicable

### Bolobo

- Type détecté: Territoire
- Province: Maindombe
- Zone FDSU: OT
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Maindombe -> Territoire -> Bolobo
- Dossier parent: Territoire
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoire' dans la branche Zone -> Province -> Territoire. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Bolobo", "TYPE": "Territoire", "CODE_INS": "3061", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "4124.379781", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone OT\nProvince 16\nTerritoire 001"}
- Hypothèse supplémentaire: Non applicable

### Kwamouth

- Type détecté: Territoire
- Province: Maindombe
- Zone FDSU: OT
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Maindombe -> Territoire -> Kwamouth
- Dossier parent: Territoire
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoire' dans la branche Zone -> Province -> Territoire. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Kwamouth", "TYPE": "Territoire", "CODE_INS": "3062", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "14552.102618", "ORIGINE": "Numerisation Saint Moulin / Image satellite"}, "description_values": {}, "description_html": "Zone OT \nProvince 16\nTerritoire 006"}
- Hypothèse supplémentaire: Non applicable

### Mushie

- Type détecté: Territoire
- Province: Maindombe
- Zone FDSU: OT
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Maindombe -> Territoire -> Mushie
- Dossier parent: Territoire
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoire' dans la branche Zone -> Province -> Territoire. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Mushie", "TYPE": "Territoire", "CODE_INS": "3063", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "11859.907446", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone OT\nProvince 16\nTerritoire 007"}
- Hypothèse supplémentaire: Non applicable

### Yumbi

- Type détecté: Territoire
- Province: Maindombe
- Zone FDSU: OT
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Maindombe -> Territoire -> Yumbi
- Dossier parent: Territoire
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoire' dans la branche Zone -> Province -> Territoire. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Yumbi", "TYPE": "Territoire", "CODE_INS": "3064", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "1214.926642", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone OT\nProvince 16\nTerritoire 009"}
- Hypothèse supplémentaire: Non applicable

### Inongo

- Type détecté: Territoire
- Province: Maindombe
- Zone FDSU: OT
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Maindombe -> Territoire -> Inongo
- Dossier parent: Territoire
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoire' dans la branche Zone -> Province -> Territoire. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Inongo", "TYPE": "Territoire", "CODE_INS": "3021", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "24017.229487", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone OT\nProvince 16\nTerritoire 003"}
- Hypothèse supplémentaire: Non applicable

### Kiri

- Type détecté: Territoire
- Province: Maindombe
- Zone FDSU: OT
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Maindombe -> Territoire -> Kiri
- Dossier parent: Territoire
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoire' dans la branche Zone -> Province -> Territoire. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Kiri", "TYPE": "Territoire", "CODE_INS": "3022", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "12613.548066", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone OT\nProvince 16\nTerritoire 004"}
- Hypothèse supplémentaire: Non applicable

### Oshwe

- Type détecté: Territoire
- Province: Maindombe
- Zone FDSU: OT
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Maindombe -> Territoire -> Oshwe
- Dossier parent: Territoire
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoire' dans la branche Zone -> Province -> Territoire. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Oshwe", "TYPE": "Territoire", "CODE_INS": "3023", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "41732.361552", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {}, "description_html": "Zone OT\nProvince 16\nTerritoire 008"}
- Hypothèse supplémentaire: Non applicable

### Kutu

- Type détecté: Territoire
- Province: Maindombe
- Zone FDSU: OT
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE OUEST -> Provinces -> Maindombe -> Territoire -> Kutu
- Dossier parent: Territoire
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoire' dans la branche Zone -> Province -> Territoire. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Kutu", "TYPE": "Territoire", "CODE_INS": "3024", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (UTC+01:00)", "SURFACE": "18673.710844", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "OT Province 16 Territoire 005"}, "description_html": "Zone : OT\nProvince 16\nTerritoire 005"}
- Hypothèse supplémentaire: Non applicable

### Luebo

- Type détecté: Territoire
- Province: Kasai
- Zone FDSU: CE
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Kasai -> Territoires -> Luebo
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Luebo", "TYPE": "Territoire", "CODE_INS": "9031", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "8246.858111", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "CE Province : 07 Territoire : 005"}, "description_html": "Zone : CE\nProvince : 07\nTerritoire : 005"}
- Hypothèse supplémentaire: Non applicable

### Kamonia

- Type détecté: Territoire
- Province: Kasai
- Zone FDSU: CE
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Kasai -> Territoires -> Kamonia
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Kamonia", "TYPE": "Territoire", "CODE_INS": "9032", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "27491.939085", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "CE Province : 07 Territoire : 002"}, "description_html": "Zone : CE\nProvince : 07\nTerritoire : 002"}
- Hypothèse supplémentaire: Non applicable

### Ilebo

- Type détecté: Territoire
- Province: Kasai
- Zone FDSU: CE
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Kasai -> Territoires -> Ilebo
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Ilebo", "TYPE": "Territoire", "CODE_INS": "9033", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "16224.455382", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "CE Province : 07 Territoire : 004"}, "description_html": "Zone : CE\nProvince : 07\nTerritoire : 004"}
- Hypothèse supplémentaire: Non applicable

### Mweka

- Type détecté: Territoire
- Province: Kasai
- Zone FDSU: CE
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Kasai -> Territoires -> Mweka
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Mweka", "TYPE": "Territoire", "CODE_INS": "9034", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "19788.271679", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "CE Province : 07 Territoire : 006"}, "description_html": "Zone : CE\nProvince : 07\nTerritoire : 006"}
- Hypothèse supplémentaire: Non applicable

### Dekese

- Type détecté: Territoire
- Province: Kasai
- Zone FDSU: CE
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Kasai -> Territoires -> Dekese
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Dekese", "TYPE": "Territoire", "CODE_INS": "9035", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "25734.154851", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "CE Province : 07 Territoire : 003"}, "description_html": "Zone : CE\nProvince : 07\nTerritoire : 003"}
- Hypothèse supplémentaire: Non applicable

### Dibaya

- Type détecté: Territoire
- Province: Kasai Central
- Zone FDSU: CE
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Kasai Central -> Territoires -> Dibaya
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Dibaya", "TYPE": "Territoire", "CODE_INS": "9021", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "7180.032488", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "CE Province : 08 Territoire : 007"}, "description_html": "Zone : CE\nProvince : 08\nTerritoire : 007"}
- Hypothèse supplémentaire: Non applicable

### Luiza

- Type détecté: Territoire
- Province: Kasai Central
- Zone FDSU: CE
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Kasai Central -> Territoires -> Luiza
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Luiza", "TYPE": "Territoire", "CODE_INS": "9022", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "16099.304784", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "CE Province : 08 Territoire : 010"}, "description_html": "Zone : CE\nProvince : 08\nTerritoire : 010"}
- Hypothèse supplémentaire: Non applicable

### Kazumba

- Type détecté: Territoire
- Province: Kasai Central
- Zone FDSU: CE
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Kasai Central -> Territoires -> Kazumba
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Kazumba", "TYPE": "Territoire", "CODE_INS": "9023", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "12460.834152", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "CE Province : 08 Territoire : 009"}, "description_html": "Zone : CE\nProvince : 08\nTerritoire : 009"}
- Hypothèse supplémentaire: Non applicable

### Demba

- Type détecté: Territoire
- Province: Kasai Central
- Zone FDSU: CE
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Kasai Central -> Territoires -> Demba
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Demba", "TYPE": "Territoire", "CODE_INS": "9024", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "9490.977156", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "CE Province : 08 Territoire : 006"}, "description_html": "Zone : CE\nProvince : 08\nTerritoire : 006"}
- Hypothèse supplémentaire: Non applicable

### Dimbelenge

- Type détecté: Territoire
- Province: Kasai Central
- Zone FDSU: CE
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Kasai Central -> Territoires -> Dimbelenge
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Dimbelenge", "TYPE": "Territoire", "CODE_INS": "9025", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "11770.068225", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "CE Province : 08 Territoire : 008"}, "description_html": "Zone : CE\nProvince : 08\nTerritoire : 008"}
- Hypothèse supplémentaire: Non applicable

### Miabi

- Type détecté: Territoire
- Province: Kasai Oriental
- Zone FDSU: CE
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Kasai Oriental -> Territoires -> Miabi
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Miabi", "TYPE": "Territoire", "CODE_INS": "8021", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "1655.415734", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "CE Province : 09 Territoire : 009"}, "description_html": "Zone : CE\nProvince : 09\nTerritoire : 009"}
- Hypothèse supplémentaire: Non applicable

### Kabeya-Kamwanga

- Type détecté: Territoire
- Province: Kasai Oriental
- Zone FDSU: CE
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Kasai Oriental -> Territoires -> Kabeya-Kamwanga
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Kabeya-Kamwanga", "TYPE": "Territoire", "CODE_INS": "8022", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "2279.680127", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "CE Province : 09 Territoire : 006"}, "description_html": "Zone : CE\nProvince : 09\nTerritoire : 006"}
- Hypothèse supplémentaire: Non applicable

### Lupatapata

- Type détecté: Territoire
- Province: Kasai Oriental
- Zone FDSU: CE
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Kasai Oriental -> Territoires -> Lupatapata
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Lupatapata", "TYPE": "Territoire", "CODE_INS": "8023", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "2123.062713", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "CE Province : 09 Territoire : 008"}, "description_html": "Zone : CE\nProvince : 09\nTerritoire : 008"}
- Hypothèse supplémentaire: Non applicable

### Katanda

- Type détecté: Territoire
- Province: Kasai Oriental
- Zone FDSU: CE
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Kasai Oriental -> Territoires -> Katanda
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Katanda", "TYPE": "Territoire", "CODE_INS": "8024", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "2187.680741", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "CE Province : 09 Territoire : 007"}, "description_html": "Zone : CE\nProvince : 09\nTerritoire : 007"}
- Hypothèse supplémentaire: Non applicable

### Tshilenge

- Type détecté: Territoire
- Province: Kasai Oriental
- Zone FDSU: CE
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Kasai Oriental -> Territoires -> Tshilenge
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Tshilenge", "TYPE": "Territoire", "CODE_INS": "8025", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "1932.017032", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "CE Province : 09 Territoire : 010"}, "description_html": "Zone : CE\nProvince : 09\nTerritoire : 010"}
- Hypothèse supplémentaire: Non applicable

### Luilu

- Type détecté: Territoire
- Province: Lomami
- Zone FDSU: CE
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Lomami -> Territoires -> Luilu
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Luilu", "TYPE": "Territoire", "CODE_INS": "8041", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "10772.559301", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "CE Province : 14 Territoire : 006"}, "description_html": "Zone : CE\nProvince : 14\nTerritoire : 006"}
- Hypothèse supplémentaire: Non applicable

### Kamiji

- Type détecté: Territoire
- Province: Lomami
- Zone FDSU: CE
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Lomami -> Territoires -> Kamiji
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Kamiji", "TYPE": "Territoire", "CODE_INS": "8042", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "1291.044075", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "CE Province : 14 Territoire : 004"}, "description_html": "Zone : CE\nProvince : 14\nTerritoire : 004"}
- Hypothèse supplémentaire: Non applicable

### Ngandajika

- Type détecté: Territoire
- Province: Lomami
- Zone FDSU: CE
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Lomami -> Territoires -> Ngandajika
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Ngandajika", "TYPE": "Territoire", "CODE_INS": "8043", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "5738.286055", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "CE Province : 14 Territoire : 007"}, "description_html": "Zone : CE\nProvince : 14\nTerritoire : 007"}
- Hypothèse supplémentaire: Non applicable

### Kabinda

- Type détecté: Territoire
- Province: Lomami
- Zone FDSU: CE
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Lomami -> Territoires -> Kabinda
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Kabinda", "TYPE": "Territoire", "CODE_INS": "8044", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "14415.457782", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "CE Province : 14 Territoire : 003"}, "description_html": "Zone : CE\nProvince : 14\nTerritoire : 003"}
- Hypothèse supplémentaire: Non applicable

### Lubao

- Type détecté: Territoire
- Province: Lomami
- Zone FDSU: CE
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Lomami -> Territoires -> Lubao
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Lubao", "TYPE": "Territoire", "CODE_INS": "8045", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "22245.743512", "ORIGINE": "Numerisation Saint Moulin / Image satellite"}, "description_values": {"zone": "CE Province : 14 Territoire : 005"}, "description_html": "Zone : CE\nProvince : 14\nTerritoire : 005"}
- Hypothèse supplémentaire: Non applicable

### Lusambo

- Type détecté: Territoire
- Province: Sankuru
- Zone FDSU: CE
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Sankuru -> Territoires -> Lusambo
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Lusambo", "TYPE": "Territoire", "CODE_INS": "8031", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "11693.850213", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "CE Province : 21 Territoire : 006"}, "description_html": "Zone : CE\nProvince : 21\nTerritoire : 006"}
- Hypothèse supplémentaire: Non applicable

### Kole

- Type détecté: Territoire
- Province: Sankuru
- Zone FDSU: CE
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Sankuru -> Territoires -> Kole
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Kole", "TYPE": "Territoire", "CODE_INS": "8032", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "18021.674294", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "CE Province : 21 Territoire : 002"}, "description_html": "Zone : CE\nProvince : 21\nTerritoire : 002"}
- Hypothèse supplémentaire: Non applicable

### Lomela

- Type détecté: Territoire
- Province: Sankuru
- Zone FDSU: CE
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Sankuru -> Territoires -> Lomela
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Lomela", "TYPE": "Territoire", "CODE_INS": "8033", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "28733.267849", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "CE Province : 21 Territoire : 004"}, "description_html": "Zone : CE\nProvince : 21\nTerritoire : 004"}
- Hypothèse supplémentaire: Non applicable

### Katako-Kombe

- Type détecté: Territoire
- Province: Sankuru
- Zone FDSU: CE
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Sankuru -> Territoires -> Katako-Kombe
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Katako-Kombe", "TYPE": "Territoire", "CODE_INS": "8034", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "24026.574881", "ORIGINE": "Numerisation Saint Moulin / Image satellite"}, "description_values": {"zone": "CE Province : 21 Territoire : 001"}, "description_html": "Zone : CE\nProvince : 21\nTerritoire : 001"}
- Hypothèse supplémentaire: Non applicable

### Lubefu

- Type détecté: Territoire
- Province: Sankuru
- Zone FDSU: CE
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Sankuru -> Territoires -> Lubefu
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Lubefu", "TYPE": "Territoire", "CODE_INS": "8035", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "13691.759965", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "CE Province : 21 Territoire : 005"}, "description_html": "Zone : CE\nProvince : 21\nTerritoire : 005"}
- Hypothèse supplémentaire: Non applicable

### Lodja

- Type détecté: Territoire
- Province: Sankuru
- Zone FDSU: CE
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Sankuru -> Territoires -> Lodja
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Lodja", "TYPE": "Territoire", "CODE_INS": "8036", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "12503.918045", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "CE Province : 21 Territoire : 003"}, "description_html": "Zone : CE\nProvince : 21\nTerritoire : 003"}
- Hypothèse supplémentaire: Non applicable

### Kipushi

- Type détecté: Territoire
- Province: Haut-Katanga
- Zone FDSU: SD
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE SUD -> Provinces -> Haut-Katanga -> Territoires -> Kipushi
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Kipushi", "TYPE": "Territoire", "CODE_INS": "7071", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "8969.454341", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "SD Province : 03 Territoire : 012"}, "description_html": "Zone : SD\nProvince : 03\nTerritoire : 012"}
- Hypothèse supplémentaire: Non applicable

### Sakania

- Type détecté: Territoire
- Province: Haut-Katanga
- Zone FDSU: SD
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE SUD -> Provinces -> Haut-Katanga -> Territoires -> Sakania
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Sakania", "TYPE": "Territoire", "CODE_INS": "7072", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "22141.305767", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "SD Province : 03 Territoire : 015"}, "description_html": "Zone : SD\nProvince : 03\nTerritoire : 015"}
- Hypothèse supplémentaire: Non applicable

### Kasenga

- Type détecté: Territoire
- Province: Haut-Katanga
- Zone FDSU: SD
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE SUD -> Provinces -> Haut-Katanga -> Territoires -> Kasenga
- Dossier parent: Territoires
- Géométrie: MultiGeometry
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Kasenga", "TYPE": "Territoire", "CODE_INS": "7073", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "24691.367123", "ORIGINE": "Numerisation Saint Moulin / Image satellite"}, "description_values": {"zone": "SD Province : 03 Territoire : 011"}, "description_html": "Zone : SD\nProvince : 03\nTerritoire : 011"}
- Hypothèse supplémentaire: Non applicable

### Pweto

- Type détecté: Territoire
- Province: Haut-Katanga
- Zone FDSU: SD
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE SUD -> Provinces -> Haut-Katanga -> Territoires -> Pweto
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Pweto", "TYPE": "Territoire", "CODE_INS": "7075", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "22421.275633", "ORIGINE": "Numerisation Saint Moulin / Image satellite"}, "description_values": {"zone": "SD Province : 03 Territoire : 014"}, "description_html": "Zone : SD\nProvince : 03\nTerritoire : 014"}
- Hypothèse supplémentaire: Non applicable

### Kambove

- Type détecté: Territoire
- Province: Haut-Katanga
- Zone FDSU: SD
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE SUD -> Provinces -> Haut-Katanga -> Territoires -> Kambove
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Kambove", "TYPE": "Territoire", "CODE_INS": "7076", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "22235.771501", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "SD Province : 03 Territoire : 010"}, "description_html": "Zone : SD\nProvince : 03\nTerritoire : 010"}
- Hypothèse supplémentaire: Non applicable

### Mitwaba

- Type détecté: Territoire
- Province: Haut-Katanga
- Zone FDSU: SD
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE SUD -> Provinces -> Haut-Katanga -> Territoires -> Mitwaba
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Mitwaba", "TYPE": "Territoire", "CODE_INS": "7074", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "24933.074388", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "SD Province : 03 Territoire : 013"}, "description_html": "Zone : SD\nProvince : 03\nTerritoire : 013"}
- Hypothèse supplémentaire: Non applicable

### Kalemie

- Type détecté: Territoire
- Province: Tanganyika
- Zone FDSU: SD
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE SUD -> Provinces -> Tanganyika -> Territoires -> Kalemie
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Kalemie", "TYPE": "Territoire", "CODE_INS": "7061", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "21155.114196", "ORIGINE": "Numerisation Saint Moulin / Image satellite"}, "description_values": {"zone": "SD Province : 24 Territoire : 002"}, "description_html": "Zone : SD\nProvince : 24\nTerritoire : 002"}
- Hypothèse supplémentaire: Non applicable

### Moba

- Type détecté: Territoire
- Province: Tanganyika
- Zone FDSU: SD
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE SUD -> Provinces -> Tanganyika -> Territoires -> Moba
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Moba", "TYPE": "Territoire", "CODE_INS": "7062", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "23079.538158", "ORIGINE": "Numerisation Saint Moulin / Image satellite"}, "description_values": {"zone": "SD Province : 24 Territoire : 006"}, "description_html": "Zone : SD\nProvince : 24\nTerritoire : 006"}
- Hypothèse supplémentaire: Non applicable

### Manono

- Type détecté: Territoire
- Province: Tanganyika
- Zone FDSU: SD
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE SUD -> Provinces -> Tanganyika -> Territoires -> Manono
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Manono", "TYPE": "Territoire", "CODE_INS": "7063", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "34614.674195", "ORIGINE": "Numerisation Saint Moulin / Image satellite"}, "description_values": {"zone": "SD Province : 24 Territoire : 005"}, "description_html": "Zone : SD\nProvince : 24\nTerritoire : 005"}
- Hypothèse supplémentaire: Non applicable

### Kabalo

- Type détecté: Territoire
- Province: Tanganyika
- Zone FDSU: SD
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE SUD -> Provinces -> Tanganyika -> Territoires -> Kabalo
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Kabalo", "TYPE": "Territoire", "CODE_INS": "7064", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "14778.677206", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "SD Province : 24 Territoire : 003"}, "description_html": "Zone : SD\nProvince : 24\nTerritoire : 003"}
- Hypothèse supplémentaire: Non applicable

### Kongolo

- Type détecté: Territoire
- Province: Tanganyika
- Zone FDSU: SD
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE SUD -> Provinces -> Tanganyika -> Territoires -> Kongolo
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Kongolo", "TYPE": "Territoire", "CODE_INS": "7065", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "13171.160812", "ORIGINE": "Numerisation Saint Moulin / Image satellite"}, "description_values": {"zone": "SD Province : 24 Territoire : 004"}, "description_html": "Zone : SD\nProvince : 24\nTerritoire : 004"}
- Hypothèse supplémentaire: Non applicable

### Nyunzu

- Type détecté: Territoire
- Province: Tanganyika
- Zone FDSU: SD
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE SUD -> Provinces -> Tanganyika -> Territoires -> Nyunzu
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Nyunzu", "TYPE": "Territoire", "CODE_INS": "7066", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "15741.305731", "ORIGINE": "Numerisation Saint Moulin / Image satellite"}, "description_values": {"zone": "SD Province : 24 Territoire : 007"}, "description_html": "Zone : SD\nProvince : 24\nTerritoire : 007"}
- Hypothèse supplémentaire: Non applicable

### Kamina

- Type détecté: Territoire
- Province: Haut-Lomami
- Zone FDSU: SD
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE SUD -> Provinces -> Haut-Lomami -> Territoires -> Kamina
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Kamina", "TYPE": "Territoire", "CODE_INS": "7051", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "41887.246353", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "SD Province : 04 Territoire : 002"}, "description_html": "Zone : SD\nProvince : 04\nTerritoire : 002"}
- Hypothèse supplémentaire: Non applicable

### Kaniama

- Type détecté: Territoire
- Province: Haut-Lomami
- Zone FDSU: SD
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE SUD -> Provinces -> Haut-Lomami -> Territoires -> Kaniama
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Kaniama", "TYPE": "Territoire", "CODE_INS": "7052", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "13893.650731", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "SD Province : 04 Territoire : 005"}, "description_html": "Zone : SD\nProvince : 04\nTerritoire : 005"}
- Hypothèse supplémentaire: Non applicable

### Kabongo

- Type détecté: Territoire
- Province: Haut-Lomami
- Zone FDSU: SD
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE SUD -> Provinces -> Haut-Lomami -> Territoires -> Kabongo
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Kabongo", "TYPE": "Territoire", "CODE_INS": "7053", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "20897.890109", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "SD Province : 04 Territoire : 004"}, "description_html": "Zone : SD\nProvince : 04\nTerritoire : 004"}
- Hypothèse supplémentaire: Non applicable

### Malemba-Nkulu

- Type détecté: Territoire
- Province: Haut-Lomami
- Zone FDSU: SD
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE SUD -> Provinces -> Haut-Lomami -> Territoires -> Malemba-Nkulu
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Malemba-Nkulu", "TYPE": "Territoire", "CODE_INS": "7054", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "15297.709747", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "SD Province : 04 Territoire : 006"}, "description_html": "Zone : SD\nProvince : 04\nTerritoire : 006"}
- Hypothèse supplémentaire: Non applicable

### Bukama

- Type détecté: Territoire
- Province: Haut-Lomami
- Zone FDSU: SD
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE SUD -> Provinces -> Haut-Lomami -> Territoires -> Bukama
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Bukama", "TYPE": "Territoire", "CODE_INS": "7055", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "19398.474798", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "SD Province : 04 Territoire : 003"}, "description_html": "Zone : SD\nProvince : 04\nTerritoire : 003"}
- Hypothèse supplémentaire: Non applicable

### Mutshatsha

- Type détecté: Territoire
- Province: Lualaba
- Zone FDSU: SD
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE SUD -> Provinces -> Lualaba -> Territoires -> Mutshatsha
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Mutshatsha", "TYPE": "Territoire", "CODE_INS": "7033", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "24830.40011", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "SD Province : 15 Territoire : 005"}, "description_html": "Zone : SD\nProvince : 15\nTerritoire : 005"}
- Hypothèse supplémentaire: Non applicable

### Lubudi

- Type détecté: Territoire
- Province: Lualaba
- Zone FDSU: SD
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE SUD -> Provinces -> Lualaba -> Territoires -> Lubudi
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Lubudi", "TYPE": "Territoire", "CODE_INS": "7034", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "18939.509051", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "SD Province : 15 Territoire : 002"}, "description_html": "Zone : SD\nProvince : 15\nTerritoire : 002"}
- Hypothèse supplémentaire: Non applicable

### Dilolo

- Type détecté: Territoire
- Province: Lualaba
- Zone FDSU: SD
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE SUD -> Provinces -> Lualaba -> Territoires -> Dilolo
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Dilolo", "TYPE": "Territoire", "CODE_INS": "7041", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "25648.434799", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "SD Province : 15 Territoire : 003"}, "description_html": "Zone : SD\nProvince : 15\nTerritoire : 003"}
- Hypothèse supplémentaire: Non applicable

### Sandoa

- Type détecté: Territoire
- Province: Lualaba
- Zone FDSU: SD
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE SUD -> Provinces -> Lualaba -> Territoires -> Sandoa
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Sandoa", "TYPE": "Territoire", "CODE_INS": "7042", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "30404.433426", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "SD Province : 15 Territoire : 006"}, "description_html": "Zone : SD\nProvince : 15\nTerritoire : 006"}
- Hypothèse supplémentaire: Non applicable

### Kapanga

- Type détecté: Territoire
- Province: Lualaba
- Zone FDSU: SD
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE SUD -> Provinces -> Lualaba -> Territoires -> Kapanga
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Kapanga", "TYPE": "Territoire", "CODE_INS": "7043", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "25509.767307", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "SD Province : 15 Territoire : 004"}, "description_html": "Zone : SD\nProvince : 15\nTerritoire : 004"}
- Hypothèse supplémentaire: Non applicable

### Irumu

- Type détecté: Territoire
- Province: Ituri
- Zone FDSU: ET
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Ituri -> Territoires -> Irumu
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Irumu", "TYPE": "Territoire", "CODE_INS": "5051", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "7709.903472", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "ET Province : 06 Territoire : 004"}, "description_html": "Zone : ET\nProvince : 06\nTerritoire : 004"}
- Hypothèse supplémentaire: Non applicable

### Mambasa

- Type détecté: Territoire
- Province: Ituri
- Zone FDSU: ET
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Ituri -> Territoires -> Mambasa
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Mambasa", "TYPE": "Territoire", "CODE_INS": "5052", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "35604.976632", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "ET Province : 06 Territoire : 006"}, "description_html": "Zone : ET\nProvince : 06\nTerritoire : 006"}
- Hypothèse supplémentaire: Non applicable

### Djugu

- Type détecté: Territoire
- Province: Ituri
- Zone FDSU: ET
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Ituri -> Territoires -> Djugu
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Djugu", "TYPE": "Territoire", "CODE_INS": "5053", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "7955.027628", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "ET Province : 06 Territoire : 003"}, "description_html": "Zone : ET\nProvince : 06\nTerritoire : 003"}
- Hypothèse supplémentaire: Non applicable

### Mahagi

- Type détecté: Territoire
- Province: Ituri
- Zone FDSU: ET
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Ituri -> Territoires -> Mahagi
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Mahagi", "TYPE": "Territoire", "CODE_INS": "5054", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "4617.346565", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "ET Province : 06 Territoire : 005"}, "description_html": "Zone : ET\nProvince : 06\nTerritoire : 005"}
- Hypothèse supplémentaire: Non applicable

### Aru

- Type détecté: Territoire
- Province: Ituri
- Zone FDSU: ET
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Ituri -> Territoires -> Aru
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Aru", "TYPE": "Territoire", "CODE_INS": "5055", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "6948.841745", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "ET Province : 06 Territoire : 002"}, "description_html": "Zone : ET\nProvince : 06\nTerritoire : 002"}
- Hypothèse supplémentaire: Non applicable

### Nyiragongo

- Type détecté: Territoire
- Province: Nord-Kivu
- Zone FDSU: ET
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Nord-Kivu -> Territoires -> Nyiragongo
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Nyiragongo", "TYPE": "Territoire", "CODE_INS": "6121", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "443.793046", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "ET Province : 19 Territoire : 012"}, "description_html": "Zone : ET\nProvince : 19\nTerritoire : 012"}
- Hypothèse supplémentaire: Non applicable

### Walikale

- Type détecté: Territoire
- Province: Nord-Kivu
- Zone FDSU: ET
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Nord-Kivu -> Territoires -> Walikale
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Walikale", "TYPE": "Territoire", "CODE_INS": "6122", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "23702.324201", "ORIGINE": "Numerisation Saint Moulin / Image satellite"}, "description_values": {"zone": "ET Province : 19 Territoire : 014"}, "description_html": "Zone : ET\nProvince : 19\nTerritoire : 014"}
- Hypothèse supplémentaire: Non applicable

### Lubero

- Type détecté: Territoire
- Province: Nord-Kivu
- Zone FDSU: ET
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Nord-Kivu -> Territoires -> Lubero
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Lubero", "TYPE": "Territoire", "CODE_INS": "6123", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "15422.307647", "ORIGINE": "Numerisation Saint Moulin / Image satellite"}, "description_values": {"zone": "ET Province : 19 Territoire : 010"}, "description_html": "Zone : ET\nProvince : 19\nTerritoire : 010"}
- Hypothèse supplémentaire: Non applicable

### Oicha

- Type détecté: Territoire
- Province: Nord-Kivu
- Zone FDSU: ET
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Nord-Kivu -> Territoires -> Oicha
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Oicha", "TYPE": "Territoire", "CODE_INS": "6124", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "7354.309647", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "ET Province : 19 Territoire : 008"}, "description_html": "Zone : ET\nProvince : 19\nTerritoire : 008"}
- Hypothèse supplémentaire: Non applicable

### Rutshuru

- Type détecté: Territoire
- Province: Nord-Kivu
- Zone FDSU: ET
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Nord-Kivu -> Territoires -> Rutshuru
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Rutshuru", "TYPE": "Territoire", "CODE_INS": "6125", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "5385.055882", "ORIGINE": "Numerisation Saint Moulin / Image satellite"}, "description_values": {"zone": "ET Province : 19 Territoire : 013"}, "description_html": "Zone : ET\nProvince : 19\nTerritoire : 013"}
- Hypothèse supplémentaire: Non applicable

### Masisi

- Type détecté: Territoire
- Province: Nord-Kivu
- Zone FDSU: ET
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Nord-Kivu -> Territoires -> Masisi
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Masisi", "TYPE": "Territoire", "CODE_INS": "6126", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "4318.786982", "ORIGINE": "Numerisation Saint Moulin / Image satellite"}, "description_values": {"zone": "ET Province : 19 Territoire : 011"}, "description_html": "Zone : ET\nProvince : 19\nTerritoire : 011"}
- Hypothèse supplémentaire: Non applicable

### Walungu

- Type détecté: Territoire
- Province: Sud-Kivu
- Zone FDSU: ET
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Sud-Kivu -> Territoires -> Walungu
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Walungu", "TYPE": "Territoire", "CODE_INS": "6221", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "1863.604652", "ORIGINE": "Numerisation Saint Moulin / Image satellite"}, "description_values": {"zone": "ET Province : 22 Territoire : 011"}, "description_html": "Zone : ET\nProvince : 22\nTerritoire : 011"}
- Hypothèse supplémentaire: Non applicable

### Uvira

- Type détecté: Territoire
- Province: Sud-Kivu
- Zone FDSU: ET
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Sud-Kivu -> Territoires -> Uvira
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Uvira", "TYPE": "Territoire", "CODE_INS": "6222", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "3360.157107", "ORIGINE": "Numerisation Saint Moulin / Image satellite"}, "description_values": {"zone": "ET Province : 22 Territoire : 010"}, "description_html": "Zone : ET\nProvince : 22\nTerritoire : 010"}
- Hypothèse supplémentaire: Non applicable

### Fizi

- Type détecté: Territoire
- Province: Sud-Kivu
- Zone FDSU: ET
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Sud-Kivu -> Territoires -> Fizi
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Fizi", "TYPE": "Territoire", "CODE_INS": "6223", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "11699.632049", "ORIGINE": "Numerisation Saint Moulin / Image satellite"}, "description_values": {"zone": "ET Province : 22 Territoire : 004"}, "description_html": "Zone : ET\nProvince : 22\nTerritoire : 004"}
- Hypothèse supplémentaire: Non applicable

### Mwenga

- Type détecté: Territoire
- Province: Sud-Kivu
- Zone FDSU: ET
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Sud-Kivu -> Territoires -> Mwenga
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Mwenga", "TYPE": "Territoire", "CODE_INS": "6224", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "11105.78354", "ORIGINE": "Numerisation Saint Moulin / Image satellite"}, "description_values": {"zone": "ET Province : 22 Territoire : 008"}, "description_html": "Zone : ET\nProvince : 22\nTerritoire : 008"}
- Hypothèse supplémentaire: Non applicable

### Shabunda

- Type détecté: Territoire
- Province: Sud-Kivu
- Zone FDSU: ET
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Sud-Kivu -> Territoires -> Shabunda
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Shabunda", "TYPE": "Territoire", "CODE_INS": "6225", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "24858.433061", "ORIGINE": "Numerisation Saint Moulin / Image satellite"}, "description_values": {"zone": "ET Province : 22 Territoire : 009"}, "description_html": "Zone : ET\nProvince : 22\nTerritoire : 009"}
- Hypothèse supplémentaire: Non applicable

### Kalehe

- Type détecté: Territoire
- Province: Sud-Kivu
- Zone FDSU: ET
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Sud-Kivu -> Territoires -> Kalehe
- Dossier parent: Territoires
- Géométrie: MultiGeometry
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Kalehe", "TYPE": "Territoire", "CODE_INS": "6226", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "4201.314242", "ORIGINE": "Numerisation Saint Moulin / Image satellite"}, "description_values": {"zone": "ET Province : 22 Territoire : 007"}, "description_html": "Zone : ET\nProvince : 22\nTerritoire : 007"}
- Hypothèse supplémentaire: Non applicable

### Idjwi

- Type détecté: Territoire
- Province: Sud-Kivu
- Zone FDSU: ET
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Sud-Kivu -> Territoires -> Idjwi
- Dossier parent: Territoires
- Géométrie: MultiGeometry
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Idjwi", "TYPE": "Territoire", "CODE_INS": "6227", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "280.693187", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "ET Province : 22 Territoire : 005"}, "description_html": "Zone : ET\nProvince : 22\nTerritoire : 005"}
- Hypothèse supplémentaire: Non applicable

### Kabare

- Type détecté: Territoire
- Province: Sud-Kivu
- Zone FDSU: ET
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Sud-Kivu -> Territoires -> Kabare
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Kabare", "TYPE": "Territoire", "CODE_INS": "6228", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "1887.359878", "ORIGINE": "Numerisation Saint Moulin / Image satellite"}, "description_values": {"zone": "ET Province : 22 Territoire : 006"}, "description_html": "Zone : ET\nProvince : 22\nTerritoire : 006"}
- Hypothèse supplémentaire: Non applicable

### Kabambare

- Type détecté: Territoire
- Province: Maniema
- Zone FDSU: ET
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Maniema -> Territoires -> Kabambare
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Kabambare", "TYPE": "Territoire", "CODE_INS": "6321", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "18969.78883", "ORIGINE": "Numerisation Saint Moulin / Image satellite"}, "description_values": {"zone": "ET Province : 17 Territoire : 002"}, "description_html": "Zone : ET\nProvince : 17\nTerritoire : 002"}
- Hypothèse supplémentaire: Non applicable

### Kibombo

- Type détecté: Territoire
- Province: Maniema
- Zone FDSU: ET
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Maniema -> Territoires -> Kibombo
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Kibombo", "TYPE": "Territoire", "CODE_INS": "6322", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "22567.288284", "ORIGINE": "Numerisation Saint Moulin / Image satellite"}, "description_values": {"zone": "ET Province : 17 Territoire : 005"}, "description_html": "Zone : ET\nProvince : 17\nTerritoire : 005"}
- Hypothèse supplémentaire: Non applicable

### Lubutu

- Type détecté: Territoire
- Province: Maniema
- Zone FDSU: ET
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Maniema -> Territoires -> Lubutu
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Lubutu", "TYPE": "Territoire", "CODE_INS": "6323", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "15912.051612", "ORIGINE": "Numerisation Saint Moulin / Image satellite"}, "description_values": {"zone": "ET Province : 17 Territoire : 006"}, "description_html": "Zone : ET\nProvince : 17\nTerritoire : 006"}
- Hypothèse supplémentaire: Non applicable

### Pangi

- Type détecté: Territoire
- Province: Maniema
- Zone FDSU: ET
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Maniema -> Territoires -> Pangi
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Pangi", "TYPE": "Territoire", "CODE_INS": "6324", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "14413.530931", "ORIGINE": "Numerisation Saint Moulin / Image satellite"}, "description_values": {"zone": "ET Province : 17 Territoire : 007"}, "description_html": "Zone : ET\nProvince : 17\nTerritoire : 007"}
- Hypothèse supplémentaire: Non applicable

### Kasongo

- Type détecté: Territoire
- Province: Maniema
- Zone FDSU: ET
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Maniema -> Territoires -> Kasongo
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Kasongo", "TYPE": "Territoire", "CODE_INS": "6325", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "16640.595526", "ORIGINE": "Numerisation Saint Moulin / Image satellite"}, "description_values": {"zone": "ET Province : 17 Territoire : 004"}, "description_html": "Zone : ET\nProvince : 17\nTerritoire : 004"}
- Hypothèse supplémentaire: Non applicable

### Kailo

- Type détecté: Territoire
- Province: Maniema
- Zone FDSU: ET
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Maniema -> Territoires -> Kailo
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Kailo", "TYPE": "Territoire", "CODE_INS": "6326", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "22992.990152", "ORIGINE": "Numerisation Saint Moulin / Image satellite"}, "description_values": {"zone": "ET Province : 17 Territoire : 003"}, "description_html": "Zone : ET\nProvince : 17\nTerritoire : 003"}
- Hypothèse supplémentaire: Non applicable

### Punia

- Type détecté: Territoire
- Province: Maniema
- Zone FDSU: ET
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Maniema -> Territoires -> Punia
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Territoire'. Type détecté pour audit = 'Territoire'.
- Attributs disponibles: {"extended_data": {"NOM": "Punia", "TYPE": "Territoire", "CODE_INS": "6327", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "16397.490059", "ORIGINE": "Numerisation Saint Moulin / Image satellite"}, "description_values": {"zone": "ET Province : 17 Territoire : 008"}, "description_html": "Zone : ET\nProvince : 17\nTerritoire : 008"}
- Hypothèse supplémentaire: Non applicable

### Kananga

- Type détecté: Commune
- Province: Kasai Central
- Zone FDSU: CE
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Kasai Central -> Territoires -> Kananga
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Communes'. Type détecté pour audit = 'Commune'.
- Attributs disponibles: {"extended_data": {"NOM": "Kananga", "TYPE": "Communes", "CODE_INS": "9010", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "763.924327", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "CE Province : 08 Territoire : 001"}, "description_html": "Zone : CE\nProvince : 08\nTerritoire : 001"}
- Hypothèse supplémentaire: Ville

### Mbuji-Mayi

- Type détecté: Commune
- Province: Kasai Oriental
- Zone FDSU: CE
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Kasai Oriental -> Territoires -> Mbuji-Mayi
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Communes'. Type détecté pour audit = 'Commune'.
- Attributs disponibles: {"extended_data": {"NOM": "Mbuji-Mayi", "TYPE": "Communes", "CODE_INS": "8010", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "139.045212", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "CE Province : 09 Territoire : 001"}, "description_html": "Zone : CE\nProvince : 09\nTerritoire : 001"}
- Hypothèse supplémentaire: Ville

### Mwene Ditu

- Type détecté: Commune
- Province: Lomami
- Zone FDSU: CE
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE CENTRE -> Provinces -> Lomami -> Territoires -> Mwene Ditu
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Communes'. Type détecté pour audit = 'Commune'.
- Attributs disponibles: {"extended_data": {"NOM": "Mwene Ditu", "TYPE": "Communes", "CODE_INS": "8050", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "149.987548", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "CE Province : 14 Territoire : 002"}, "description_html": "Zone : CE\nProvince : 14\nTerritoire : 002"}
- Hypothèse supplémentaire: Ville

### Likasi

- Type détecté: Commune
- Province: Haut-Katanga
- Zone FDSU: SD
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE SUD -> Provinces -> Haut-Katanga -> Territoires -> Likasi
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Communes'. Type détecté pour audit = 'Commune'.
- Attributs disponibles: {"extended_data": {"NOM": "Likasi", "TYPE": "Communes", "CODE_INS": "7020", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "279.6408", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "SD Province : 03 Territoire : 009"}, "description_html": "Zone : SD\nProvince : 03\nTerritoire : 009"}
- Hypothèse supplémentaire: Ville

### Lubumbashi

- Type détecté: Commune
- Province: Haut-Katanga
- Zone FDSU: SD
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE SUD -> Provinces -> Haut-Katanga -> Territoires -> Lubumbashi
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Communes'. Type détecté pour audit = 'Commune'.
- Attributs disponibles: {"extended_data": {"NOM": "Lubumbashi", "TYPE": "Communes", "CODE_INS": "7010", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "856.78134", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "SD Province : 03 Territoire : 001"}, "description_html": "Zone : SD\nProvince : 03\nTerritoire : 001"}
- Hypothèse supplémentaire: Ville

### Kolwezi

- Type détecté: Commune
- Province: Lualaba
- Zone FDSU: SD
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE SUD -> Provinces -> Lualaba -> Territoires -> Kolwezi
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Communes'. Type détecté pour audit = 'Commune'.
- Attributs disponibles: {"extended_data": {"NOM": "Kolwezi", "TYPE": "Communes", "CODE_INS": "7030", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "119.04601", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "SD Province : 15 Territoire : 001"}, "description_html": "Zone : SD\nProvince : 15\nTerritoire : 001"}
- Hypothèse supplémentaire: Ville

### Butembo

- Type détecté: Commune
- Province: Nord-Kivu
- Zone FDSU: ET
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Nord-Kivu -> Territoires -> Butembo
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Communes'. Type détecté pour audit = 'Commune'.
- Attributs disponibles: {"extended_data": {"NOM": "Butembo", "TYPE": "Communes", "CODE_INS": "6140", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "207.91688", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "ET Province : 19 Territoire : 009"}, "description_html": "Zone : ET\nProvince : 19\nTerritoire : 009"}
- Hypothèse supplémentaire: Ville

### Beni

- Type détecté: Commune
- Province: Nord-Kivu
- Zone FDSU: ET
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Nord-Kivu -> Territoires -> Beni
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Communes'. Type détecté pour audit = 'Commune'.
- Attributs disponibles: {"extended_data": {"NOM": "Beni", "TYPE": "Communes", "CODE_INS": "6130", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "360.567961", "ORIGINE": "Numerisation Saint Moulin"}, "description_values": {"zone": "ET Province : 19 Territoire : 007"}, "description_html": "Zone : ET\nProvince : 19\nTerritoire : 007"}
- Hypothèse supplémentaire: Ville

### Goma

- Type détecté: Commune
- Province: Nord-Kivu
- Zone FDSU: ET
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Nord-Kivu -> Territoires -> Goma
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Communes'. Type détecté pour audit = 'Commune'.
- Attributs disponibles: {"extended_data": {"NOM": "Goma", "TYPE": "Communes", "CODE_INS": "6110", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "45.446617", "ORIGINE": "Numerisation Saint Moulin / Image satellite"}, "description_values": {"zone": "ET Province : 19 Territoire : 001"}, "description_html": "Zone : ET\nProvince : 19\nTerritoire : 001"}
- Hypothèse supplémentaire: Ville

### Bukavu

- Type détecté: Commune
- Province: Sud-Kivu
- Zone FDSU: ET
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Sud-Kivu -> Territoires -> Bukavu
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Communes'. Type détecté pour audit = 'Commune'.
- Attributs disponibles: {"extended_data": {"NOM": "Bukavu", "TYPE": "Communes", "CODE_INS": "6210", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "57.978572", "ORIGINE": "Numerisation Saint Moulin / Image satellite"}, "description_values": {"zone": "ET Province : 22 Territoire : 001"}, "description_html": "Zone : ET\nProvince : 22\nTerritoire : 001"}
- Hypothèse supplémentaire: Ville

### Kindu

- Type détecté: Commune
- Province: Maniema
- Zone FDSU: ET
- Chemin complet KMZ: ZONES.kmz -> ZONES -> ZONE EST -> Provinces -> Maniema -> Territoires -> Kindu
- Dossier parent: Territoires
- Géométrie: Polygon
- Pourquoi cette entité a été classée comme territoire: Entité captée car le placemark est rangé sous le dossier parent 'Territoires' dans la branche Zone -> Province -> Territoires. TYPE attributaire = 'Communes'. Type détecté pour audit = 'Commune'.
- Attributs disponibles: {"extended_data": {"NOM": "Kindu", "TYPE": "Communes", "CODE_INS": "6310", "SCE_SEM": "INS", "SCE_GEO": "UNDP", "MODIF": "Fri Jun 18 2010 00:00:00 GMT+0100 (heure normale d’Afrique de l’Ouest)", "SURFACE": "142.689332", "ORIGINE": "Numerisation Saint Moulin / Image satellite"}, "description_values": {"zone": "ET Province : 17 Territoire : 001"}, "description_html": "Zone : ET\nProvince : 17\nTerritoire : 001"}
- Hypothèse supplémentaire: Ville
