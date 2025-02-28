import json


def main():
    # Load data from the JSON file
    with open("song_rankings.json", "r") as f:
        data = json.load(f)

    # Sort the songs by rating in descending order
    sorted_files = sorted(data.items(), key=lambda item: item[1]["rating"], reverse=True)

    # Display the songs with ranking, country name, and rating (rounded to 1 decimal)
    for rank, (filename, details) in enumerate(sorted_files, start=1):
        country = filename.split('_')[0]
        rating = round(details["rating"], 1)
        print(f"{rank}. {country} - {rating}")


if __name__ == "__main__":
    main()
