import arcade
import random


SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 768
SCREEN_TITLE = "SABACC"

CARD_SCALE = 0.5

CARD_WIDTH = 120 * CARD_SCALE
CARD_HEIGHT = 150 * CARD_SCALE

#how big is the mat we'll place the card on?
MAT_PERCENT_OVERSIZE = 1.98
MAT_HEIGHT = int(CARD_HEIGHT * MAT_PERCENT_OVERSIZE)
MAT_WIDTH = int(CARD_WIDTH * MAT_PERCENT_OVERSIZE)

#how much space do we leave as a gap between the mats?
#done as a percent of the mat size
VERTICAL_MARGIN_PERCENT = 0.5
HORIZONTAL_MARGIN_PERCENT = 1.50

#The Y of the bottom row (2 piles)
BOTTOM_Y = MAT_HEIGHT / 2 + MAT_HEIGHT * VERTICAL_MARGIN_PERCENT

#The x of where to start putting things on the left side
START_X = MAT_WIDTH / 2 + MAT_WIDTH * HORIZONTAL_MARGIN_PERCENT

#the y of the top row (4 piles)
TOP_Y = SCREEN_HEIGHT - MAT_HEIGHT /2 - MAT_HEIGHT * VERTICAL_MARGIN_PERCENT

#the Y of the middle row (7 piles)
MIDDLE_Y = TOP_Y+90 - MAT_HEIGHT - MAT_HEIGHT * VERTICAL_MARGIN_PERCENT

#how far apart each pile goes
X_SPACING = MAT_WIDTH+39 + MAT_WIDTH * VERTICAL_MARGIN_PERCENT

#card constants
CARD_VALUES = ["+1", "+2", "+3", "+4", "+5", "+6", "+7", "+8", "+9", "+10","-1","-2","-3","-4","-5","-6","-7","-8","-9","-10"]
CARD_SUITS = [" Circle", " Square", " Triangle"]

ZERO_VALUE = ["0","0"]
ZERO_SUIT = [" Sylop"]

#if we fan out cards stacked on each other, how far apart to fan them?
CARD_VERTICAL_OFFSET = CARD_HEIGHT * CARD_SCALE * 0.3

FACE_DOWN_IMAGE = "Back.png"

class MyGame(arcade.Window):

    def __init__(self):
        super().__init__(SCREEN_WIDTH,SCREEN_HEIGHT,SCREEN_TITLE)

        self.card_list = None

        arcade.set_background_color(arcade.color.AMAZON)

        #list of cards we are dragging with the mouse
        self.held_cards = None

        #original location of cards we are dragging with the house in case they ahve to go back
        self.held_cards_original_position = None

        #Spirte list with all the mats that cards lay on
        self.pile_mat_list = None


    def setup(self):
        #list of cards we are dragging with the mouse
        self.held_cards = []
        #original location of cards we are dragging the mouse in case they have to go back
        self.held_cards_original_position =[]

        #create the mats the cards go on
        #sprite list with all the mats that the cards lay on
        self.pile_mat_list: arcade.SpriteList = arcade.SpriteList()

        #create the mats for the bottom face down and face up piles
        pile = arcade.SpriteSolidColor(MAT_WIDTH, MAT_HEIGHT, arcade.csscolor.ALICE_BLUE)
        pile.position = START_X, BOTTOM_Y
        self.pile_mat_list.append(pile)

        pile= arcade.SpriteSolidColor(MAT_WIDTH, MAT_HEIGHT, arcade.csscolor.SIENNA)
        pile.position = START_X + X_SPACING, BOTTOM_Y
        self.pile_mat_list.append(pile)

        #Create the seven middle piles
        for i in range(0):
            pile = arcade.SpriteSolidColor(MAT_WIDTH, MAT_HEIGHT, arcade.csscolor.DARK_OLIVE_GREEN)
            pile.position = START_X + i * X_SPACING, MIDDLE_Y
            self.pile_mat_list.append(pile)

        #create the top "play" piles
        for i in range(5):
            pile = arcade.SpriteSolidColor(MAT_WIDTH, MAT_HEIGHT, arcade.csscolor.DARK_OLIVE_GREEN)
            pile.position = START_X + i * X_SPACING, TOP_Y
            self.pile_mat_list.append(pile)

        self.card_list = arcade.SpriteList()

        #create every card
        self.card_list = arcade.SpriteList()
        for card_suit in CARD_SUITS:
            for card_value in CARD_VALUES:
                card = Card(card_suit, card_value, CARD_SCALE)
                card.position = START_X, BOTTOM_Y
                self.card_list.append(card)
        for sylop in ZERO_SUIT:
            for card1 in ZERO_VALUE:
                card = Card(sylop, card1, CARD_SCALE)
                card.position = START_X, BOTTOM_Y
                self.card_list.append(card)



