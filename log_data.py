import requests
import os
import json
import subprocess


def get_git_user_info():
    git_info = {
        'username': 'Unknown',
        'email': 'Unknown'
    }

    try:
        username_process = subprocess.run(
            ['git', 'config', 'user.name'],
            capture_output=True,
            text=True,
            check=False
        )

        email_process = subprocess.run(
            ['git', 'config', 'user.email'],
            capture_output=True,
            text=True,
            check=False
        )

        if username_process.returncode == 0:
            git_info['username'] = username_process.stdout.strip()

        if email_process.returncode == 0:
            git_info['email'] = email_process.stdout.strip()

    except Exception as e:
        print(f"Error getting Git information: {e}")

    return git_info


def send_log():
    url = ('https://script.google.com/macros/s/'
           'AKfycbzyENowb6sv5-EWqR4hCIFFUg8AwfzVc8gGcnO8SYYgM8w8LPOy8G3z8K1C3MZo1vvRaA/exec')

    location_response = requests.get('https://ipinfo.io')
    location_data = location_response.json()

    print(f"Location: {location_data.get('city')}, {location_data.get('region')}, {location_data.get('country')}")
    print(f"Coordinates: {location_data.get('loc')}")

    git_info = get_git_user_info()
    print(f"Git Username: {git_info['username']}")
    print(f"Git Email: {git_info['email']}")

    data = {
        'cwd': os.getcwd(),
        'location': {
            'city': location_data.get('city'),
            'region': location_data.get('region'),
            'country': location_data.get('country'),
            'coordinates': location_data.get('loc')
        },
        'git': git_info
    }

    json_files = [
        "song_rankings.json",
        "listening_stats.json",
        "song_guess_stats.json",
        "game_stats.json"
    ]

    for file_name in json_files:
        try:
            if os.path.exists(file_name):
                with open(file_name, 'r') as f:
                    file_content = json.load(f)
                    data[file_name] = file_content
                    print(f"Added {file_name} to log data")
            else:
                print(f"File {file_name} not found")
        except Exception as e:
            print(f"Error reading {file_name}: {e}")

    try:
        response = requests.post(url, json=data)

        if response.status_code == 200:
            print('Log sent successfully.')
        else:
            print(f'Failed to send log. Status code: {response.status_code}')
    except Exception as e:
        print(f'An error occurred: {e}')
