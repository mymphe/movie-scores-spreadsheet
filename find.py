from main import get_api_key, get_info
from urllib.parse import urlencode
import requests
import enquiries


def main():
    api_key = get_api_key()
    title = input("Enter title: ")
    search_endpoint = "https://api.themoviedb.org/3/search/multi"
    search_query = urlencode({
        'api_key': api_key,
        'include_adult': False,
        'page': 1,
        'query': title,
    })

    search_url = f'{search_endpoint}?{search_query}'
    search_response = requests.get(search_url)
    search_result = search_response.json()

    matches = search_result.get('results')
    titles = [
        f"{m.get('title') or m.get('name')}, {m.get('release_date') or m.get('first_air_date') or '????'}, {m.get('media_type')}"
        for m in matches
    ]

    selected = enquiries.choose("Pick a movie", titles)
    title_index = titles.index(selected)

    # get the themoviedb id of the movie
    id = matches[title_index].get('id')
    category = matches[title_index].get('media_type')

    info = get_info(id, category, api_key)

    print(info)


if __name__ == "__main__":
    main()