#         for pos1 in range(len(self.card_list)):
#             pos2 = random.randrange(len(self.card_list))
#             self.card_list[pos1], self.card_list[pos2] = self.card_list[pos2], self.card_list[pos1]

    def on_draw(self):
        #render the screen
        #clear the screen
        arcade.start_render()
        #draw the mats the cards go on to
        self.pile_mat_list.draw()
        #draw the cards
        self.card_list.draw()

    def on_mouse_press(self,x,y, button, key_modifiers):
        #called when the user pressed a mouse button
        #get list of cards we've clicked on
        cards = arcade.get_sprites_at_point((x,y), self.card_list)

        #have we clicked on a card?
        if len(cards) > 0:
            #might be a stack of cards, get the top one
            primary_card = cards[-1]

            if primary_card.is_face_down:
                primary_card.face_up()
            else:
                primary_card.face_down()


            #all other cases grab the face up card we are clicking on
            self.held_cards = [primary_card]
            #save the position
            self.held_cards_original_position = [self.held_cards[0].position]
            #put on top in drawing order
            self.pull_to_top(self.held_cards[0])


    def on_mouse_release(self, x: float, y: float, button: int,
                         modifiers: int):
        #if we don't have any cards, who cares
        if len(self.held_cards) == 0:
            return

        #find the closest pile, inc ase we are in contact with more than one
        pile,distance = arcade.get_closest_sprite(self.held_cards[0], self.pile_mat_list)
        reset_position = True

        #see if we are in contact with the closest pile
        if arcade.check_for_collision(self.held_cards[0],pile):
            #for each helf card, move it to the pile we dropped on
            for i, dropped_card in enumerate(self.held_cards):
                #move cards to proper position
                dropped_card.position = pile.center_x, pile.center_y
            #success, don't reset position of your cards
            reset_position = False

            #release on top play pile? and only one card help?
        if reset_position:
            #whereever we weere dropped, it wasn't valid. Reset the each cards position
            #to its original spot
            for pile_index, card in enumerate(self.held_cards):
                card.position = self.held_cards_original_position[pile_index]

        #we are no longer holding cards
        self.held_cards = []


    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        #user moves mouse

        #if we are holding cards, move them with the mouse
        for card in self.held_cards:
            card.center_x += dx
            card.center_y += dy


    def pull_to_top(self, card):
        #pull card to top of rendering order (last to render, looks on top)
        #find the index of the card
        index = self.card_list.index(card)
        #loop and pull the other cards down towards the zero end
        for i in range(index, len(self.card_list)-1):
            self.card_list[i] = self.card_list[i+1]
        #put this card at the right-side/top/size of the list
        self.card_list[len(self.card_list) -1] = card

    def on_key_press(self, symbol: int, modifiers: int):
        #user presses key
        if symbol == arcade.key.R:
            self.setup()


class Card(arcade.Sprite):
    #card sprite
    def __init__(self, suit, value, scale=1):
        #card constructor
        #attributes for suit and value
        self.suit = suit
        self.value = value

        self.image_file_name = f"cards/{self.value}{self.suit}.png"

        self.is_face_up = False

        super().__init__(FACE_DOWN_IMAGE, scale, hit_box_algorithm="None")

    def face_down(self):
        #turn card face down
        self.texture = arcade.load_texture(FACE_DOWN_IMAGE)
        self.is_face_up = True

    def face_up(self):
        #turn card face up
        self.texture = arcade.load_texture(self.image_file_name)
        self.is_face_up = False

    @property
    def is_face_down(self):
        #is this card face down?
        return self.is_face_up


def main():
    window = MyGame()
    window.setup()
    arcade.run()

if __name__=="__main__":
    main()
