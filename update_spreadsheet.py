import argparse
import gspread
import json
import sys
from oauth2client.service_account import ServiceAccountCredentials


def get_sheet(credentials):
    api = gspread.authorize(credentials)
    return api.open('Abstractions.io Conference Schedule').get_worksheet(0)


def read_credentials(file_name):
    return ServiceAccountCredentials.from_json_keyfile_name(
        file_name,
        ['https://spreadsheets.google.com/feeds']
    )


def parse_args():
    description = 'Update the Abstractions.io schedule Google Sheet.'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        'credentials',
        help='Path to the JSON file containing the Google Sheets '
             'service account credentials'
    )
    parser.add_argument('schedule', help='Path to the JSON file')
    return parser.parse_args()


def clear_sheet(sheet):
    cell_list = [sheet.cell(row, column)
                 for row in range(1, sheet.row_count + 1)
                 for column in range(1, sheet.col_count + 1)]
    for cell in cell_list:
        cell.value = ''
    sheet.update_cells(cell_list)


def add_sheet_headers(sheet):
    headers = ['Start Date', 'End date', 'Title',
               '', '', '', '', '', '', 'Location',
               'Speaker', 'Speaker Image URL', 'Description']
    cell_list = [sheet.cell(1, column)
                 for column in range(1, len(headers) + 1)]
    for cell, name in zip(cell_list, headers):
        cell.value = name
    sheet.update_cells(cell_list)


def update_sheet(sheet, schedule):
    add_sheet_headers(sheet)


def main():
    args = parse_args()
    with open(args.schedule) as f:
        schedule = json.load(f)
    credentials = read_credentials(args.credentials)
    sheet = get_sheet(credentials)
    clear_sheet(sheet)
    update_sheet(sheet, schedule)

    return 0


if __name__ == "__main__":
    status = main()
    sys.exit(status)


