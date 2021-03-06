import gspread
from dotenv import load_dotenv
import os
from urllib.parse import urlencode
import requests
import sys
import enquiries
from datetime import date, timedelta


def main():

    api_key = get_api_key()

    (id, category) = search_by_title(api_key)

    info = get_info(id, category, api_key)

    update_spreadsheet(info)


def get_api_key():
    # load api key from .env
    load_dotenv()
    api_key = os.environ['THEMOVIEDB_API_KEY']
    return api_key


def search_by_title(api_key):
    search_endpoint = "https://api.themoviedb.org/3/search/multi"

    # prompt loop
    while True:
        search_term = input("Search for: ")

        id = None
        category = None

        page = 1
        # result pages loop
        while True:
            # construct url for search
            search_query = urlencode({
                'api_key': api_key,
                'include_adult': False,
                'page': page,
                'query': search_term,
            })

            search_url = f'{search_endpoint}?{search_query}'

            print(f"Searching for titles containing '{search_term}' ...")

            search_response = requests.get(search_url)

            # check if the response is ok
            if search_response.status_code != 200:
                sys.exit('Request to themoviedb failed')

            search_result = search_response.json()

            matches = search_result.get('results')

            # go back to search prompt if nothing's found
            if len(matches) == 0:
                print("Found no matches. Try again...")
                break

            total_pages = search_result.get('total_pages')

            # extract titles and release dates
            titles = [
                f"{m.get('title') or m.get('name')}, {m.get('release_date') or m.get('first_air_date') or '????'}, {m.get('media_type')}"
                for m in matches
            ]

            # add option to either navigate to the next page or start over
            NEXT_PAGE = '[next page]'
            START_OVER = '[start over]'
            titles.append(NEXT_PAGE if page < total_pages else START_OVER)

            # prompt user to pick match
            selected = enquiries.choose(f"Page {page} of {total_pages}",
                                        titles)

            # go to next page
            if selected == NEXT_PAGE:
                page += 1
                continue

            # go to search prompt
            if selected == START_OVER:
                break

            title_index = titles.index(selected)

            # get the themoviedb id of the movie
            id = matches[title_index].get('id')
            category = matches[title_index].get('media_type')
            break

        if id and category:
            break

    return (id, category)


def get_info(id, category, api_key):
    print("-" * 40)
    print("Searching info about selected title...")

    id_endpoint = f'https://api.themoviedb.org/3/{category}/'
    id_query = urlencode({"api_key": api_key, 'append_to_response': 'credits'})

    id_url = f"{id_endpoint}{id}?{id_query}"
    id_response = requests.get(id_url)

    # check if the response is ok
    if id_response.status_code != 200:
        sys.exit('Request to themoviedb failed. Exiting program')

    info = id_response.json()

    title = info.get('title') or info.get('name')

    # director for movie or executive producers for tv show
    creators = ', '.join([
        member.get('name') for member in info.get('credits').get('crew')
        if member.get('job') == 'Director' and category == 'movie'
        or member.get('job') == 'Executive Producer' and category == 'tv'
    ])

    # release date for movie, first and last episode air dates for tv
    dates = info.get('release_date') or '???'.join(
        [info.get('first_air_date'),
         info.get('last_air_date')])

    print('Found something!')

    print(f"Title: {title}")
    print(f"Creators: {creators}")
    print(f"Dates: {dates}")

    return (title, creators, dates, id)


def update_spreadsheet(info):
    print("-" * 40)
    # connect google service account, sourced from ~/.config/gspread/service_account.json
    gc = gspread.service_account()

    print('Searching for this title in your spreadsheet...')

    # open spreadsheet by name
    sh = gc.open("watched")

    sheet = sh.sheet1

    id_with_prefix = f"id-{info[3]}"
    # check if it exists in the table
    id_cell = sheet.find(id_with_prefix)

    AYA = 'aya'
    AZAT = 'azat'
    viewers = [AYA, AZAT]

    SKIP = '[skip]'
    scores = [SKIP, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0]

    if id_cell:
        print('Found in your spreadsheet')
        found_row = sheet.row_values(id_cell.row)

        print(f"Title: {found_row[0]}")
        print(f"Creators: {found_row[1]}")
        print(f"Dates: {found_row[2]}")
        print(f"Aya: {found_row[4]}, {found_row[5]}, {found_row[6]}")
        print(f"Azat: {found_row[7]}, {found_row[8]}, {found_row[9]}")

        # update scores
        for viewer in viewers:
            updated = []
            score = enquiries.choose(f'{viewer}: score', scores)

            if score == SKIP:
                continue
            else:
                updated.append(score)

                is_fav = enquiries.confirm(f"{viewer}: flag as favorite?")

                updated.append(is_fav)

                TODAY = 'Today'
                YESTERDAY = 'Yesterday'
                ENTER_DATE = 'Enter date'

                dates = [TODAY, YESTERDAY, ENTER_DATE]
                date_watched = enquiries.choose(f"{viewer}: date watched",
                                                dates)

                DATE_FORMAT = '%d.%m.%Y'
                if date_watched == TODAY:
                    updated.append(date.today().strftime(DATE_FORMAT))
                elif date_watched == YESTERDAY:
                    updated.append((date.today() -
                                    timedelta(days=1)).strftime(DATE_FORMAT))
                else:
                    custom_date = input('Please enter date (d.m.y): ')
                    updated.append(custom_date)

            print(updated)

            col_start = 5 if viewer == AYA else 8

            for i in range(3):
                col = col_start + i
                sheet.update_cell(id_cell.row, col, updated[i])
    else:
        print("Nothing found in your spreadsheet")
        new_row = [info[0], info[1], info[2], f'id-{info[3]}']

        for viewer in viewers:
            score = enquiries.choose(f'{viewer}: score', scores)

            if score == SKIP:
                new_row.append('???')
                new_row.append('???')
                new_row.append('???')
            else:
                new_row.append(score)

                is_fav = enquiries.confirm(f"{viewer}: flag as favorite?")

                new_row.append(is_fav)

                TODAY = 'Today'
                YESTERDAY = 'Yesterday'
                ENTER_DATE = 'Enter date'

                dates = [TODAY, YESTERDAY, ENTER_DATE]
                date_watched = enquiries.choose(f"{viewer}: date watched",
                                                dates)

                DATE_FORMAT = '%m/%d/%Y'
                if date_watched == TODAY:
                    new_row.append(date.today().strftime(DATE_FORMAT))
                elif date_watched == YESTERDAY:
                    new_row.append((date.today() -
                                    timedelta(days=1)).strftime(DATE_FORMAT))
                else:
                    custom_date = input('Please enter date (m/d/y): ')
                    new_row.append(custom_date)

        print(new_row)

        sheet.append_row(new_row)


if __name__ == "__main__":
    main()
