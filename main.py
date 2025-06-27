import arcade
import os
import random
import math
import time
from dice import roll_dice  # Import the minimal dice roller

# Window settings
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
SCREEN_TITLE = "Sabacc Deck Test"

# Asset paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(CURRENT_DIR, "..", "assets")
CARD_BACK_IMAGE = os.path.join(ASSETS_DIR, "cards", "Back.png")
BACKGROUND_IMAGE = os.path.join(ASSETS_DIR, "background.png")
DICE_IMAGE_DIR = os.path.join(ASSETS_DIR, "dice")
DICE_IMAGES = [
    os.path.join(DICE_IMAGE_DIR, f"Spike Die {i+1} Holo.png") for i in range(6)
]

# Card constants
CARD_VALUES = ["+1", "+2", "+3", "+4", "+5", "+6", "+7", "+8", "+9", "+10",
               "-1", "-2", "-3", "-4", "-5", "-6", "-7", "-8", "-9", "-10"]
CARD_SUITS = [" Circle", " Square", " Triangle"]
ZERO_VALUE = ["0", "0"]
ZERO_SUIT = [" Sylop"]

CARD_SCALE = 0.25

def card_filename(card_value, card_suit):
    return os.path.join(ASSETS_DIR, "cards", f"{card_value}{card_suit}.png")

class Card(arcade.Sprite):
    def __init__(self, card_value, card_suit, scale):
        filename = card_filename(card_value, card_suit)
        super().__init__(filename, scale)
        self.card_value = card_value
        self.card_suit = card_suit
        self.image_filename = filename
        self.target_x = None
        self.target_y = None
        self.dealing = False
        self.deal_angle = 0
        self.deal_speed = 0
        self.deal_spin = 0

