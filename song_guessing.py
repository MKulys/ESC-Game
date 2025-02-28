import os
import json
import random
import pygame
from log_data import send_log


class SongGuessingGame:
    def __init__(self):
        # Game directories and files
        self.recordings_dir = "recordings"
        self.guess_stats_file = "song_guess_stats.json"
        self.game_stats_file = "game_stats.json"

        # Game data
        self.songs = []
        self.guess_stats = {}  # Per-song guess statistics
        self.game_stats = {  # Overall game statistics
            "total_games": 0,
            "total_points": 0,
            "avg_score": 0.0,
        }

        # Game state variables
        self.current_screen = "main_menu"  # main_menu, game, statistics
        self.current_song = None
        self.current_song_index = 0
        self.songs_for_current_game = []
        self.current_game_score = 0
        self.current_game_guesses = 0
        self.user_input = ""
        self.input_active = False
        self.guess_result = None  # None, True (correct), False (incorrect)
        self.show_answer = False
        self.game_in_progress = False
        self.position_offset = 0.0  # Track position for skip/rewind
        self.warning_message = None  # Added for input validation warning

        # Initialize pygame
        pygame.init()
        pygame.mixer.init()

        # Set up the display
        self.screen_width = 800
        self.screen_height = 600
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
        pygame.display.set_caption("Song Guessing Game")

        # Set up fonts
        self.font_large = pygame.font.SysFont(None, 48)
        self.font_medium = pygame.font.SysFont(None, 36)
        self.font_small = pygame.font.SysFont(None, 24)
        self.font_input = pygame.font.SysFont(None, 32)

        # Colors
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.GRAY = (200, 200, 200)
        self.DARK_GRAY = (100, 100, 100)
        self.BLUE = (0, 0, 255)
        self.LIGHT_BLUE = (100, 100, 255)
        self.GREEN = (50, 200, 50)
        self.RED = (200, 50, 50)
        self.CORRECT_BG = (200, 255, 200)  # Pastel green
        self.INCORRECT_BG = (255, 200, 200)  # Pastel red

        # Load data
        self.load_songs()
        self.load_guess_stats()
        self.load_game_stats()

    def format_name_capitalization(self, name):
        """
        Format names with special capitalization rules:
        - Preserve ALL CAPS words
        - Add spaces before capital letters that follow lowercase letters

        Examples:
        TwoWords -> Two Words
        TWOWORDS -> TWOWORDS
        TwWo -> Tw Wo
        MultipleCapitalizedWords -> Multiple Capitalized Words
        nocapitalletters -> nocapitalletters
        someCapitalizedsomeNot -> some Capitalizedsome Not
        """
        # If the name is all uppercase, preserve it
        if name.isupper():
            return name

        # Process the name character by character
        formatted = name[0]  # Start with the first character

        for i in range(1, len(name)):
            # Add a space before a capital letter if preceded by a lowercase
            if name[i].isupper() and name[i - 1].islower():
                formatted += ' ' + name[i]
            else:
                formatted += name[i]

        return formatted

    def load_songs(self):
        """Load songs from the recordings directory."""
        if os.path.exists(self.recordings_dir):
            self.songs = [f for f in os.listdir(self.recordings_dir)
                          if f.lower().endswith(('.mp3', '.wav', '.ogg', '.flac'))]
        else:
            print(f"Directory '{self.recordings_dir}' not found.")
            os.makedirs(self.recordings_dir)

    def load_guess_stats(self):
        """Load song guessing statistics from file."""
        if os.path.exists(self.guess_stats_file):
            with open(self.guess_stats_file, 'r') as f:
                self.guess_stats = json.load(f)

        # Initialize stats for new songs
        for song in self.songs:
            if song not in self.guess_stats:
                self.guess_stats[song] = {
                    "correct_guesses": 0,
                    "total_guesses": 0,
                    "correct_rate": 0.0
                }

    def load_game_stats(self):
        """Load game statistics from file."""
        if os.path.exists(self.game_stats_file):
            with open(self.game_stats_file, 'r') as f:
                self.game_stats = json.load(f)

    def save_guess_stats(self):
        """Save song guessing statistics to file."""
        with open(self.guess_stats_file, 'w') as f:
            json.dump(self.guess_stats, f, indent=4)

    def save_game_stats(self):
        """Save game statistics to file."""
        with open(self.game_stats_file, 'w') as f:
            json.dump(self.game_stats, f, indent=4)

    def update_guess_stats(self, song, correct):
        """Update the guessing statistics for a song."""
        if song not in self.guess_stats:
            self.guess_stats[song] = {
                "correct_guesses": 0,
                "total_guesses": 0,
                "correct_rate": 0.0
            }

        self.guess_stats[song]["total_guesses"] += 1
        if correct:
            self.guess_stats[song]["correct_guesses"] += 1

        # Update correct rate
        self.guess_stats[song]["correct_rate"] = (
                                                         self.guess_stats[song]["correct_guesses"] /
                                                         self.guess_stats[song]["total_guesses"]
                                                 ) * 100.0

        # Save the updated stats
        self.save_guess_stats()

    def update_game_stats(self):
        """Update overall game statistics."""
        self.game_stats["total_games"] += 1
        self.game_stats["total_points"] += self.current_game_score
        self.game_stats["avg_score"] = (
                self.game_stats["total_points"] /
                self.game_stats["total_games"]
        )

        # Save the updated stats
        self.save_game_stats()

    def parse_song_info(self, filename):
        """Parse song filename to extract country, artist, and song name."""
        # Remove file extension
        base_name = os.path.splitext(filename)[0]

        # Split by underscore
        parts = base_name.split('_')

        # Default values if parsing fails
        country = artist = song_name = ""

        if len(parts) >= 3:
            country = parts[0]
            artist = parts[1]
            song_name = '_'.join(parts[2:])  # Join remaining parts if song name contains underscores
        elif len(parts) == 2:
            country = ""
            artist = parts[0]
            song_name = parts[1]
        elif len(parts) == 1:
            country = ""
            artist = ""
            song_name = parts[0]

        return country, artist, song_name

    def start_new_game(self):
        """Start a new guessing game."""
        if not self.songs:
            print("No songs available to play.")
            return

        # Reset game state
        self.current_game_score = 0
        self.current_game_guesses = 0
        self.current_song_index = 0
        self.warning_message = None  # Clear any warning messages

        # Shuffle songs for this game
        self.songs_for_current_game = self.songs.copy()
        random.shuffle(self.songs_for_current_game)

        # Start with the first song
        self.current_song = self.songs_for_current_game[0]
        self.guess_result = None
        self.show_answer = False
        self.user_input = ""
        self.game_in_progress = True
        self.position_offset = 0.0

        # Play the song
        self.play_current_song()

        # Change screen to game
        self.current_screen = "game"

    def play_current_song(self):
        """Play the current song."""
        if self.current_song:
            song_path = os.path.join(self.recordings_dir, self.current_song)
            pygame.mixer.music.load(song_path)
            pygame.mixer.music.play()

    def next_song(self):
        """Move to the next song in the game."""
        # Update current song index
        self.current_song_index += 1
        self.warning_message = None  # Clear any warning messages

        # Check if we've gone through all songs
        if self.current_song_index >= len(self.songs_for_current_game):
            self.end_game()
            return

        # Set the next song
        self.current_song = self.songs_for_current_game[self.current_song_index]
        self.guess_result = None
        self.show_answer = False
        self.user_input = ""
        self.position_offset = 0.0

        # Play the song
        self.play_current_song()

    def end_game(self):
        """End the current game and update statistics."""
        if self.game_in_progress and self.current_game_guesses > 0:
            self.update_game_stats()

        # Reset game state
        self.game_in_progress = False
        self.current_song = None
        pygame.mixer.music.stop()

        # Return to main menu
        self.current_screen = "main_menu"

    def check_guess(self):
        """Check if the user's guess is correct."""
        if not self.current_song:
            return

        country, _, _ = self.parse_song_info(self.current_song)

        # Check if input is at least 3 characters
        if len(self.user_input.strip()) < 3:
            # Set a warning message but don't count this attempt
            self.warning_message = "Input must be at least 3 characters"
            return
        else:
            self.warning_message = None  # Clear any warning

        # Check if guess is correct (as a substring, case-insensitive)
        user_input_lower = self.user_input.strip().lower()
        country_lower = country.lower()
        is_correct = user_input_lower in country_lower

        # Update stats
        self.update_guess_stats(self.current_song, is_correct)
        self.current_game_guesses += 1

        if is_correct:
            self.current_game_score += 1
            self.guess_result = True
        else:
            self.guess_result = False

        # Show the answer
        self.show_answer = True

    # UI Rendering Methods
    def render_text(self, text, font, color, x, y, align="left"):
        """Render text with alignment options."""
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()

        if align == "left":
            text_rect.topleft = (x, y)
        elif align == "center":
            text_rect.midtop = (x, y)
        elif align == "right":
            text_rect.topright = (x, y)

        self.screen.blit(text_surface, text_rect)
        return text_rect

    def create_button(self, text, font, x, y, width, height, inactive_color, active_color):
        """Create a clickable button."""
        mouse_pos = pygame.mouse.get_pos()
        button_rect = pygame.Rect(x, y, width, height)

        if button_rect.collidepoint(mouse_pos):
            pygame.draw.rect(self.screen, active_color, button_rect)
        else:
            pygame.draw.rect(self.screen, inactive_color, button_rect)

        pygame.draw.rect(self.screen, self.BLACK, button_rect, 2)  # Button border

        # Center the text on the button
        text_surf = font.render(text, True, self.BLACK)
        text_rect = text_surf.get_rect(center=button_rect.center)
        self.screen.blit(text_surf, text_rect)

        return button_rect

    def create_input_box(self, x, y, width, height, text=""):
        """Create a text input box."""
        input_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, self.WHITE, input_rect)
        pygame.draw.rect(self.screen, self.BLACK, input_rect, 2)

        # Render the text
        text_surf = self.font_input.render(text, True, self.BLACK)
        text_rect = text_surf.get_rect(midleft=(x + 5, y + height // 2))
        self.screen.blit(text_surf, text_rect)

        return input_rect

    def render_main_menu(self):
        """Render the main menu screen."""
        self.screen.fill(self.WHITE)

        # Title
        self.render_text("SONG GUESSING GAME", self.font_large, self.BLACK,
                         self.screen_width // 2, 30, "center")

        # Menu options
        y_pos = 150
        button_height = 60
        button_spacing = 30

        start_button = self.create_button("Start Game", self.font_medium,
                                          self.screen_width // 2 - 150, y_pos,
                                          300, button_height, self.GRAY, self.LIGHT_BLUE)
        y_pos += button_height + button_spacing

        stats_button = self.create_button("Statistics", self.font_medium,
                                          self.screen_width // 2 - 150, y_pos,
                                          300, button_height, self.GRAY, self.LIGHT_BLUE)
        y_pos += button_height + button_spacing

        quit_button = self.create_button("Quit", self.font_medium,
                                         self.screen_width // 2 - 150, y_pos,
                                         300, button_height, self.GRAY, self.LIGHT_BLUE)

        # Display some game statistics if available
        if self.game_stats["total_games"] > 0:
            stats_y = 400
            self.render_text(f"Games Played: {self.game_stats['total_games']}",
                             self.font_small, self.BLACK,
                             self.screen_width // 2, stats_y, "center")
            self.render_text(f"Average Score: {self.game_stats['avg_score']:.2f} points per game",
                             self.font_small, self.BLACK,
                             self.screen_width // 2, stats_y + 30, "center")

        return start_button, stats_button, quit_button

    def render_game_screen(self):
        """Render the game screen."""
        # Determine background color based on guess result
        if self.guess_result is True:
            self.screen.fill(self.CORRECT_BG)
        elif self.guess_result is False:
            self.screen.fill(self.INCORRECT_BG)
        else:
            self.screen.fill(self.WHITE)

        # Game info
        self.render_text("GUESS THE COUNTRY", self.font_large, self.BLACK,
                         self.screen_width // 2, 30, "center")

        # Score display
        self.render_text(f"Score: {self.current_game_score} / {self.current_game_guesses}",
                         self.font_medium, self.BLACK,
                         self.screen_width - 20, 20, "right")

        # Song progress
        self.render_text(f"Song {self.current_song_index + 1} of {len(self.songs_for_current_game)}",
                         self.font_small, self.BLACK,
                         20, 20, "left")

        # Song info
        if self.current_song:
            country, artist, song_name = self.parse_song_info(self.current_song)

            # If showing answer, display full info
            if self.show_answer:
                # Format artist and song name with the capitalization rules
                formatted_song_name = self.format_name_capitalization(song_name)
                formatted_artist = self.format_name_capitalization(artist)

                self.render_text(f"{formatted_song_name}", self.font_medium, self.BLACK,
                                 self.screen_width // 2, 100, "center")
                self.render_text(f"by {formatted_artist} from {country}", self.font_medium, self.BLACK,
                                 self.screen_width // 2, 140, "center")

                # Result message
                if self.guess_result is True:
                    self.render_text("Correct! +1 point", self.font_medium, self.GREEN,
                                     self.screen_width // 2, 190, "center")
                else:
                    self.render_text(f"Incorrect! The correct answer was: {country}",
                                     self.font_medium, self.RED,
                                     self.screen_width // 2, 190, "center")

                # Next song button
                next_button = self.create_button(
                    "Next Song" if self.current_song_index < len(self.songs_for_current_game) - 1 else "End Game",
                    self.font_medium,
                    self.screen_width // 2 - 100, 340,
                    200, 50, self.GRAY, self.LIGHT_BLUE
                )
            else:
                # Regular game display - just need to guess the country
                self.render_text("Guess the country of this song:", self.font_medium, self.BLACK,
                                 self.screen_width // 2, 100, "center")

                # Display warning message if present
                if self.warning_message:
                    self.render_text(self.warning_message, self.font_small, self.RED,
                                     self.screen_width // 2, 130, "center")

                # Input box
                input_box = self.create_input_box(
                    self.screen_width // 2 - 150, 160,
                    300, 40, self.user_input
                )

                # Submit button
                submit_button = self.create_button("Submit Guess", self.font_medium,
                                                   self.screen_width // 2 - 100, 220,
                                                   200, 50, self.GRAY, self.LIGHT_BLUE)
                next_button = None

            # Playback controls guide
            controls_y = 400
            self.render_text("Playback Controls:", self.font_small, self.BLACK,
                             self.screen_width // 2, controls_y, "center")
            self.render_text("RIGHT: Skip +5s", self.font_small, self.BLACK,
                             self.screen_width // 2, controls_y + 25, "center")
            self.render_text("LEFT: Rewind -5s", self.font_small, self.BLACK,
                             self.screen_width // 2, controls_y + 50, "center")
        else:
            # No song loaded
            self.render_text("No song loaded", self.font_medium, self.BLACK,
                             self.screen_width // 2, 100, "center")
            next_button = None
            submit_button = None
            input_box = None

        # Back to menu button
        back_button = self.create_button("Back to Menu", self.font_medium,
                                         self.screen_width // 2 - 100, 500,
                                         200, 50, self.GRAY, self.LIGHT_BLUE)

        if self.show_answer:
            return back_button, next_button, None, None
        else:
            return back_button, None, submit_button, input_box

    def render_statistics_screen(self):
        """Render the statistics screen."""
        self.screen.fill(self.WHITE)

        # Title
        self.render_text("GAME STATISTICS", self.font_large, self.BLACK,
                         self.screen_width // 2, 30, "center")

        y_pos = 100

        # Game stats
        if self.game_stats["total_games"] > 0:
            self.render_text("Overall Game Stats:", self.font_medium, self.BLACK, 50, y_pos)
            y_pos += 40

            self.render_text(f"Total Games Played: {self.game_stats['total_games']}",
                             self.font_small, self.BLACK, 70, y_pos)
            y_pos += 30

            self.render_text(f"Average Score: {self.game_stats['avg_score']:.2f} points per game",
                             self.font_small, self.BLACK, 70, y_pos)
            y_pos += 50
        else:
            self.render_text("No games played yet.", self.font_medium, self.BLACK, 50, y_pos)
            y_pos += 50

        # Song stats
        if self.guess_stats:
            self.render_text("Song Guessing Stats:", self.font_medium, self.BLACK, 50, y_pos)
            y_pos += 40

            # Sort songs by correct rate
            sorted_songs = sorted(
                [(song, stats) for song, stats in self.guess_stats.items()
                 if stats["total_guesses"] > 0],
                key=lambda x: x[1]["correct_rate"],
                reverse=True
            )

            if sorted_songs:
                # Best guessed songs
                self.render_text("Top 3 Best-Guessed Songs:", self.font_small, self.GREEN, 70, y_pos)
                y_pos += 30

                for i, (song, stats) in enumerate(sorted_songs[:3]):
                    country, artist, _ = self.parse_song_info(song)
                    # Format artist with the capitalization rules
                    formatted_artist = self.format_name_capitalization(artist)

                    self.render_text(
                        f"{i + 1}. {formatted_artist} ({country}): {stats['correct_rate']:.1f}% correct",
                        self.font_small, self.BLACK, 90, y_pos
                    )
                    y_pos += 25

                y_pos += 20

                # Worst guessed songs
                self.render_text("Top 3 Most Challenging Songs:", self.font_small, self.RED, 70, y_pos)
                y_pos += 30

                for i, (song, stats) in enumerate(sorted_songs[-3:]):
                    country, artist, _ = self.parse_song_info(song)
                    # Format artist with the capitalization rules
                    formatted_artist = self.format_name_capitalization(artist)

                    self.render_text(
                        f"{i + 1}. {formatted_artist} ({country}): {stats['correct_rate']:.1f}% correct",
                        self.font_small, self.BLACK, 90, y_pos
                    )
                    y_pos += 25
            else:
                self.render_text("No song guessing data available yet.",
                                 self.font_small, self.BLACK, 70, y_pos)
        else:
            self.render_text("No song guessing data available yet.",
                             self.font_medium, self.BLACK, 50, y_pos)

        # Back button
        back_button = self.create_button("Back to Main Menu", self.font_medium,
                                         self.screen_width // 2 - 150, 500,
                                         300, 50, self.GRAY, self.LIGHT_BLUE)

        return back_button

    def handle_playback_controls(self, event):
        """Handle playback controls for the song."""
        if not pygame.mixer.music.get_busy() or not self.current_song:
            return

        song_path = os.path.join(self.recordings_dir, self.current_song)

        if event.key == pygame.K_RIGHT:
            # Skip forward 5 seconds
            current_pos = pygame.mixer.music.get_pos() / 1000 + self.position_offset
            new_pos = current_pos + 5.0
            pygame.mixer.music.stop()
            pygame.mixer.music.load(song_path)
            pygame.mixer.music.play(start=new_pos)
            self.position_offset = new_pos
        elif event.key == pygame.K_LEFT:
            # Rewind 5 seconds
            current_pos = pygame.mixer.music.get_pos() / 1000 + self.position_offset
            new_pos = max(0, current_pos - 5.0)
            pygame.mixer.music.stop()
            pygame.mixer.music.load(song_path)
            pygame.mixer.music.play(start=new_pos)
            self.position_offset = new_pos

    def run(self):
        """Main game loop."""
        running = True
        clock = pygame.time.Clock()

        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    # Update the screen size if window is resized
                    self.screen_width, self.screen_height = event.size
                    self.screen = pygame.display.set_mode((self.screen_width, self.screen_height),
                                                          pygame.RESIZABLE)
                elif event.type == pygame.KEYDOWN:
                    # Handle playback controls in game screen
                    if self.current_screen == "game" and self.current_song:
                        self.handle_playback_controls(event)

                    # Handle text input for guessing
                    if self.current_screen == "game" and not self.show_answer:
                        if event.key == pygame.K_RETURN:
                            # Submit guess
                            if self.user_input.strip():
                                self.check_guess()
                        elif event.key == pygame.K_BACKSPACE:
                            self.user_input = self.user_input[:-1]
                        else:
                            # Add character to input (only if it's a letter or space)
                            if event.unicode.isalpha() or event.unicode.isspace():
                                self.user_input += event.unicode
                    # Handle Enter key to move to next song when showing answer
                    elif self.current_screen == "game" and self.show_answer and event.key == pygame.K_RETURN:
                        self.next_song()
                        pygame.time.delay(200)  # Prevent double actions

            # Handle mouse clicks
            mouse_clicked = pygame.mouse.get_pressed()[0]  # Left mouse button
            mouse_pos = pygame.mouse.get_pos()

            # Render current screen and handle button clicks
            if self.current_screen == "main_menu":
                buttons = self.render_main_menu()

                if mouse_clicked:
                    if buttons[0].collidepoint(mouse_pos):  # Start Game
                        self.start_new_game()
                        pygame.time.delay(200)  # Prevent double-clicks
                    elif buttons[1].collidepoint(mouse_pos):  # Statistics
                        self.current_screen = "statistics"
                        pygame.time.delay(200)
                    elif buttons[2].collidepoint(mouse_pos):  # Quit
                        running = False

            elif self.current_screen == "game":
                buttons = self.render_game_screen()
                back_button, next_button, submit_button, input_box = buttons

                if mouse_clicked:
                    if back_button.collidepoint(mouse_pos):  # Back to Menu
                        self.end_game()
                        pygame.time.delay(200)

                    if next_button and next_button.collidepoint(mouse_pos):  # Next Song / End Game
                        self.next_song()
                        pygame.time.delay(200)

                    if submit_button and submit_button.collidepoint(mouse_pos):  # Submit Guess
                        if self.user_input.strip():
                            self.check_guess()
                            pygame.time.delay(200)

                    if input_box and input_box.collidepoint(mouse_pos):  # Activate text input
                        self.input_active = True
                    else:
                        self.input_active = False

            elif self.current_screen == "statistics":
                back_button = self.render_statistics_screen()

                if mouse_clicked and back_button.collidepoint(mouse_pos):
                    self.current_screen = "main_menu"
                    pygame.time.delay(200)

            # Update the display
            pygame.display.flip()

            # Cap the frame rate
            clock.tick(60)

        # Ensure stats are saved before exit
        self.save_guess_stats()
        self.save_game_stats()

        # Clean exit
        pygame.quit()
        print("Thanks for playing Song Guessing Game!")


if __name__ == "__main__":
    send_log()
    game = SongGuessingGame()
    game.run()
