import csv
import os
from datetime import datetime

import xlsxwriter

from db import DB


def export_to_csv(db: DB, query: str = None, file_name: str = 'export.csv',
                  file_path: str = 'export/') -> str | None:
    print('Exporting to CSV...')

    if query:
        goods = db.execute_query(query)
    else:
        goods = db.get_goods()

    if not goods:
        print('No goods found')
        return None

    try:
        os.makedirs(file_path, exist_ok=True)
        with open(os.path.join(file_path, file_name), 'w', encoding='utf-8') as csv_file:
            csv_writer = csv.writer(csv_file)
            # Write column names
            csv_writer.writerow(
                ['id', 'platform', 'platform_id', 'query_id', 'name', 'href', 'img_href', 'brand', 'created_at',
                 'last_updated', 'last_confirmed'])
            # Write data rows
            csv_writer.writerows(goods)
    except Exception as e:
        print('Export to CSV error:', e)
        return None
    else:
        print('Export to CSV successful')
        return os.path.join(file_path, file_name)


def export_to_xlsx(db: DB, query: str = None, file_name: str = 'export.xlsx',
                   file_path: str = 'export/') -> str | None:
    print('Exporting to XLSX...')

    if query:
        goods = db.execute_query(query)
    else:
        goods = db.get_goods()

    if not goods:
        print('No goods found')
        return None

    try:
        os.makedirs(file_path, exist_ok=True)

        with xlsxwriter.Workbook(os.path.join(file_path, file_name), {'strings_to_urls': False}) as workbook:
            worksheet = workbook.add_worksheet('Goods')

            # Add a bold format to use to highlight cells.
            bold = workbook.add_format({'bold': True})

            # Add an Excel date format.
            date_format = workbook.add_format({'num_format': 'mmmm d yyyy hh:mm:ss'})  # '%Y-%m-%d %H:%M:%S'

            row = 0
            col = 0

            worksheet.write_row(row, col,
                                ['id', 'platform', 'platform_id', 'query_id', 'name', 'href', 'img_href', 'brand',
                                 'created_at', 'last_updated', 'last_confirmed'], bold)

            # Adjust the columns' width.
            worksheet.set_column(col, col, 10)  # id
            worksheet.set_column(col + 1, col + 1, 10)  # platform
            worksheet.set_column(col + 2, col + 2, 15)  # platform_id
            worksheet.set_column(col + 3, col + 3, 15)  # query_id
            worksheet.set_column(col + 4, col + 4, 100)  # name
            worksheet.set_column(col + 5, col + 5, 30)  # href
            worksheet.set_column(col + 6, col + 6, 30)  # img_href
            worksheet.set_column(col + 7, col + 7, 20)  # brand
            worksheet.set_column(col + 8, col + 8, 30)  # created_at
            worksheet.set_column(col + 9, col + 9, 30)  # last_updated
            worksheet.set_column(col + 10, col + 10, 30)  # ` last_confirmed

            row += 1
            for good in goods:
                worksheet.write_row(row, col, good[:-3])
                worksheet.write_datetime(row, col + 8,
                                         good[-3] if isinstance(good[-3], datetime) else datetime.strptime(good[-3],
                                                                                                           '%Y-%m-%d '
                                                                                                           '%H:%M:%S'),
                                         date_format)
                worksheet.write_datetime(row, col + 9,
                                         good[-2] if isinstance(good[-2], datetime) else datetime.strptime(good[-2],
                                                                                                           '%Y-%m-%d '
                                                                                                           '%H:%M:%S'),
                                         date_format)
                worksheet.write_datetime(row, col + 10,
                                         good[-1] if isinstance(good[-1], datetime) else datetime.strptime(good[-1],
                                                                                                           '%Y-%m-%d '
                                                                                                           '%H:%M:%S'),
                                         date_format)
                row += 1

            # Set the auto filter.
            worksheet.autofilter(0, 0, row - 1, 10)

    except Exception as e:
        print('Export to XLSX error:', e)
        return None
    else:
        print('Export to XLSX successful')
        return os.path.join(file_path, file_name)
