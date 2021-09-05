from main import get_api_key
import gspread
from urllib.parse import urlencode
import requests
import enquiries
from datetime import datetime

EM_DASH = '—'


def main():
    api_key = get_api_key()
    search_endpoint = "https://api.themoviedb.org/3/search/multi"

    gc = gspread.service_account()

    # open spreadsheet by name
    old = gc.open("movie_ratings")

    old_sheet = old.sheet1

    new = gc.open('watched')
    new_sheet = new.sheet1

    failed_rows = []

    # for i in range(101, 102):
    for i in range(3, 1120):
        print('------------------------------------------')
        print(f'ROW {i}')

        row = old_sheet.row_values(i)
        search_title = row[0].replace(", The", "")

        new_row = []

        none = '—'

        try:

            print(search_title)

            search_query = urlencode({
                'api_key': api_key,
                'include_adult': False,
                'page': 1,
                'query': search_title,
            })

            search_url = f'{search_endpoint}?{search_query}'
            search_response = requests.get(search_url)
            search_result = search_response.json()

            matches = search_result.get('results')

            homogenous_matches = [homogenize(m) for m in matches]

            found = find_target(homogenous_matches, row[1])

            id = found[3]
            print(id)
            category = found[2]

            id_endpoint = f'https://api.themoviedb.org/3/{category}/'
            id_query = urlencode({
                "api_key": api_key,
                'append_to_response': 'credits'
            })

            id_url = f"{id_endpoint}{id}?{id_query}"
            id_response = requests.get(id_url)

            info = id_response.json()

            title = info.get('title') or info.get('name')

            # director for movie or executive producers for tv show
            creators = ', '.join([
                member.get('name')
                for member in info.get('credits').get('crew')
                if member.get('job') == 'Director' and category == 'movie' or
                member.get('job') == 'Executive Producer' and category == 'tv'
            ])

            movie_year = info.get('release_date')[0:4] if info.get(
                'release_date') else '????'
            tv_start = info.get('first_air_date')[0:4] if info.get(
                'first_air_date') else '????'
            tv_end = info.get('last_air_date')[0:4] if info.get(
                'last_air_date') else '????'

            # release date for movie, first and last episode air dates for tv
            years = movie_year if category == 'movie' else none.join(
                [tv_start, tv_end])

            print('About this movie')

            print(f"Title: {title}")
            print(f"Creators: {creators}")
            print(f"Years: {years}")

            new_row.append(title)
            new_row.append(creators)
            new_row.append(years)
            new_row.append(f'id-{id}')
        except BaseException as e:
            print(e)
            new_row.append(search_title)
            new_row.append(row[2])
            new_row.append(row[1])
            new_row.append('id-')

            failed_rows.append(i)

        try:

            yes_no = {'Yes': True, 'No': False}

            aya_score = set_score(row, 3)
            aya_fav = yes_no.get(safe_list_get(row, 4)) if type(
                yes_no.get(safe_list_get(row, 4))) == type(True) else none
            aya_date = parse_date(row[5]) if safe_list_get(row, 5) else none

            az_score = int(safe_list_get(row, 6)) if safe_list_get(row,
                                                                   6) else none
            az_fav = yes_no.get(safe_list_get(row, 7)) if type(
                yes_no.get(safe_list_get(row, 7))) == type(True) else none
            az_date = parse_date(row[8]) if safe_list_get(row, 8) else none

            id_format = f'id-{id}'
            # new_row = [title, creators, dates, id_format] + [
            #     aya_score, aya_fav, aya_date, az_score, az_fav, az_date
            # ]
            new_row.append(aya_score)
            new_row.append(aya_fav)
            new_row.append(aya_date)
            new_row.append(az_score)
            new_row.append(az_fav)
            new_row.append(az_date)
        except:
            new_row.append('XXX')
            new_row.append('XXX')
            new_row.append('XXX')
            new_row.append('XXX')
            new_row.append('XXX')
            new_row.append('XXX')

        new_sheet.append_row(new_row, value_input_option='USER_ENTERED')

    print('-' * 40)
    print('Failed rows')
    print(failed_rows)


def safe_list_get(list, index):
    try:
        return list[index]
    except IndexError:
        return None


def get_agnostic_title(movie_or_tv):
    return movie_or_tv.get('title') or movie_or_tv.get('name')


def get_agnostic_release_year(movie_or_tv):
    release_year = movie_or_tv.get('release_date') or movie_or_tv.get(
        'first_air_date') or '????'
    return release_year[0:4]


def get_media_type(movie_or_tv):
    return movie_or_tv.get('media_type')


def get_id(movie_or_tv):
    return movie_or_tv.get('id')


def homogenize(movie_or_tv):
    title = get_agnostic_title(movie_or_tv)
    release_year = get_agnostic_release_year(movie_or_tv)
    media_type = get_media_type(movie_or_tv)
    id = get_id(movie_or_tv)
    return (title, release_year, media_type, id)


def approx_year(year1, year2):
    if year1 == '????':
        return False

    year1 = int(year1)
    year2 = int(year2[0:4])
    return year1 == year2 or year1 + 1 == year2 or year1 - 1 == year2 or year1 + 2 == year2 or year1 - 2 == year2


def find_target(matches, target_year):
    filtered = list(
        filter(lambda m: approx_year(m[1], target_year) and m[2] != 'person',
               matches))
    return filtered[0]


def set_score(row, id):
    return safe_list_get(row, id) or EM_DASH


def parse_date(date):
    if '.' in date:
        return date
    else:
        return datetime.strptime(date, '%m/%d/%Y').strftime('%d.%m.%Y')


if __name__ == "__main__":
    main()
