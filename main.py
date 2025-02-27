import os
import json
import random
import pygame
import sys
import math


class SongRanker:
    def __init__(self):
        self.recordings_dir = "recordings"
        self.rankings_file = "song_rankings.json"
        self.listening_stats_file = "listening_stats.json"
        self.comparison_history_file = "comparison_history.json"
        self.songs = []
        self.rankings = {}
        self.listening_stats = {}
        self.comparison_history = []  # Track all comparisons with outcomes
        self.compared_pairs = set()  # Track which pairs have been compared

        # Initialize pygame for audio playback and UI
        pygame.init()
        pygame.mixer.init()

        # Set up the display
        self.screen_width = 800
        self.screen_height = 600
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
        pygame.display.set_caption("Song Ranker")

        # Set up fonts
        self.font_large = pygame.font.SysFont(None, 48)
        self.font_medium = pygame.font.SysFont(None, 36)
        self.font_small = pygame.font.SysFont(None, 24)

        # Colors
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.GRAY = (200, 200, 200)
        self.DARK_GRAY = (100, 100, 100)
        self.BLUE = (0, 0, 255)
        self.LIGHT_BLUE = (100, 100, 255)
        self.GREEN = (50, 200, 50)
        self.RED = (200, 50, 50)

        # UI state
        self.current_screen = "main_menu"
        self.scroll_offset = 0
        self.max_scroll = 0
        self.message_log = []
        self.current_song1 = None
        self.current_song2 = None

        # Load data
        self.load_songs()
        self.load_rankings()
        self.load_listening_stats()
        self.load_comparison_history()

    def load_songs(self):
        if os.path.exists(self.recordings_dir):
            self.songs = [f for f in os.listdir(self.recordings_dir)
                          if f.lower().endswith(('.mp3', '.wav', '.ogg', '.flac'))]
        else:
            self.log_message(f"Directory '{self.recordings_dir}' not found.")
            os.makedirs(self.recordings_dir)

    def load_rankings(self):
        if os.path.exists(self.rankings_file):
            with open(self.rankings_file, 'r') as f:
                old_rankings = json.load(f)

            # Convert old format to new format if needed
            self.rankings = {}
            for song, data in old_rankings.items():
                if isinstance(data, dict) and "rating" in data:
                    # Already in new format
                    self.rankings[song] = data
                else:
                    # Convert from old format (just a number)
                    self.rankings[song] = {
                        "rating": float(data),
                        "uncertainty": 50.0,  # Medium uncertainty for existing ratings
                        "comparisons": 10  # Assume some comparisons have been made
                    }
        else:
            self.rankings = {}

        # Initialize rankings for new songs
        for song in self.songs:
            if song not in self.rankings:
                self.rankings[song] = {
                    "rating": 1000.0,  # Default rating
                    "uncertainty": 100.0,  # High initial uncertainty
                    "comparisons": 0  # No comparisons yet
                }

    def save_rankings(self):
        with open(self.rankings_file, 'w') as f:
            json.dump(self.rankings, f)

    def load_listening_stats(self):
        if os.path.exists(self.listening_stats_file):
            with open(self.listening_stats_file, 'r') as f:
                self.listening_stats = json.load(f)

        # Initialize stats for new songs
        for song in self.songs:
            if song not in self.listening_stats:
                self.listening_stats[song] = {
                    "total_listen_time": 0,
                    "listen_count": 0,
                    "average_listen_time": 0
                }

    def load_comparison_history(self):
        if os.path.exists(self.comparison_history_file):
            with open(self.comparison_history_file, 'r') as f:
                self.comparison_history = json.load(f)

            # Rebuild compared_pairs set from history
            self.compared_pairs = set()
            for comp in self.comparison_history:
                pair = frozenset([comp["song1"], comp["song2"]])
                self.compared_pairs.add(pair)

    def save_comparison_history(self):
        with open(self.comparison_history_file, 'w') as f:
            json.dump(self.comparison_history, f)

    def update_listening_stats(self, song, listen_time):
        if song not in self.listening_stats:
            self.listening_stats[song] = {
                "total_listen_time": 0,
                "listen_count": 0,
                "average_listen_time": 0
            }

        self.listening_stats[song]["total_listen_time"] += listen_time
        self.listening_stats[song]["listen_count"] += 1
        self.listening_stats[song]["average_listen_time"] = (
                self.listening_stats[song]["total_listen_time"] /
                self.listening_stats[song]["listen_count"]
        )

        # Save stats after each update
        self.save_listening_stats()

    def save_listening_stats(self):
        with open(self.listening_stats_file, 'w') as f:
            json.dump(self.listening_stats, f)

    # UI Helper Methods
    def log_message(self, message):
        """Add a message to the log (hidden, but kept for compatibility)"""
        self.message_log.append(message)
        # Keep the log to a reasonable size
        if len(self.message_log) > 20:
            self.message_log.pop(0)

    def render_text(self, text, font, color, x, y, align="left"):
        """Render text with alignment options"""
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
        """Create a clickable button"""
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

    # Play song function (modified to use the UI)
    def play_song(self, song_path):
        song_name = os.path.basename(song_path)
        self.log_message(f"Playing: {song_name}")
        self.log_message("Controls:")
        self.log_message("- Press 'q' to stop and return")
        self.log_message("- Press RIGHT ARROW or 'D' to skip forward 5 seconds")
        self.log_message("- Press LEFT ARROW or 'A' to rewind 5 seconds")

        pygame.mixer.music.load(song_path)
        # Start playing from the beginning
        pygame.mixer.music.play()

        # Track the current position (in seconds)
        position_offset = 0.0  # Start from the beginning
        actual_listen_time = 0  # Track actual listening time

        playing = True
        last_time_check = pygame.time.get_ticks() / 1000
        self.current_screen = "playback"

        while playing and self.current_screen == "playback":
            current_time = pygame.time.get_ticks() / 1000
            # Only count time when music is actually playing
            if pygame.mixer.music.get_busy():
                actual_listen_time += current_time - last_time_check
            last_time_check = current_time

            # Handle all pygame events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        playing = False
                        self.log_message("Stopping playback and returning...")
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        # Skip forward 5 seconds
                        current_pos = pygame.mixer.music.get_pos() / 1000 + position_offset
                        new_pos = current_pos + 5.0
                        pygame.mixer.music.stop()
                        pygame.mixer.music.load(song_path)
                        pygame.mixer.music.play(start=new_pos)
                        position_offset = new_pos
                        self.log_message(f"Skipped forward to {new_pos:.1f} seconds")
                    elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        # Rewind 5 seconds
                        current_pos = pygame.mixer.music.get_pos() / 1000 + position_offset
                        new_pos = max(0, current_pos - 5.0)
                        pygame.mixer.music.stop()
                        pygame.mixer.music.load(song_path)
                        pygame.mixer.music.play(start=new_pos)
                        position_offset = new_pos
                        self.log_message(f"Rewound to {new_pos:.1f} seconds")

            # Render the playback screen
            self.screen.fill(self.WHITE)

            # Song playback information
            self.render_text(f"Now Playing: {song_name}", self.font_medium, self.BLACK,
                             self.screen_width // 2, 50, "center")

            # Play/pause control
            is_playing = pygame.mixer.music.get_busy()
            play_status = "PLAYING" if is_playing else "PAUSED"
            self.render_text(f"Status: {play_status}", self.font_medium, self.BLACK,
                             self.screen_width // 2, 100, "center")

            # Playback controls guide
            controls_y = 150
            self.render_text("Controls:", self.font_small, self.BLACK, 50, controls_y)
            self.render_text("Q: Stop and Return", self.font_small, self.BLACK, 50, controls_y + 30)
            self.render_text("RIGHT/D: Skip +5s", self.font_small, self.BLACK, 50, controls_y + 60)
            self.render_text("LEFT/A: Rewind -5s", self.font_small, self.BLACK, 50, controls_y + 90)

            # Stop button
            stop_button = self.create_button("Stop Playback (Q)", self.font_medium,
                                             self.screen_width // 2 - 100, 400, 200, 50,
                                             self.GRAY, self.LIGHT_BLUE)

            # Update the display
            pygame.display.flip()

            # Check for button clicks
            if pygame.mouse.get_pressed()[0]:  # Left mouse button
                pos = pygame.mouse.get_pos()
                if stop_button.collidepoint(pos):
                    playing = False
                    self.log_message("Stopping playback and returning...")

            # Check if song has finished playing
            if not pygame.mixer.music.get_busy() and playing:
                playing = False
                self.log_message("Song finished playing")

            # Small delay to reduce CPU usage
            pygame.time.delay(10)

        pygame.mixer.music.stop()

        # Update listening stats
        self.update_listening_stats(song_name, actual_listen_time)

    # IMPROVED: Update TrueSkill-inspired ranking system with uncertainty
    def update_ranking(self, winner, loser):
        # Get current ratings and uncertainties
        winner_data = self.rankings[winner]
        loser_data = self.rankings[loser]

        # Adaptive K-factor based on uncertainty - higher uncertainty means more dramatic updates
        base_k = 32
        winner_k = min(base_k * 1.5, base_k * (1 + winner_data["uncertainty"] / 100))
        loser_k = min(base_k * 1.5, base_k * (1 + loser_data["uncertainty"] / 100))

        # Calculate expected outcome (using Elo formula)
        winner_rating = winner_data["rating"]
        loser_rating = loser_data["rating"]

        expected_win = 1 / (1 + 10 ** ((loser_rating - winner_rating) / 400))

        # Update ratings based on actual vs expected outcome
        new_winner_rating = winner_rating + winner_k * (1 - expected_win)
        new_loser_rating = loser_rating + loser_k * (0 - (1 - expected_win))

        # Update uncertainties - decrease based on number of comparisons and certainty of outcome
        certainty_factor = abs(0.5 - expected_win) * 2  # How certain we were of the outcome
        uncertainty_reduction = 0.85 - (certainty_factor * 0.1)  # Between 0.75 and 0.85

        winner_data["uncertainty"] = max(15, winner_data["uncertainty"] * uncertainty_reduction)
        loser_data["uncertainty"] = max(15, loser_data["uncertainty"] * uncertainty_reduction)

        # Increment comparison counters
        winner_data["comparisons"] = winner_data.get("comparisons", 0) + 1
        loser_data["comparisons"] = loser_data.get("comparisons", 0) + 1

        # Update the ratings
        winner_data["rating"] = new_winner_rating
        loser_data["rating"] = new_loser_rating

        # Add to comparison history
        self.comparison_history.append({
            "song1": winner,
            "song2": loser,
            "winner": winner,
            "time": pygame.time.get_ticks() / 1000  # Timestamp
        })

        # Save comparison history
        self.save_comparison_history()

        # Save updated rankings
        self.save_rankings()

        return abs(new_winner_rating - winner_rating)  # Return rating change magnitude

    # IMPROVED: Smarter comparison selection that balances exploration and refinement
    def select_comparison_pair(self):
        if len(self.songs) < 2:
            return None, None

        # Calculate "Information Gain" for each potential pairing
        pair_scores = []

        # Track how many times each song has been compared
        song_comparison_count = {song: 0 for song in self.songs}
        for pair in self.compared_pairs:
            pair_list = list(pair)
            song_comparison_count[pair_list[0]] = song_comparison_count.get(pair_list[0], 0) + 1
            song_comparison_count[pair_list[1]] = song_comparison_count.get(pair_list[1], 0) + 1

        # First prioritize songs that have never been compared
        uncomp_songs = [s for s in self.songs if song_comparison_count[s] == 0]
        if len(uncomp_songs) >= 2:
            # Randomly select two uncompared songs
            return random.sample(uncomp_songs, 2)
        elif len(uncomp_songs) == 1:
            # Pair the uncompared song with another song that has been compared least
            other_songs = sorted([s for s in self.songs if s != uncomp_songs[0]],
                                 key=lambda s: song_comparison_count[s])
            return uncomp_songs[0], other_songs[0]

        # Generate all possible pairs for scoring
        for i, song1 in enumerate(self.songs):
            for song2 in self.songs[i + 1:]:
                # Skip pairs that have been compared too many times
                pair = frozenset([song1, song2])
                times_compared = sum(1 for comp in self.comparison_history
                                     if frozenset([comp["song1"], comp["song2"]]) == pair)

                # Limit repeated comparisons of the same pair
                if times_compared >= 3:
                    continue

                s1_data = self.rankings[song1]
                s2_data = self.rankings[song2]

                # Calculate how informative this comparison would be

                # 1. Uncertainty score - higher is better (prioritize uncertain songs)
                uncertainty_score = (s1_data["uncertainty"] + s2_data["uncertainty"]) / 2

                # 2. Rating proximity score - higher when ratings are close
                rating_diff = abs(s1_data["rating"] - s2_data["rating"])
                # Sigmoid function to prioritize songs with similar ratings
                proximity_score = 200 / (1 + math.exp(rating_diff / 100))

                # 3. Novelty score - prioritize pairs that haven't been compared
                novelty_score = 100 if times_compared == 0 else (30 if times_compared == 1 else 10)

                # 4. Undersampled score - prioritize songs with fewer comparisons
                comp_deficit = max(0, 5 - min(song_comparison_count[song1], song_comparison_count[song2]))
                undersampled_score = comp_deficit * 15

                # Combine all factors with weights
                total_score = (
                        uncertainty_score * 1.0 +
                        proximity_score * 0.8 +
                        novelty_score * 1.2 +
                        undersampled_score * 1.5
                )

                pair_scores.append((song1, song2, total_score))

        # If we have valid pairs to compare
        if pair_scores:
            # Sort by score (highest first)
            pair_scores.sort(key=lambda x: x[2], reverse=True)

            # Get top 3 pairs and select one randomly (adds some exploration)
            top_n = min(3, len(pair_scores))
            selected_pair = random.choice(pair_scores[:top_n])
            return selected_pair[0], selected_pair[1]

        # Fallback: just pick two random songs
        return random.sample(self.songs, 2)

    # Modified to use the UI
    def run_comparison(self):
        if len(self.songs) < 2:
            self.log_message("Need at least 2 songs to compare. Please add songs to the 'recordings' folder.")
            self.current_screen = "main_menu"
            return

        self.current_song1, self.current_song2 = self.select_comparison_pair()

        if self.current_song1 is None or self.current_song2 is None:
            self.log_message("Could not select a valid song pair for comparison.")
            self.current_screen = "main_menu"
            return

        # Track this pair as compared
        self.compared_pairs.add(frozenset([self.current_song1, self.current_song2]))

        self.current_screen = "comparison"

    # Screen rendering methods
    def render_comparison_screen(self):
        self.screen.fill(self.WHITE)

        # Title
        self.render_text("SONG COMPARISON", self.font_large, self.BLACK,
                         self.screen_width // 2, 30, "center")

        # Get current ratings if available
        s1_rating = self.rankings[self.current_song1]["rating"] if self.current_song1 in self.rankings else "?"
        s2_rating = self.rankings[self.current_song2]["rating"] if self.current_song2 in self.rankings else "?"

        # Song 1 info
        y_pos = 100
        self.render_text(f"Song 1: {self.current_song1}", self.font_medium, self.BLACK,
                         self.screen_width // 2, y_pos, "center")
        if s1_rating != "?":
            self.render_text(f"Current Rating: {s1_rating:.1f}", self.font_small, self.DARK_GRAY,
                             self.screen_width // 2, y_pos + 30, "center")

        # Song 1 buttons
        play1_button = self.create_button("Play Song 1", self.font_medium,
                                          self.screen_width // 2 - 250, y_pos + 70,
                                          200, 50, self.GRAY, self.LIGHT_BLUE)
        vote1_button = self.create_button("Prefer Song 1", self.font_medium,
                                          self.screen_width // 2 + 50, y_pos + 70,
                                          200, 50, self.GRAY, self.GREEN)

        # Song 2 info
        y_pos = 250
        self.render_text(f"Song 2: {self.current_song2}", self.font_medium, self.BLACK,
                         self.screen_width // 2, y_pos, "center")
        if s2_rating != "?":
            self.render_text(f"Current Rating: {s2_rating:.1f}", self.font_small, self.DARK_GRAY,
                             self.screen_width // 2, y_pos + 30, "center")

        # Song 2 buttons
        play2_button = self.create_button("Play Song 2", self.font_medium,
                                          self.screen_width // 2 - 250, y_pos + 70,
                                          200, 50, self.GRAY, self.LIGHT_BLUE)
        vote2_button = self.create_button("Prefer Song 2", self.font_medium,
                                          self.screen_width // 2 + 50, y_pos + 70,
                                          200, 50, self.GRAY, self.GREEN)

        # Return button
        back_button = self.create_button("Back to Main Menu", self.font_medium,
                                         self.screen_width // 2 - 150, 450,
                                         300, 50, self.GRAY, self.LIGHT_BLUE)

        return play1_button, vote1_button, play2_button, vote2_button, back_button

    def render_main_menu(self):
        self.screen.fill(self.WHITE)

        # Title
        self.render_text("SONG RANKER", self.font_large, self.BLACK,
                         self.screen_width // 2, 30, "center")

        # Menu options
        y_pos = 120
        button_height = 60
        button_spacing = 20

        compare_button = self.create_button("1. Compare Songs", self.font_medium,
                                            self.screen_width // 2 - 150, y_pos,
                                            300, button_height, self.GRAY, self.LIGHT_BLUE)
        y_pos += button_height + button_spacing

        rankings_button = self.create_button("2. View Rankings", self.font_medium,
                                             self.screen_width // 2 - 150, y_pos,
                                             300, button_height, self.GRAY, self.LIGHT_BLUE)
        y_pos += button_height + button_spacing

        stats_button = self.create_button("3. View Listening Statistics", self.font_medium,
                                          self.screen_width // 2 - 150, y_pos,
                                          300, button_height, self.GRAY, self.LIGHT_BLUE)
        y_pos += button_height + button_spacing

        progress_button = self.create_button("4. View Ranking Confidence", self.font_medium,
                                             self.screen_width // 2 - 150, y_pos,
                                             300, button_height, self.GRAY, self.LIGHT_BLUE)
        y_pos += button_height + button_spacing

        refresh_button = self.create_button("5. Refresh Song List", self.font_medium,
                                            self.screen_width // 2 - 150, y_pos,
                                            300, button_height, self.GRAY, self.LIGHT_BLUE)
        y_pos += button_height + button_spacing

        exit_button = self.create_button("6. Exit", self.font_medium,
                                         self.screen_width // 2 - 150, y_pos,
                                         300, button_height, self.GRAY, self.LIGHT_BLUE)

        return compare_button, rankings_button, stats_button, progress_button, refresh_button, exit_button

    def render_rankings_screen(self):
        self.screen.fill(self.WHITE)

        # Title
        self.render_text("CURRENT SONG RANKINGS", self.font_large, self.BLACK,
                         self.screen_width // 2, 30, "center")

        if not self.rankings:
            self.render_text("No rankings available yet.", self.font_medium, self.BLACK,
                             self.screen_width // 2, 100, "center")
        else:
            # Sort by rating
            sorted_rankings = sorted(
                self.rankings.items(),
                key=lambda x: x[1]["rating"] if isinstance(x[1], dict) else x[1],
                reverse=True
            )

            # Header
            self.render_text("Rank", self.font_medium, self.BLACK, 50, 80)
            self.render_text("Song", self.font_medium, self.BLACK, 120, 80)
            self.render_text("Rating", self.font_medium, self.BLACK, 500, 80)
            self.render_text("Confidence", self.font_medium, self.BLACK, 600, 80)
            pygame.draw.line(self.screen, self.BLACK, (50, 105), (self.screen_width - 50, 105), 2)

            # Display rankings in a scrollable area
            y_pos = 120 - self.scroll_offset
            for rank, (song, data) in enumerate(sorted_rankings, 1):
                if y_pos + 30 > 120 and y_pos < 400:  # Only render visible items
                    if isinstance(data, dict):
                        rating = data["rating"]
                        uncertainty = data["uncertainty"]
                        comparisons = data.get("comparisons", 0)

                        # Calculate confidence as inverse of uncertainty (0-100%)
                        confidence = max(0, min(100, 100 - uncertainty))
                        confidence_color = (
                            int(255 - confidence * 2.55),  # More red when less confident
                            int(confidence * 2.55),  # More green when more confident
                            0
                        )

                        self.render_text(f"{rank}.", self.font_medium, self.BLACK, 50, y_pos)

                        # Truncate long song names
                        display_name = song
                        if len(display_name) > 30:
                            display_name = display_name[:27] + "..."
                        self.render_text(display_name, self.font_medium, self.BLACK, 120, y_pos)

                        self.render_text(f"{rating:.1f}", self.font_medium, self.BLACK, 500, y_pos)
                        self.render_text(f"{confidence:.0f}%", self.font_medium, confidence_color, 600, y_pos)
                    else:
                        # Handle old format (just a number)
                        self.render_text(f"{rank}. {song} (Rating: {data})",
                                         self.font_medium, self.BLACK, 50, y_pos)
                y_pos += 30

            # Calculate max scroll
            self.max_scroll = max(0, len(sorted_rankings) * 30 - 280)

        # Back button
        back_button = self.create_button("Back to Main Menu", self.font_medium,
                                         self.screen_width // 2 - 150, 450,
                                         300, 50, self.GRAY, self.LIGHT_BLUE)

        return back_button

    def render_stats_screen(self):
        self.screen.fill(self.WHITE)

        # Title
        self.render_text("LISTENING STATISTICS", self.font_large, self.BLACK,
                         self.screen_width // 2, 30, "center")

        if not self.listening_stats:
            self.render_text("No listening statistics available yet.", self.font_medium, self.BLACK,
                             self.screen_width // 2, 100, "center")
        else:
            # Sort by average listen time (descending)
            sorted_stats = sorted(
                self.listening_stats.items(),
                key=lambda x: x[1]["average_listen_time"],
                reverse=True
            )

            # Header
            self.render_text("Song", self.font_medium, self.BLACK, 50, 80)
            self.render_text("Avg. Time", self.font_medium, self.BLACK, 400, 80)
            self.render_text("Listens", self.font_medium, self.BLACK, 500, 80)
            self.render_text("Total Time", self.font_medium, self.BLACK, 600, 80)
            pygame.draw.line(self.screen, self.BLACK, (50, 105), (self.screen_width - 50, 105), 2)

            # Display stats in a scrollable area
            y_pos = 120 - self.scroll_offset
            for song, stats in sorted_stats:
                if stats["listen_count"] > 0:
                    if y_pos + 30 > 120 and y_pos < 400:  # Only render visible items
                        avg_time = stats["average_listen_time"]
                        count = stats["listen_count"]
                        total = stats["total_listen_time"]

                        # Truncate long song names
                        display_name = song
                        if len(display_name) > 25:
                            display_name = display_name[:22] + "..."

                        self.render_text(display_name, self.font_medium, self.BLACK, 50, y_pos)
                        self.render_text(f"{avg_time:.1f}s", self.font_medium, self.BLACK, 400, y_pos)
                        self.render_text(f"{count}", self.font_medium, self.BLACK, 500, y_pos)
                        self.render_text(f"{total:.1f}s", self.font_medium, self.BLACK, 600, y_pos)

                    y_pos += 30  # Less space between entries for more compact view

            # Calculate max scroll
            self.max_scroll = max(0, sum(30 for song, stats in sorted_stats if stats["listen_count"] > 0) - 280)

        # Back button
        back_button = self.create_button("Back to Main Menu", self.font_medium,
                                         self.screen_width // 2 - 150, 450,
                                         300, 50, self.GRAY, self.LIGHT_BLUE)

        return back_button

    def render_progress_screen(self):
        self.screen.fill(self.WHITE)

        # Title
        self.render_text("RANKING CONFIDENCE", self.font_large, self.BLACK,
                         self.screen_width // 2, 30, "center")

        total_songs = len(self.songs)
        if total_songs < 2:
            self.render_text("Not enough songs to calculate ranking confidence.", self.font_medium, self.BLACK,
                             self.screen_width // 2, 100, "center")
        else:
            # Calculate statistics
            total_comparisons = len(self.comparison_history)
            unique_pairs = len(self.compared_pairs)
            total_possible_pairs = (total_songs * (total_songs - 1)) // 2

            # Calculate average uncertainty across all songs
            uncertainties = [data["uncertainty"] for data in self.rankings.values()
                             if isinstance(data, dict) and "uncertainty" in data]
            avg_uncertainty = sum(uncertainties) / len(uncertainties) if uncertainties else 100

            # Estimate overall ranking confidence (0-100%)
            coverage_pct = (unique_pairs / total_possible_pairs) * 100 if total_possible_pairs > 0 else 0
            confidence_pct = max(0, min(100, 100 - avg_uncertainty))

            # Modified formula that considers both coverage and average uncertainty
            adjusted_confidence = (coverage_pct * 0.4) + (confidence_pct * 0.6)

            # Display overall statistics
            self.render_text(f"Total songs: {total_songs}", self.font_medium, self.BLACK, 50, 100)
            self.render_text(f"Total comparisons: {total_comparisons}", self.font_medium, self.BLACK, 50, 130)
            self.render_text(f"Unique pairs compared: {unique_pairs}/{total_possible_pairs} ({coverage_pct:.1f}%)",
                             self.font_medium, self.BLACK, 50, 160)

            # Display confidence measure
            confidence_color = (
                int(255 - adjusted_confidence * 2.55),  # Red component
                int(adjusted_confidence * 2.55),  # Green component
                0
            )

            self.render_text("Overall Ranking Confidence:", self.font_medium, self.BLACK, 50, 200)

            # Draw confidence bar
            bar_width = 400
            bar_height = 30
            bar_x = self.screen_width // 2 - bar_width // 2
            bar_y = 230

            # Background bar (gray)
            pygame.draw.rect(self.screen, self.GRAY, (bar_x, bar_y, bar_width, bar_height))

            # Confidence level bar (colored)
            filled_width = int(bar_width * adjusted_confidence / 100)
            pygame.draw.rect(self.screen, confidence_color, (bar_x, bar_y, filled_width, bar_height))

            # Border
            pygame.draw.rect(self.screen, self.BLACK, (bar_x, bar_y, bar_width, bar_height), 2)

            # Percentage text
            self.render_text(f"{adjusted_confidence:.1f}%", self.font_medium, self.BLACK,
                             self.screen_width // 2, bar_y + bar_height + 10, "center")

            # Interpretation text
            if adjusted_confidence < 30:
                advice = "Keep comparing more songs to improve confidence"
            elif adjusted_confidence < 60:
                advice = "Ranking is forming, but needs more comparisons"
            elif adjusted_confidence < 80:
                advice = "Ranking is fairly reliable"
            else:
                advice = "Ranking is highly confident"

            self.render_text(advice, self.font_medium, self.BLACK,
                             self.screen_width // 2, bar_y + bar_height + 40, "center")

            # Information about how to improve
            if adjusted_confidence < 90:
                suggested_comparisons = min(10, total_possible_pairs - unique_pairs)
                self.render_text(f"Suggestion: Compare at least {suggested_comparisons} more pairs",
                                 self.font_small, self.BLACK, 50, 320)

                # Find songs with highest uncertainty
                high_uncertainty = sorted(
                    [(song, data["uncertainty"]) for song, data in self.rankings.items()],
                    key=lambda x: x[1], reverse=True
                )[:3]  # Top 3

                if high_uncertainty:
                    self.render_text("Focus on these songs with highest uncertainty:",
                                     self.font_small, self.BLACK, 50, 350)

                    y_pos = 380
                    for i, (song, uncertainty) in enumerate(high_uncertainty):
                        self.render_text(f"{i + 1}. {song} (±{uncertainty:.1f})",
                                         self.font_small, self.BLACK, 70, y_pos)
                        y_pos += 25

        # Back button
        back_button = self.create_button("Back to Main Menu", self.font_medium,
                                         self.screen_width // 2 - 150, 450,
                                         300, 50, self.GRAY, self.LIGHT_BLUE)

        return back_button

    # Main application loop
    def run(self):
        running = True
        clock = pygame.time.Clock()

        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEWHEEL:
                    self.scroll_offset -= event.y * 30  # Adjust scroll speed
                    # Clamp scroll offset
                    self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))
                elif event.type == pygame.VIDEORESIZE:
                    # Update the screen size if window is resized
                    self.screen_width, self.screen_height = event.size
                    self.screen = pygame.display.set_mode((self.screen_width, self.screen_height),
                                                          pygame.RESIZABLE)

            # Handle mouse clicks - we do this separately to avoid multiple clicks
            mouse_clicked = pygame.mouse.get_pressed()[0]  # Left mouse button
            mouse_pos = pygame.mouse.get_pos()

            # Render the current screen
            if self.current_screen == "main_menu":
                buttons = self.render_main_menu()

                # Check for button clicks
                if mouse_clicked:
                    if buttons[0].collidepoint(mouse_pos):  # Compare Songs
                        self.run_comparison()
                        pygame.time.delay(200)  # Prevent double-clicks
                    elif buttons[1].collidepoint(mouse_pos):  # View Rankings
                        self.current_screen = "rankings"
                        self.scroll_offset = 0
                        pygame.time.delay(200)
                    elif buttons[2].collidepoint(mouse_pos):  # View Listening Statistics
                        self.current_screen = "stats"
                        self.scroll_offset = 0
                        pygame.time.delay(200)
                    elif buttons[3].collidepoint(mouse_pos):  # View Ranking Confidence
                        self.current_screen = "progress"
                        self.scroll_offset = 0
                        pygame.time.delay(200)
                    elif buttons[4].collidepoint(mouse_pos):  # Refresh Song List
                        self.load_songs()
                        self.load_rankings()
                        self.load_listening_stats()
                        self.log_message("Song list refreshed.")
                        pygame.time.delay(200)
                    elif buttons[5].collidepoint(mouse_pos):  # Exit
                        running = False

            elif self.current_screen == "comparison":
                buttons = self.render_comparison_screen()

                # Check for button clicks
                if mouse_clicked:
                    if buttons[0].collidepoint(mouse_pos):  # Play Song 1
                        self.play_song(os.path.join(self.recordings_dir, self.current_song1))
                        self.current_screen = "comparison"  # Return to comparison after playback
                        pygame.time.delay(200)
                    elif buttons[1].collidepoint(mouse_pos):  # Prefer Song 1
                        rating_change = self.update_ranking(self.current_song1, self.current_song2)
                        self.log_message(f"You preferred: {self.current_song1} (Rating +{rating_change:.1f})")
                        # Continue with a new comparison
                        self.run_comparison()
                        pygame.time.delay(200)
                    elif buttons[2].collidepoint(mouse_pos):  # Play Song 2
                        self.play_song(os.path.join(self.recordings_dir, self.current_song2))
                        self.current_screen = "comparison"  # Return to comparison after playback
                        pygame.time.delay(200)
                    elif buttons[3].collidepoint(mouse_pos):  # Prefer Song 2
                        rating_change = self.update_ranking(self.current_song2, self.current_song1)
                        self.log_message(f"You preferred: {self.current_song2} (Rating +{rating_change:.1f})")
                        # Continue with a new comparison
                        self.run_comparison()
                        pygame.time.delay(200)
                    elif buttons[4].collidepoint(mouse_pos):  # Back to Main Menu
                        self.current_screen = "main_menu"
                        pygame.time.delay(200)

            elif self.current_screen == "rankings":
                back_button = self.render_rankings_screen()

                # Check for button clicks
                if mouse_clicked and back_button.collidepoint(mouse_pos):
                    self.current_screen = "main_menu"
                    pygame.time.delay(200)

            elif self.current_screen == "stats":
                back_button = self.render_stats_screen()

                # Check for button clicks
                if mouse_clicked and back_button.collidepoint(mouse_pos):
                    self.current_screen = "main_menu"
                    pygame.time.delay(200)

            elif self.current_screen == "progress":
                back_button = self.render_progress_screen()

                # Check for button clicks
                if mouse_clicked and back_button.collidepoint(mouse_pos):
                    self.current_screen = "main_menu"
                    pygame.time.delay(200)

            # Update the display
            pygame.display.flip()

            # Cap the frame rate
            clock.tick(60)

        pygame.quit()
        print("Thanks for using Song Ranker!")


if __name__ == "__main__":
    app = SongRanker()
    app.run()
