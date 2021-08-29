import gspread
from dotenv import load_dotenv
import os
from urllib.parse import urlencode
import requests
import sys
import enquiries


def main():
    # load api key from .env
    load_dotenv()
    api_key = os.environ['THEMOVIEDB_API_KEY']

    # search movies, tv
    search_endpoint = f"https://api.themoviedb.org/3/search/multi"

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

            print("Searching...")

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
                pass

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

    print("Searching info...")

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
    dates = info.get('release_date') or '—'.join(
        [info.get('first_air_date'),
         info.get('last_air_date')])

    print('About this movie')

    print(f"Title: {title}")
    print(f"Creators: {creators}")
    print(f"Dates: {dates}")

    # connect google service account, sourced from ~/.config/gspread/service_account.json
    # gc = gspread.service_account()

    # open spreadsheet by name
    # sh = gc.open("movie_ratings")

    # print(sh.sheet1.get('A1'))


if __name__ == "__main__":
    main()
