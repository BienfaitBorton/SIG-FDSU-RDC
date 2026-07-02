from app.fdsu_structure_importer import FDSUStructureImporter
from pathlib import Path
import pandas as pd

importer = FDSUStructureImporter(username='system')
path = Path('data/imports/referentiel/FDSU Structure.xlsx')
xls = pd.read_excel(path, sheet_name=None, engine='openpyxl', header=None, dtype=object)
sheets = importer._sheet_map(xls)
out = []

for normalized_sheet, sheet in sheets.items():
    df, mapping, missing_columns = importer._detect_header(xls[sheet])
    current_prov_code = None
    for idx, row in df.iterrows():
        province_name = importer._text(row.get(mapping['province_name']))
        province_code = importer._code(row.get(mapping['province_code']), 2)
        territoire_name = importer._text(row.get(mapping['territoire_name']))
        territoire_code = importer._code(row.get(mapping['territoire_code']), 3)

        if not province_code and not province_name and not territoire_code and not territoire_name:
            continue
        if province_code in importer.SHEET_ZONES and not province_name and not territoire_code and not territoire_name:
            continue

        is_province_row = bool(province_code and province_name)
        prov_code = province_code if is_province_row else current_prov_code
        terr_code = territoire_code

        if not prov_code:
            continue

        if not terr_code or not territoire_name:
            if not is_province_row:
                row_values = [None if pd.isna(v) else v for v in row.tolist()]
                out.append({'sheet': sheet, 'line': int(idx) + 1, 'row_values': row_values})
                continue

        current_prov_code = prov_code

print('count=', len(out))
for item in out:
    print('SHEET=', item['sheet'])
    print('LINE=', item['line'])
    print('ROW=', item['row_values'])
    print('---')
