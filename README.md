# Song Ranker (Eurovision-specific repo)

A very raw and unfinished Python application that helps you discover your favorite songs through pairwise comparisons, keeps track of your listening habits, and tests your knowledge of song origins through a guessing game.

## Overview

Song Ranker is an interactive tool that lets you rank your music collection by comparing songs in pairs. Using a sophisticated TrueSkill-inspired ranking algorithm, the application gradually builds a reliable ranking of your preferences while also tracking listening statistics. The repository also includes a Song Guessing Game that challenges you to identify the country of origin for each song.

## Features

### Song Ranker
- **Pairwise Comparison**: Compare two songs at a time to gradually build a reliable ranking
- **Adaptive Selection**: Smart selection of song pairs that maximizes information gain
- **Confidence Rating**: Tracks uncertainty in rankings and prioritizes comparisons that will improve ranking confidence
- **Listening Statistics**: Records play count, average listen time, and total listen time for each song
- **Interactive UI**: Simple and intuitive interface with playback controls
- **Rating History**: Keeps a record of all comparisons for future analysis

### Song Guessing Game
- **Country Guessing**: Test your knowledge by guessing the country of origin for each song
- **Scoring System**: Earn points for correct guesses and track your performance across games
- **Playback Controls**: Skip forward or rewind songs during gameplay
- **Statistics Tracking**: View your best and worst guessed songs, overall performance, and more
- **Intuitive Interface**: Easy-to-use UI with visual feedback for correct and incorrect answers

## Getting Started

### Prerequisites

- Python 3.6+
- PyGame library

### Installation

1. Clone the repository or download the source code
2. Install the required dependencies:

```
pip install -r requirements.txt
```

3. Create a folder named `recordings` in the application directory 
4. Add your music files to the `recordings` folder (supported formats: .mp3, .wav, .ogg, .flac)
5. **IMPORTANT:** delete all JSON files when first initializing the app. These files contain personal rankings, uploaded for my progress saving purposes, but they do not reflect your personal choices. After deleting them, the app will automatically generate your personal statistics. Note: make sure to back up the progress before pulling new updates, as this might overwrite your statistics/create merge conflicts.

### File Naming Convention (Optional)

For better organization and to ensure proper formatting, you should name your files following this pattern:
```
Country_Artist_SongName.mp3
```

Example: `Canada_TheWeeknd_AfterHours.mp3`

## Usage

### Song Ranker

Run the application:

```
python main.py
```

#### Main Menu Options:

- **Compare Songs**: Start comparing songs to build your ranking
- **View Rankings**: See your current song rankings with confidence levels
- **View Listening Statistics**: Check play counts and listening times
- **View Ranking Confidence**: See overall ranking reliability and suggestions for improvement
- **Refresh Song List**: Update the application if you've added new songs
- **Exit**: Close the application

#### During Playback:

- **Q**: Stop playback and return to the previous screen
- **Right Arrow/D**: Skip forward 5 seconds
- **Left Arrow/A**: Rewind 5 seconds

### Song Guessing Game

Run the application:

```
python song_guessing.py
```

#### Main Menu Options:

- **Start Game**: Begin a new guessing game session
- **Statistics**: View your guessing performance and game statistics
- **Quit**: Exit the application

#### During Gameplay:

- **Right Arrow**: Skip forward 5 seconds
- **Left Arrow**: Rewind 5 seconds
- **Enter**: Submit your guess
- **Next Song/End Game**: Proceed to the next song or end the game

## How It Works

### Song Ranker
The application uses a modified Elo/TrueSkill rating system that not only updates song ratings after each comparison but also tracks the uncertainty of each rating. Songs with higher uncertainty are prioritized for future comparisons, ensuring that the ranking becomes more accurate over time.

### Song Guessing Game
The game randomly selects songs from your collection and challenges you to guess their country of origin. Each correct guess earns you a point, and the game tracks your performance across multiple play sessions to identify which songs you're best and worst at guessing.

## Data Files

The applications create and maintain several JSON files:

### Song Ranker
- **song_rankings.json**: Current ratings and uncertainty values for each song
- **listening_stats.json**: Play counts and durations for each song
- **comparison_history.json**: Record of all pairwise comparisons

### Song Guessing Game
- **song_guess_stats.json**: Correct guess rates and statistics for each song
- **game_stats.json**: Overall game performance statistics

These files are automatically loaded when the applications start and saved after each update.
