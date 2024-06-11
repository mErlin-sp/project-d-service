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


def int_to_excel_col(num):
    """Convert a positive integer to its corresponding Excel column letter."""
    if num < 1:
        raise ValueError("Column number must be 1 or greater.")

    result = ""
    while num > 0:
        num -= 1
        result = chr(num % 26 + 65) + result
        num //= 26

    return result


# Function to convert datetime to Excel serial date number
def datetime_to_excel(date_time):
    temp = datetime(1899, 12, 30)  # Excels base date is 1899-12-30
    delta = date_time - temp
    return float(delta.days) + (float(delta.seconds) / 86400)


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
            goods_worksheet = workbook.add_worksheet('Goods')

            # Add a bold format to use to highlight cells.
            bold = workbook.add_format({'bold': True})

            # Add an Excel date format.
            date_format = workbook.add_format({'num_format': 'mmmm d yyyy hh:mm:ss'})  # '%Y-%m-%d %H:%M:%S'

            # Define a format with center alignment
            center_align_format = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'bold': True})

            row = 0
            col = 0

            goods_worksheet.write_row(row, col,
                                      ['id', 'platform', 'platform_id', 'query_id', 'name', 'href', 'img_href', 'brand',
                                       'created_at', 'last_updated', 'last_confirmed'], bold)

            # Adjust the columns' width.
            goods_worksheet.set_column(col, col, 10)  # id
            goods_worksheet.set_column(col + 1, col + 1, 10)  # platform
            goods_worksheet.set_column(col + 2, col + 2, 15)  # platform_id
            goods_worksheet.set_column(col + 3, col + 3, 15)  # query_id
            goods_worksheet.set_column(col + 4, col + 4, 100)  # name
            goods_worksheet.set_column(col + 5, col + 5, 30)  # href
            goods_worksheet.set_column(col + 6, col + 6, 30)  # img_href
            goods_worksheet.set_column(col + 7, col + 7, 20)  # brand
            goods_worksheet.set_column(col + 8, col + 8, 30)  # created_at
            goods_worksheet.set_column(col + 9, col + 9, 30)  # last_updated
            goods_worksheet.set_column(col + 10, col + 10, 30)  # ` last_confirmed

            row += 1
            for good in goods:
                goods_worksheet.write_row(row, col, good[:-3])
                goods_worksheet.write_datetime(row, col + 8,
                                               good[-3] if isinstance(good[-3], datetime) else datetime.strptime(
                                                   good[-3],
                                                   '%Y-%m-%d '
                                                   '%H:%M:%S'),
                                               date_format)
                goods_worksheet.write_datetime(row, col + 9,
                                               good[-2] if isinstance(good[-2], datetime) else datetime.strptime(
                                                   good[-2],
                                                   '%Y-%m-%d '
                                                   '%H:%M:%S'),
                                               date_format)
                goods_worksheet.write_datetime(row, col + 10,
                                               good[-1] if isinstance(good[-1], datetime) else datetime.strptime(
                                                   good[-1],
                                                   '%Y-%m-%d '
                                                   '%H:%M:%S'),
                                               date_format)
                row += 1

            # Set the auto filter.
            goods_worksheet.autofilter(0, 0, row - 1, 10)

            # Create a new worksheet for prices.
            prices_worksheet = workbook.add_worksheet('Prices')

            prices_worksheet.set_column(0, 0, 15)  # first column
            prices_worksheet.set_column(1, 100, 30)  # price and created_at columns

            row = 0
            for good in goods[:1000]:
                prices = db.get_prices(good[0])
                if prices:
                    print(f'Price. Good ID: {good[0]}')
                    prices_worksheet.merge_range(row, 0, row, 5, f'Good ID: {good[0]}', center_align_format)
                    prices_worksheet.set_row(row, 30)

                    # Add prices table
                    prices_worksheet.write(row + 1, 0, 'price', bold)
                    prices_worksheet.write(row + 2, 0, 'created_at', bold)
                    for x, price in enumerate(prices):
                        prices_worksheet.write(row + 1, x + 1, price[0])
                        price_date = price[1] if isinstance(price[1], datetime) else datetime.strptime(price[1],
                                                                                                       '%Y-%m-%d ' '%H:%M:%S')
                        prices_worksheet.write(row + 2, x + 1, price_date)
                        prices_worksheet.write_datetime(row + 3, x + 1, price_date, date_format)

                    # Create price chart
                    price_chart = workbook.add_chart({'type': 'line'})
                    price_chart.add_series({
                        # 'categories': f'=Prices!$B${row + 2}:${int_to_excel_col(x)}${row + 2}',
                        'categories': f'=Prices!$B${row + 2 + 1}:${int_to_excel_col(x + 1 + 1)}${row + 2 + 1}',
                        'values': f'=Prices!$B${row + 1 + 1}:${int_to_excel_col(x + 1 + 1)}${row + 1 + 1}',
                        'line': {'color': 'blue'},
                    })
                    price_chart.set_title({'name': 'Prices'})
                    price_chart.set_x_axis({'name': 'Date', 'date_axis': True, 'num_format': 'dd/mm/yy hh:mm:ss',
                                            'major_gridlines': {'visible': True}})
                    price_chart.set_y_axis({'name': 'Price'})
                    price_chart.set_size({'width': 720, 'height': 576})
                    prices_worksheet.insert_chart(f'B{row + 7}', price_chart)

                    row += 40

            # Create a new worksheet for in-stock.
            in_stock_worksheet = workbook.add_worksheet('Stock')

            in_stock_worksheet.set_column(0, 0, 15)  # first column
            in_stock_worksheet.set_column(1, 100, 30)  # in_stock and created_at columns

            row = 0
            for good in goods[:1000]:
                in_stock = db.get_in_stock(good[0])
                if in_stock:
                    print(f'In Stock. Good ID: {good[0]}')
                    in_stock_worksheet.merge_range(row, 0, row, 5, f'Good ID: {good[0]}', center_align_format)
                    in_stock_worksheet.set_row(row, 30)

                    # Add in-stock table
                    in_stock_worksheet.write(row + 1, 0, 'in_stock', bold)
                    in_stock_worksheet.write(row + 2, 0, 'created_at', bold)
                    for x, stock in enumerate(in_stock):
                        in_stock_worksheet.write(row + 1, x + 1, stock[0])
                        stock_date = stock[1] if isinstance(stock[1], datetime) else datetime.strptime(stock[1],
                                                                                                       '%Y-%m-%d ' '%H:%M:%S')
                        in_stock_worksheet.write(row + 2, x + 1, stock_date)
                        in_stock_worksheet.write_datetime(row + 3, x + 1, stock_date, date_format)

                    # Create in-stock chart
                    in_stock_chart = workbook.add_chart({'type': 'line'})
                    in_stock_chart.add_series({
                        # 'categories': f'=In Stock!$B${row + 2}:${int_to_excel_col(x)}${row + 2}',
                        'categories': f'=Stock!$B${row + 2 + 1}:${int_to_excel_col(x + 1 + 1)}${row + 2 + 1}',
                        'values': f'=Stock!$B${row + 1 + 1}:${int_to_excel_col(x + 1 + 1)}${row + 1 + 1}',
                        'line': {'color': 'green'},
                    })
                    in_stock_chart.set_title({'name': 'In Stock'})
                    in_stock_chart.set_x_axis({'name': 'Date', 'date_axis': True, 'num_format': 'dd/mm/yy hh:mm:ss',
                                               'major_gridlines': {'visible': True}})
                    in_stock_chart.set_y_axis({'name': 'In Stock'})
                    in_stock_chart.set_size({'width': 720 * 1.5, 'height': 576})
                    in_stock_worksheet.insert_chart(f'B{row + 7}', in_stock_chart)

                    row += 40


    except Exception as e:
        print('Export to XLSX error:', e)
        return None
    else:
        print('Export to XLSX successful')
        return os.path.join(file_path, file_name)