class DeckTestWindow(arcade.Window):
    def __init__(self):
        super().__init__(
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
            SCREEN_TITLE,
            resizable=True
        )
        self.deck = arcade.SpriteList()
        self.movable_cards = arcade.SpriteList()
        self.held_card = None
        self.held_card_offset_x = 0
        self.held_card_offset_y = 0
        self.held_card_origin = None

        self.button_width = 250
        self.button_height = 60
        self.dice_button_w = 180
        self.dice_button_h = 60
        self.reset_w = 180
        self.reset_h = 60

        self.discard_pile = []
        self.player_piles = [[] for _ in range(4)]
        self.deal_queue = []
        self.dealing = False
        self.deal_timer = 0
        self.swap_candidate = False
        self.last_discarded_card = None
        self.previous_discard_top = None
        self.dice_result_text = ""
        self.last_dice = [None, None]  # Store the last dice roll
        self.show_sabacc_shift = False  # Track if "Sabacc Shift" should be shown
        # --- Dice animation state ---
        self.rolling = False
        self.roll_start_time = 0
        self.roll_duration = 1.2
        self.roll_end_result = [1, 1]
        self.roll_stop_times = [0, 0]
        self.roll_intervals = [0.04, 0.04]
        self.roll_next_update = [0, 0]
        self.background = None

        self.card_scale = CARD_SCALE
        self.show_card_resizer = False

        self.round = 1
        self.max_rounds = 3
        self.show_winner = False
        self.winner_text = ""
        # Add a button for "Show Winner"
        self.show_winner_button_w = 220
        self.show_winner_button_h = 60

    def get_dynamic_positions(self):
        margin = 60
        pile_width = int(self.width * 0.08)
        pile_height = int(self.height * 0.175)
        pile_width = max(70, min(pile_width, 140))
        pile_height = max(100, min(pile_height, 200))

        # --- Expand player box width for easier dropping ---
        player_box_extra = int(self.width * 0.15)  # Add 15% of width to each player box
        player_box_width = pile_width + player_box_extra
        player_box_height = pile_height + 30  # Slightly taller too

        button_width = int(self.width * 0.18)
        button_height = int(self.height * 0.075)
        button_width = max(120, min(button_width, 300))
        button_height = max(40, min(button_height, 80))

        dice_button_w = int(self.width * 0.14)
        dice_button_h = button_height
        dice_button_x = self.width - margin - dice_button_w // 2
        dice_button_y = self.height - margin - dice_button_h // 2

        reset_w = button_width
        reset_h = button_height

        button_x = self.width - margin - button_width // 2
        button_y = margin + button_height // 2
        draw_pile_x = button_x
        draw_pile_y = button_y + button_height // 2 + pile_height // 2 + 10

        discard_pile_x = draw_pile_x - pile_width - 40
        discard_pile_y = draw_pile_y

        reset_x = margin + reset_w // 2
        reset_y = margin + reset_h // 2

        player_pile_positions = [
            (self.width // 2, self.height - margin - pile_height // 2),  # Top
            (self.width - margin - pile_width // 2, self.height // 2),   # Right
            (self.width // 2, margin + pile_height // 2 + button_height + 40),  # Bottom
            (margin + pile_width // 2, self.height // 2),                # Left
        ]

        # Add player box sizes to positions dict
        return {
            "pile_width": pile_width,
            "pile_height": pile_height,
            "player_box_width": player_box_width,
            "player_box_height": player_box_height,
            "button_x": button_x,
            "button_y": button_y,
            "button_width": button_width,
            "button_height": button_height,
            "draw_pile_x": draw_pile_x,
            "draw_pile_y": draw_pile_y,
            "discard_pile_x": discard_pile_x,
            "discard_pile_y": discard_pile_y,
            "dice_button_x": dice_button_x,
            "dice_button_y": dice_button_y,
            "dice_button_w": dice_button_w,
            "dice_button_h": dice_button_h,
            "reset_x": reset_x,
            "reset_y": reset_y,
            "reset_w": reset_w,
            "reset_h": reset_h,
            "player_pile_positions": player_pile_positions,
            "show_winner_button_x": self.width - margin - dice_button_w // 2,
            "show_winner_button_y": dice_button_y - dice_button_h // 2 - 40 - self.show_winner_button_h // 2,
            "show_winner_button_w": self.show_winner_button_w,
            "show_winner_button_h": self.show_winner_button_h,
        }

    def setup(self):
        self.deck = arcade.SpriteList()
        deck = []
        for suit in CARD_SUITS:
            for value in CARD_VALUES:
                deck.append(Card(value, suit, CARD_SCALE))
        for sylop in ZERO_SUIT:
            for value in ZERO_VALUE:
                deck.append(Card(value, sylop, CARD_SCALE))
        random.shuffle(deck)
        for card in deck:
            card.center_x = 0
            card.center_y = 0
            self.deck.append(card)
        self.movable_cards = arcade.SpriteList()
        self.held_card = None
        self.held_card_origin = None
        self.player_piles = [[] for _ in range(4)]
        self.deal_queue = []
        self.dealing = False
        self.deal_timer = 0
        self.discard_pile = []
        self.swap_candidate = False
        self.last_discarded_card = None
        self.previous_discard_top = None
        self.dice_result_text = ""
        self.last_dice = [None, None]

        if os.path.exists(BACKGROUND_IMAGE):
            self.background = arcade.load_texture(BACKGROUND_IMAGE)
        else:
            self.background = None

    def reset_deck(self):
        all_cards = []
        for pile in self.player_piles:
            all_cards.extend(pile)
            pile.clear()
        all_cards.extend(self.movable_cards)
        self.movable_cards = arcade.SpriteList()
        all_cards.extend(self.discard_pile)
        self.discard_pile.clear()
        all_cards.extend(self.deck)
        self.deck = arcade.SpriteList()
        random.shuffle(all_cards)
        for card in all_cards:
            card.center_x = 0
            card.center_y = 0
            card.angle = 0
        self.deck.extend(all_cards)
        self.held_card = None
        self.held_card_origin = None
        self.deal_queue = []
        self.dealing = False
        self.swap_candidate = False
        self.last_discarded_card = None
        self.previous_discard_top = None
        self.dice_result_text = ""
        self.last_dice = [None, None]
        self.round = 1
        self.show_winner = False
        self.winner_text = ""

    def get_card_value(self, card):
        try:
            return int(card.card_value)
        except Exception:
            return 0

    def get_player_score(self, player_index):
        hand = self.player_piles[player_index]
        score = sum(self.get_card_value(card) for card in hand)
        sylop_zeros = [card for card in hand if card.card_value == "0" and card.card_suit == " Sylop"]
        if len(sylop_zeros) == 2:
            return "Pure Sabacc"
        elif score == 0 and len(hand) > 0:
            return "Sabacc"
        else:
            return score

    def on_draw(self):
        arcade.start_render()
        # Draw background if available
        if self.background:
            arcade.draw_lrwh_rectangle_textured(
                0, 0, self.width, self.height, self.background
            )
        pos = self.get_dynamic_positions()
        pile_width = pos["pile_width"]
        pile_height = pos["pile_height"]
        player_box_width = pos["player_box_width"]
        player_box_height = pos["player_box_height"]

        # --- Draw expanded transparent player boxes BEFORE cards ---
        for i, (x, y) in enumerate(pos["player_pile_positions"]):
            arcade.draw_rectangle_filled(
                x, y, player_box_width, player_box_height,
                (*arcade.color.LIGHT_GREEN, 40)
            )

        # Draw discard pile area (rectangle)
        pre_discard_offset = -pile_width // 2
        pre_discard_x = pos["discard_pile_x"] + pre_discard_offset
        pre_discard_y = pos["discard_pile_y"]

        arcade.draw_rectangle_outline(
            pos["discard_pile_x"], pos["discard_pile_y"], pile_width, pile_height, arcade.color.LIGHT_GRAY, 3
        )
        arcade.draw_text("Discard", pos["discard_pile_x"] - 40, pos["discard_pile_y"] + pile_height // 2 + 10, arcade.color.LIGHT_GRAY, 16)

        # Draw top card of discard pile face up, if any
        if self.discard_pile:
            if (
                self.swap_candidate
                and self.last_discarded_card in self.discard_pile
                and self.previous_discard_top is not None
            ):
                if self.previous_discard_top and self.previous_discard_top in self.discard_pile:
                    self.previous_discard_top.alpha = 255
                    self.previous_discard_top.center_x = pos["discard_pile_x"]
                    self.previous_discard_top.center_y = pos["discard_pile_y"]
                    self.previous_discard_top.angle = 0
                    self.previous_discard_top.draw()
                self.last_discarded_card.alpha = 128
                self.last_discarded_card.center_x = pre_discard_x
                self.last_discarded_card.center_y = pre_discard_y
                self.last_discarded_card.angle = 0
                self.last_discarded_card.draw()
                self.last_discarded_card.alpha = 255
                self.last_discarded_card.center_x = pos["discard_pile_x"]
            else:
                self.discard_pile[-1].alpha = 255
                self.discard_pile[-1].center_x = pos["discard_pile_x"]
                self.discard_pile[-1].center_y = pos["discard_pile_y"]
                self.discard_pile[-1].angle = 0
                self.discard_pile[-1].draw()
        # Draw draw pile as card back
        arcade.draw_texture_rectangle(
            pos["draw_pile_x"],
            pos["draw_pile_y"],
            pile_width,
            pile_height,
            arcade.load_texture(CARD_BACK_IMAGE)
        )
        # Draw all cards that have been drawn and placed
        self.movable_cards.draw()
        # Draw player piles (cards in each pile)
        for i, pile in enumerate(self.player_piles):
            pile_center_x, pile_center_y = pos["player_pile_positions"][i]
            num_cards = len(pile)
            base_spacing = int(pile_width * 0.5)
            hand_width = (num_cards - 1) * base_spacing if num_cards > 1 else 0

            if i == 1:
                rightmost_x = pile_center_x + hand_width // 2
                overflow = max(0, rightmost_x + pile_width // 2 - self.width)
                shift = overflow if overflow > 0 else 0
                start_x = pile_center_x + hand_width // 2 - shift
                for idx, card in enumerate(pile):
                    if not getattr(card, "dealing", False):
                        card.center_x = start_x - idx * base_spacing
                        card.center_y = pile_center_y
                    card.draw()
            elif i == 3:
                leftmost_x = pile_center_x - hand_width // 2
                overflow = max(0, pile_width // 2 - leftmost_x)
                shift = overflow if overflow > 0 else 0
                start_x = pile_center_x - hand_width // 2 + shift
                for idx, card in enumerate(pile):
                    if not getattr(card, "dealing", False):
                        card.center_x = start_x + idx * base_spacing
                        card.center_y = pile_center_y
                    card.draw()
            else:
                start_x = pile_center_x - hand_width // 2
                for idx, card in enumerate(pile):
                    if not getattr(card, "dealing", False):
                        card.center_x = start_x + idx * base_spacing
                        card.center_y = pile_center_y
                    card.draw()

        # --- Draw player name and score overlays (after cards) ---
        for i, (x, y) in enumerate(pos["player_pile_positions"]):
            # Translucent background for player name
            name_bg_w, name_bg_h = 110, 32
            name_bg_x = x
            name_bg_y = y + pile_height // 2 + 26
            arcade.draw_rectangle_filled(
                name_bg_x, name_bg_y, name_bg_w, name_bg_h, (30, 60, 30, 180)
            )
            arcade.draw_text(f"Player {i+1}", x - 40, name_bg_y - 12, arcade.color.LIGHT_GREEN, 16)

            # Score text and background
            score = self.get_player_score(i)
            if score == "Pure Sabacc":
                score_text = "Pure Sabacc!"
                score_color = arcade.color.GOLD
            elif score == "Sabacc":
                score_text = "Sabacc!"
                score_color = arcade.color.BRIGHT_GREEN
            else:
                score_text = f"Score: {score}"
                score_color = arcade.color.YELLOW_ORANGE if isinstance(score, int) and score >= 0 else arcade.color.RED

            # --- Make the score background wider for long negative numbers ---
            score_bg_w, score_bg_h = 210, 44
            score_bg_x = x
            score_bg_y = y - pile_height // 2 - 18
            arcade.draw_rectangle_filled(
                score_bg_x, score_bg_y, score_bg_w, score_bg_h, (30, 60, 30, 180)
            )
            arcade.draw_text(
                score_text,
                x - score_bg_w // 2 + 10,
                score_bg_y - 14,
                score_color,
                22,
                width=score_bg_w - 20,
                align="center",
                bold=True,
                font_name="Arial"
            )
        # Info
        arcade.draw_text(f"Cards left in pile: {len(self.deck)}", 20, self.height - 40, arcade.color.WHITE, 20)
        arcade.draw_text("Click the pile to draw a card. Drag to move.", 20, self.height - 70, arcade.color.AQUA, 18)
        # Deal button
        color = arcade.color.DARK_BLUE if not self.dealing else arcade.color.GRAY
        arcade.draw_rectangle_filled(pos["button_x"], pos["button_y"], pos["button_width"], pos["button_height"], color)
        arcade.draw_text(
            "Deal Cards",
            pos["button_x"] - 70,
            pos["button_y"] - 18,
            arcade.color.WHITE,
            28,
        )
        if self.dealing:
            arcade.draw_text("Dealing...", pos["button_x"] - 60, pos["button_y"] + 50, arcade.color.YELLOW, 22)
        # Draw reset button
        arcade.draw_rectangle_filled(pos["reset_x"], pos["reset_y"], pos["reset_w"], pos["reset_h"], arcade.color.DARK_RED)
        arcade.draw_text("Reset Deck", pos["reset_x"] - 70, pos["reset_y"] - 18, arcade.color.WHITE, 28)
        # Draw Roll Dice button
        arcade.draw_rectangle_filled(pos["dice_button_x"], pos["dice_button_y"], pos["dice_button_w"], pos["dice_button_h"], arcade.color.DARK_GREEN)
        arcade.draw_text("Roll Dice", pos["dice_button_x"] - 60, pos["dice_button_y"] - 18, arcade.color.WHITE, 28)
        if self.dice_result_text:
            arcade.draw_text(self.dice_result_text, pos["dice_button_x"] - 60, pos["dice_button_y"] + 40, arcade.color.YELLOW, 22)

        # --- Draw dice images in the center of the window with animation ---
        if self.last_dice[0] is not None and self.last_dice[1] is not None:
            dice_size = 96
            center_x = self.width // 2
            center_y = self.height // 2
            offset = 70
            box_w = dice_size * 2 + 40
            box_h = dice_size + 40
            # Draw translucent background box behind dice
            arcade.draw_rectangle_filled(center_x, center_y, box_w, box_h, (30, 30, 30, 180))
            # Draw dice (animated if rolling)
            for i, die in enumerate(self.last_dice):
                if die is not None and 1 <= die <= 6:
                    dx = center_x + (i * 2 - 1) * offset
                    arcade.draw_texture_rectangle(
                        dx, center_y, dice_size, dice_size,
                        arcade.load_texture(DICE_IMAGES[die - 1])
                    )
            # Draw "Sabacc Shift" above dice if needed
            if self.show_sabacc_shift and not self.rolling:
                msg = "Sabacc Shift"
                msg_w = 320
                msg_h = 54
                msg_x = center_x
                msg_y = center_y + dice_size // 2 + 40
                arcade.draw_rectangle_filled(
                    msg_x, msg_y, msg_w, msg_h, (30, 30, 30, 200)
                )
                arcade.draw_text(
                    msg,
                    msg_x - msg_w // 2 + 10, msg_y - 22,
                    arcade.color.GOLD,
                    32,
                    width=msg_w - 20,
                    align="center",
                    bold=True,
                    font_name="Arial"
                )

        # Card resizer overlay (like in game.py)
        if self.show_card_resizer:
            box_w, box_h = 340, 180
            box_x, box_y = self.width // 2, self.height // 2
            arcade.draw_rectangle_filled(box_x, box_y, box_w, box_h, arcade.color.DARK_SLATE_GRAY + (220,))
            arcade.draw_rectangle_outline(box_x, box_y, box_w, box_h, arcade.color.WHITE, 3)
            arcade.draw_text("Card Size", box_x - 60, box_y + 40, arcade.color.WHITE, 24)
            # Draw slider
            slider_x = box_x - 100
            slider_y = box_y
            slider_w = 200
            slider_h = 8
            arcade.draw_rectangle_filled(slider_x + slider_w // 2, slider_y, slider_w, slider_h, arcade.color.LIGHT_GRAY)
            # Slider handle
            min_scale = 0.12
            max_scale = 0.45
            handle_x = slider_x + int((self.card_scale - min_scale) / (max_scale - min_scale) * slider_w)
            arcade.draw_circle_filled(handle_x, slider_y, 14, arcade.color.YELLOW_ORANGE)
            arcade.draw_text(f"{self.card_scale:.2f}", box_x + 60, box_y - 10, arcade.color.WHITE, 20)
            arcade.draw_text("Press I to close", box_x - 60, box_y - 60, arcade.color.LIGHT_GRAY, 16)

        # --- Draw round counter at top left, but lower so it doesn't cover "cards left" ---
        round_text = f"Round: {self.round} / {self.max_rounds}"
        round_box_w = 180
        round_box_h = 44
        round_box_x = 30 + round_box_w // 2
        # Move the round counter down by about 100 pixels from the top
        round_box_y = self.height - 130 - round_box_h // 2
        arcade.draw_rectangle_filled(
            round_box_x, round_box_y, round_box_w, round_box_h, (30, 30, 30, 200)
        )
        arcade.draw_text(
            round_text,
            round_box_x - round_box_w // 2 + 10, round_box_y - 16,
            arcade.color.YELLOW, 26, width=round_box_w - 20, align="center", bold=True
        )

        # --- Draw "Show Winner" button at end of round 3 ---
        if self.round > self.max_rounds or self.show_winner:
            arcade.draw_rectangle_filled(
                pos["show_winner_button_x"], pos["show_winner_button_y"],
                pos["show_winner_button_w"], pos["show_winner_button_h"],
                arcade.color.DARK_ORANGE
            )
            arcade.draw_text(
                "Show Winner",
                pos["show_winner_button_x"] - 90, pos["show_winner_button_y"] - 18,
                arcade.color.WHITE, 28
            )

        # --- Draw winner text if available ---
        if self.show_winner and self.winner_text:
            winner_box_w = 700
            winner_box_h = 120
            winner_box_x = self.width // 2
            winner_box_y = self.height // 2 + 200
            arcade.draw_rectangle_filled(
                winner_box_x, winner_box_y, winner_box_w, winner_box_h, (30, 30, 30, 230)
            )
            arcade.draw_text(
                self.winner_text,
                winner_box_x - winner_box_w // 2 + 30, winner_box_y - 38,
                arcade.color.GOLD, 38, width=winner_box_w - 60, align="center", bold=True
            )

        # ...rest of on_draw...

    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.I:
            self.show_card_resizer = not self.show_card_resizer

    def on_mouse_press(self, x, y, button, modifiers):
        pos = self.get_dynamic_positions()
        # Card resizer slider logic
        if self.show_card_resizer:
            box_x, box_y = self.width // 2, self.height // 2
            slider_x = box_x - 100
            slider_y = box_y
            slider_w = 200
            min_scale = 0.12
            max_scale = 0.45
            if slider_y - 20 < y < slider_y + 20 and slider_x < x < slider_x + slider_w:
                rel = (x - slider_x) / slider_w
                self.card_scale = min_scale + rel * (max_scale - min_scale)
                self.card_scale = max(min_scale, min(self.card_scale, max_scale))
                # Update all cards' scale
                for card in self.deck:
                    card.scale = self.card_scale
                for card in self.movable_cards:
                    card.scale = self.card_scale
                for pile in self.player_piles:
                    for card in pile:
                        card.scale = self.card_scale
                for card in self.discard_pile:  # <-- Add this line
                    card.scale = self.card_scale
                return
            # Don't interact with rest of UI while resizer is open
            return

        # --- Hide dice if dice are clicked after rolling and not animating ---
        if (
            self.last_dice[0] is not None and self.last_dice[1] is not None
            and not self.rolling
        ):
            dice_size = 96
            center_x = self.width // 2
            center_y = self.height // 2
            box_w = dice_size * 2 + 40
            box_h = dice_size + 40
            if (
                center_x - box_w // 2 < x < center_x + box_w // 2
                and center_y - box_h // 2 < y < center_y + box_h // 2
            ):
                self.last_dice = [None, None]
                self.show_sabacc_shift = False
                self.dice_result_text = ""
                return

        # --- Swap logic after discard ---
        if self.swap_candidate:
            pile_width = pos["pile_width"]
            pile_height = pos["pile_height"]
            if (
                pos["discard_pile_x"] - pile_width // 2 < x < pos["discard_pile_x"] + pile_width // 2
                and pos["discard_pile_y"] - pile_height // 2 < y < pos["discard_pile_y"] + pile_height // 2
                and self.previous_discard_top is not None
            ):
                if self.previous_discard_top in self.discard_pile:
                    self.discard_pile.remove(self.previous_discard_top)
                self.movable_cards.append(self.previous_discard_top)
                self.held_card = self.previous_discard_top
                self.held_card_offset_x = 0
                self.held_card_offset_y = 0
                self.held_card_origin = "discard"
                self.swap_candidate = False
                self.previous_discard_top = None
                return
            if (
                pos["draw_pile_x"] - pile_width // 2 < x < pos["draw_pile_x"] + pile_width // 2
                and pos["draw_pile_y"] - pile_height // 2 < y < pos["draw_pile_y"] + pile_height // 2
                and len(self.deck) > 0
            ):
                card = self.deck.pop()
                card.center_x = x
                card.center_y = y
                self.movable_cards.append(card)
                self.held_card = card
                self.held_card_offset_x = 0
                self.held_card_offset_y = 0
                self.held_card_origin = "draw"
                self.swap_candidate = False
                self.previous_discard_top = None
                return
            self.swap_candidate = False
            self.previous_discard_top = None
            return

        # Roll Dice button
        if (
            pos["dice_button_x"] - pos["dice_button_w"] // 2 < x < pos["dice_button_x"] + pos["dice_button_w"] // 2
            and pos["dice_button_y"] - pos["dice_button_h"] // 2 < y < pos["dice_button_y"] + pos["dice_button_h"] // 2
        ):
            self.roll_dice_and_shift()
            return

        # Deal button
        if (
            pos["button_x"] - pos["button_width"] // 2 < x < pos["button_x"] + pos["button_width"] // 2
            and pos["button_y"] - pos["button_height"] // 2 < y < pos["button_y"] + pos["button_height"] // 2
            and not self.dealing
        ):
            self.start_deal_animation()
            return
        # Try to pick up a movable card
        for card in reversed(self.movable_cards):
            if card.collides_with_point((x, y)):
                self.held_card = card
                self.held_card_offset_x = card.center_x - x
                self.held_card_offset_y = card.center_y - y
                self.held_card_origin = "table"
                return
        # Try to pick up a card from any player hand
        for i, pile in enumerate(self.player_piles):
            for card in reversed(pile):
                if card.collides_with_point((x, y)):
                    self.held_card = card
                    self.held_card_offset_x = card.center_x - x
                    self.held_card_offset_y = card.center_y - y
                    pile.remove(card)
                    self.movable_cards.append(card)
                    self.held_card_origin = "hand"
                    return
        # Allow drawing from pile at any time (Gain)
        pile_width = pos["pile_width"]
        pile_height = pos["pile_height"]
        if (
            self.held_card is None
            and len(self.deck) > 0
            and not self.dealing
        ):
            if (
                pos["draw_pile_x"] - pile_width // 2 < x < pos["draw_pile_x"] + pile_width // 2
                and pos["draw_pile_y"] - pile_height // 2 < y < pos["draw_pile_y"] + pile_height // 2
            ):
                card = self.deck.pop()
                card.center_x = x
                card.center_y = y
                self.movable_cards.append(card)
                self.held_card = card
                self.held_card_offset_x = 0
                self.held_card_offset_y = 0
                self.held_card_origin = "draw"
        # Reset button
        if (
            pos["reset_x"] - pos["reset_w"] // 2 < x < pos["reset_x"] + pos["reset_w"] // 2
            and pos["reset_y"] - pos["reset_h"] // 2 < y < pos["reset_y"] + pos["reset_h"] // 2
        ):
            self.reset_deck()
            return

        # --- Show Winner button logic ---
        if (
            (self.round > self.max_rounds or self.show_winner)
            and pos["show_winner_button_x"] - pos["show_winner_button_w"] // 2 < x < pos["show_winner_button_x"] + pos["show_winner_button_w"] // 2
            and pos["show_winner_button_y"] - pos["show_winner_button_h"] // 2 < y < pos["show_winner_button_y"] + pos["show_winner_button_h"] // 2
        ):
            self.show_winner = True
            self.winner_text = self.get_winner_text()
            return

    def roll_dice_and_shift(self):
        # Start dice animation
        self.rolling = True
        self.roll_start_time = time.time()
        self.roll_duration = random.uniform(1.0, 1.7)
        self.roll_end_result = [random.randint(1, 6), random.randint(1, 6)]
        self.roll_stop_times = [
            self.roll_start_time + self.roll_duration + random.uniform(0, 0.2),
            self.roll_start_time + self.roll_duration + random.uniform(0, 0.2)
        ]
        self.roll_intervals = [0.04, 0.04]
        self.roll_next_update = [self.roll_start_time, self.roll_start_time]
        self.last_dice = [random.randint(1, 6), random.randint(1, 6)]
        self.show_sabacc_shift = False
        self.dice_result_text = ""

    def on_update(self, delta_time):
        # Animate dice rolling
        if self.rolling:
            now = time.time()
            for i in range(2):
                elapsed = now - self.roll_start_time
                total = self.roll_stop_times[i] - self.roll_start_time
                t = min(max(elapsed / total, 0), 1)
                self.roll_intervals[i] = 0.04 + t * 0.18 * random.uniform(0.9, 1.1)
                if now >= self.roll_stop_times[i]:
                    self.last_dice[i] = self.roll_end_result[i]
                elif now >= self.roll_next_update[i]:
                    self.last_dice[i] = random.randint(1, 6)
                    self.roll_next_update[i] = now + self.roll_intervals[i]
            if now >= max(self.roll_stop_times):
                self.rolling = False
                die1, die2 = self.roll_end_result
                self.dice_result_text = f"Dice: {die1}, {die2}"
                self.show_sabacc_shift = (die1 == die2)
                # Only do Sabacc Shift logic after animation
                if die1 == die2:
                    hand_sizes = []
                    for pile in self.player_piles:
                        hand_sizes.append(len(pile))
                        while pile:
                            card = pile.pop()
                            self.discard_pile.append(card)
                    for i, pile in enumerate(self.player_piles):
                        num_cards = hand_sizes[i]
                        for _ in range(num_cards):
                            if len(self.deck) == 0:
                                if self.discard_pile:
                                    self.deck.extend(self.discard_pile)
                                    self.discard_pile.clear()
                                    random.shuffle(self.deck)
                                else:
                                    break
                            if len(self.deck) > 0:
                                card = self.deck.pop()
                                card.center_x, card.center_y = self.get_dynamic_positions()["player_pile_positions"][i]
                                pile.append(card)
                # --- Advance round after dice roll ---
                if self.round <= self.max_rounds:
                    self.round += 1

        # --- Card dealing animation ---
        if self.dealing and self.deal_queue:
            card, player = self.deal_queue[0]
            dx = card.target_x - card.center_x
            dy = card.target_y - card.center_y
            dist = math.hypot(dx, dy)
            if dist < card.deal_speed:
                card.center_x = card.target_x
                card.center_y = card.target_y
                card.angle = 0
                card.dealing = False
                self.player_piles[player].append(card)
                self.deal_queue.pop(0)
            else:
                card.center_x += math.cos(card.deal_angle) * card.deal_speed
                card.center_y += math.sin(card.deal_angle) * card.deal_speed
                card.angle += card.deal_spin
        elif self.dealing and not self.deal_queue:
            self.dealing = False

    def on_mouse_release(self, x, y, button, modifiers):
        pos = self.get_dynamic_positions()
        if self.held_card:
            card = self.held_card
            card_area = card.width * card.height
            snapped = False

            # --- Discard pile logic (use original pile size) ---
            pile_width = pos["pile_width"]
            pile_height = pos["pile_height"]
            pile_left = pos["discard_pile_x"] - pile_width // 2
            pile_right = pos["discard_pile_x"] + pile_width // 2
            pile_bottom = pos["discard_pile_y"] - pile_height // 2
            pile_top = pos["discard_pile_y"] + pile_height // 2
            overlap_left = max(card.left, pile_left)
            overlap_right = min(card.right, pile_right)
            overlap_bottom = max(card.bottom, pile_bottom)
            overlap_top = min(card.top, pile_top)
            if (
                overlap_right > overlap_left and overlap_top > overlap_bottom
                and self.held_card_origin != "discard"
            ):
                overlap_area = (overlap_right - overlap_left) * (overlap_top - overlap_bottom)
                if overlap_area > 0.5 * card_area:
                    if self.discard_pile:
                        self.previous_discard_top = self.discard_pile[-1]
                    else:
                        self.previous_discard_top = None
                    card.center_x = pos["discard_pile_x"]
                    card.center_y = pos["discard_pile_y"]
                    card.angle = 0
                    self.discard_pile.append(card)
                    if card in self.movable_cards:
                        self.movable_cards.remove(card)
                    for pile in self.player_piles:
                        if card in pile:
                            pile.remove(card)
                    self.swap_candidate = len(self.discard_pile) > 1
                    self.last_discarded_card = card
                    snapped = True
            if snapped:
                self.held_card = None
                self.held_card_origin = None
                return

            # --- Player pile logic (use expanded box) ---
            player_box_width = pos["player_box_width"]
            player_box_height = pos["player_box_height"]
            for i, pile in enumerate(self.player_piles):
                px, py = pos["player_pile_positions"][i]
                pile_left = px - player_box_width // 2
                pile_right = px + player_box_width // 2
                pile_bottom = py - player_box_height // 2
                pile_top = py + player_box_height // 2
                overlap_left = max(card.left, pile_left)
                overlap_right = min(card.right, pile_right)
                overlap_bottom = max(card.bottom, pile_bottom)
                overlap_top = min(card.top, pile_top)
                if overlap_right > overlap_left and overlap_top > overlap_bottom:
                    overlap_area = (overlap_right - overlap_left) * (overlap_top - overlap_bottom)
                    if overlap_area > 0.5 * card_area:
                        idx = len(self.player_piles[i])
                        card.center_x, card.center_y = pos["player_pile_positions"][i]
                        card.center_x += idx * (pos["pile_width"] // 2) - (pos["pile_width"] // 4)
                        card.angle = 0
                        self.player_piles[i].append(card)
                        if card in self.movable_cards:
                            self.movable_cards.remove(card)
                        snapped = True
                        break
            self.held_card = None
            self.held_card_origin = None

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self.held_card:
            self.held_card.center_x = x + self.held_card_offset_x
            self.held_card.center_y = y + self.held_card_offset_y

    def start_deal_animation(self):
        pos = self.get_dynamic_positions()
        self.deal_queue = []

        # If all hands are empty, deal 2 cards (start of game), else deal 1 card to each
        if all(len(pile) == 0 for pile in self.player_piles):
            rounds = 2
        else:
            rounds = 1

        for round in range(rounds):
            for player in range(4):
                if len(self.deck) > 0:
                    card = self.deck.pop()
                    card.center_x = pos["draw_pile_x"]
                    card.center_y = pos["draw_pile_y"]
                    card.angle = 0
                    card.dealing = True
                    card.target_x, card.target_y = pos["player_pile_positions"][player]
                    card.target_x += (len(self.player_piles[player]) + round) * (pos["pile_width"] // 2) - (pos["pile_width"] // 4)
                    card.deal_angle = math.atan2(card.target_y - card.center_y, card.target_x - card.center_x)
                    card.deal_speed = 30
                    card.deal_spin = random.choice([-10, 10])
                    self.deal_queue.append((card, player))
        self.dealing = True
        self.deal_timer = 0

    def get_winner_text(self):
        # Returns a string announcing the winner(s) according to Sabacc rules
        best_score = None
        best_player = []
        best_is_pure_sabacc = False
        best_is_sabacc = False
        best_card_count = None

        for i, hand in enumerate(self.player_piles):
            # Check for Pure Sabacc (two sylops)
            sylop_zeros = [card for card in hand if card.card_value == "0" and card.card_suit == " Sylop"]
            if len(sylop_zeros) == 2:
                # Pure Sabacc beats everything
                if not best_is_pure_sabacc:
                    best_player = [i]
                    best_is_pure_sabacc = True
                else:
                    best_player.append(i)
                continue
            if best_is_pure_sabacc:
                continue  # Only compare Pure Sabacc hands

            # Check for Sabacc (total 0)
            score = sum(self.get_card_value(card) for card in hand)
            if score == 0 and len(hand) > 0:
                if not best_is_sabacc:
                    best_player = [i]
                    best_is_sabacc = True
                    best_card_count = len(hand)
                elif len(hand) < best_card_count:
                    best_player = [i]
                    best_card_count = len(hand)
                elif len(hand) == best_card_count:
                    best_player.append(i)
                continue
            if best_is_sabacc:
                continue  # Only compare Sabacc hands

            # Otherwise, closest to zero, favoring positive values
            abs_score = abs(score)
            is_positive = score >= 0
            if best_score is None:
                best_score = (abs_score, not is_positive)  # not is_positive: False < True, so positive wins ties
                best_player = [i]
            else:
                if (abs_score, not is_positive) < best_score:
                    best_score = (abs_score, not is_positive)
                    best_player = [i]
                elif (abs_score, not is_positive) == best_score:
                    best_player.append(i)

        if best_is_pure_sabacc:
            if len(best_player) == 1:
                return f"Player {best_player[0]+1} wins with Pure Sabacc!"
            else:
                return f"Players {', '.join(str(p+1) for p in best_player)} tie with Pure Sabacc!"
        elif best_is_sabacc:
            if len(best_player) == 1:
                return f"Player {best_player[0]+1} wins with Sabacc!"
            else:
                return f"Players {', '.join(str(p+1) for p in best_player)} tie with Sabacc!"
        else:
            if len(best_player) == 1:
                hand = self.player_piles[best_player[0]]
                score = sum(self.get_card_value(card) for card in hand)
                return f"Player {best_player[0]+1} wins with {score:+d}!"
            else:
                scores = [sum(self.get_card_value(card) for card in self.player_piles[p]) for p in best_player]
                return f"Players {', '.join(str(p+1) for p in best_player)} tie with {', '.join(str(s) for s in scores)}!"

def main():
    window = DeckTestWindow()
    window.setup()
    arcade.run()

if __name__ == "__main__":
    main()
