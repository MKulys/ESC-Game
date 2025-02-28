# Song Ranker

A very raw and unfinished Python application that helps you discover your favorite songs through pairwise comparisons and keeps track of your listening habits.

## Overview

Song Ranker is an interactive tool that lets you rank your music collection by comparing songs in pairs. Using a sophisticated TrueSkill-inspired ranking algorithm, the application gradually builds a reliable ranking of your preferences while also tracking listening statistics.

## Features

- **Pairwise Comparison**: Compare two songs at a time to gradually build a reliable ranking
- **Adaptive Selection**: Smart selection of song pairs that maximizes information gain
- **Confidence Rating**: Tracks uncertainty in rankings and prioritizes comparisons that will improve ranking confidence
- **Listening Statistics**: Records play count, average listen time, and total listen time for each song
- **Interactive UI**: Simple and intuitive interface with playback controls
- **Rating History**: Keeps a record of all comparisons for future analysis

## Getting Started

### Prerequisites

- Python 3.6+
- PyGame library

### Installation

1. Clone the repository or download the source code
2. Install the required dependencies:

```
pip install pygame
```

3. Create a folder named `recordings` in the application directory 
4. Add your music files to the `recordings` folder (supported formats: .mp3, .wav, .ogg, .flac)

### File Naming Convention (Optional)

For better organization, you can name your files following this pattern:
```
Country_Artist_SongName.mp3
```

Example: `USA_TheWeeknd_AfterHours.mp3`

## Usage

Run the application:

```
python main.py
```

### Main Menu Options:

- **Compare Songs**: Start comparing songs to build your ranking
- **View Rankings**: See your current song rankings with confidence levels
- **View Listening Statistics**: Check play counts and listening times
- **View Ranking Confidence**: See overall ranking reliability and suggestions for improvement
- **Refresh Song List**: Update the application if you've added new songs
- **Exit**: Close the application

### During Playback:

- **Q**: Stop playback and return to the previous screen
- **Right Arrow/D**: Skip forward 5 seconds
- **Left Arrow/A**: Rewind 5 seconds

## How It Works

The application uses a modified Elo/TrueSkill rating system that not only updates song ratings after each comparison but also tracks the uncertainty of each rating. Songs with higher uncertainty are prioritized for future comparisons, ensuring that the ranking becomes more accurate over time.

## Data Files

The application creates and maintains several JSON files:

- **song_rankings.json**: Current ratings and uncertainty values for each song
- **listening_stats.json**: Play counts and durations for each song
- **comparison_history.json**: Record of all pairwise comparisons

These files are automatically loaded when the application starts and saved after each update.
