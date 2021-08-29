import gspread

def main():
    print('main')

    # connect google service account, sourced from ~/.config/gspread/service_account.json
    gc = gspread.service_account()

    # open spreadsheet by name
    sh = gc.open("movie_ratings")

    print(sh.sheet1.get('A1'))


if __name__ == "__main__":
    main()
