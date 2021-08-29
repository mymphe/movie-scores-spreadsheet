import gspread

def main():
    print('main')

    gc = gspread.service_account()
    sh = gc.open("movie_ratings")

    print(sh.sheet1.get('A1'))


if __name__ == "__main__":
    main()
