import random

#Sabacc cards are 1-10 both positive and negative
#not ideal way to model I'm sure
postive_cards = [i for i in range(1,11)]*3
negative_cards = [-i for i in range(1,11)]*3

deck = postive_cards + negative_cards
random.shuffle(deck)

#need to create classes
player1 = [deck.pop(), deck.pop()]
player2 = [deck.pop(), deck.pop()]
players = [sum(player1), sum(player2)]

print("Player1 cards: ", player1, ",The hand total is ", sum(player1))
print("Player2 cards: ", player2, ",The hand total is ", sum(player2))

#closest to absolute zero wins
winner = min(players,key=abs)

print(winner)
