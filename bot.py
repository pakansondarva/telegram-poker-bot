!pip install python-telegram-bot==13.7
import random
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext

TOKEN = "8052520477:AAGB_MHDhgdWI5omRw_jHYbkPuo2ZVVm5C0"

# Game State
players = {}
game_active = False
community_cards = []
deck = []
current_turn = None
pot = 0
minimum_bet = 500

# Poker Deck
RANKS = "23456789TJQKA"
SUITS = "♠️♥️♦️♣️"
DECK = [r + s for r in RANKS for s in SUITS]

# Initialize Logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Welcome to Telegram Poker! Type /join to enter the game.")

def join(update: Update, context: CallbackContext):
    """Players join the game."""
    global game_active

    if game_active:
        update.message.reply_text("A game is already in progress. Please wait for the next round.")
        return

    player_id = update.message.from_user.id
    player_name = update.message.from_user.first_name

    if player_id not in players:
        players[player_id] = {"name": player_name, "hand": [], "chips": 100000, "bet": 0}
        update.message.reply_text(f"{player_name} joined the game! Type /startgame when everyone has joined.")

def start_game(update: Update, context: CallbackContext):
    """Starts the game by dealing hands."""
    global game_active, deck, community_cards, current_turn, pot
    if len(players) < 2:
        update.message.reply_text("Need at least 2 players to start the game.")
        return

    game_active = True
    deck = DECK.copy()
    random.shuffle(deck)
    community_cards = []
    pot = 0

    # Deal two cards to each player
    for player_id in players:
        players[player_id]["hand"] = [deck.pop(), deck.pop()]
        players[player_id]["bet"] = 0  # Reset bets

    current_turn = list(players.keys())[0]  # First player starts

    update.message.reply_text("Game started! Dealing cards...")

    # Show each player their hand privately
    for player_id, player in players.items():
        context.bot.send_message(chat_id=player_id, text=f"Your hand: {player['hand'][0]}, {player['hand'][1]}")

    notify_players(update, context, f"{players[current_turn]['name']}'s turn. Choose an action.")

    send_turn_buttons(update, context)

def send_turn_buttons(update: Update, context: CallbackContext):
    """Send buttons for the current player to take action."""
    if not current_turn:
        return

    keyboard = [
        [InlineKeyboardButton("Check", callback_data="check"),
         InlineKeyboardButton("Bet 500", callback_data="bet_500"),
         InlineKeyboardButton("Fold", callback_data="fold")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=current_turn, text="Your turn! Choose an action:", reply_markup=reply_markup)

def button_handler(update: Update, context: CallbackContext):
    """Handles button clicks."""
    global current_turn, pot

    query = update.callback_query
    user_id = query.from_user.id

    if user_id != current_turn:
        query.answer("Not your turn!")
        return

    action = query.data
    player_name = players[user_id]["name"]

    if action == "check":
        notify_players(update, context, f"{player_name} checked.")
    elif action == "bet_500":
        if players[user_id]["chips"] >= minimum_bet:
            players[user_id]["chips"] -= minimum_bet
            players[user_id]["bet"] += minimum_bet
            pot += minimum_bet
            notify_players(update, context, f"{player_name} bet 500 chips. Pot: {pot}")
        else:
            query.answer("Not enough chips!")
            return
    elif action == "fold":
        del players[user_id]
        notify_players(update, context, f"{player_name} folded.")

    next_turn(update, context)

def next_turn(update: Update, context: CallbackContext):
    """Switches to the next player in turn."""
    global current_turn

    if len(players) == 1:
        declare_winner(update, context)
        return

    player_ids = list(players.keys())
    current_index = player_ids.index(current_turn)
    current_turn = player_ids[(current_index + 1) % len(player_ids)]

    notify_players(update, context, f"{players[current_turn]['name']}'s turn.")
    send_turn_buttons(update, context)

def notify_players(update: Update, context: CallbackContext, message: str):
    """Sends updates to all players."""
    for player_id in players:
        context.bot.send_message(chat_id=player_id, text=message)

def declare_winner(update: Update, context: CallbackContext):
    """Declares a winner and resets the game."""
    global game_active, current_turn

    if not players:
        update.message.reply_text("All players folded. No winner.")
        reset_game()
        return

    winner = random.choice(list(players.keys()))
    players[winner]["chips"] += pot

    notify_players(update, context, f"🏆 {players[winner]['name']} wins the round! 🏆\nTotal Chips: {players[winner]['chips']}")
    reset_game()

def reset_game():
    """Resets game state."""
    global game_active, current_turn, community_cards, pot
    game_active = False
    current_turn = None
    community_cards = []
    pot = 0
    for player_id in players:
        players[player_id]["bet"] = 0  # Reset bets

def exit_game(update: Update, context: CallbackContext):
    """Removes a player from the game."""
    player_id = update.message.from_user.id
    if player_id in players:
        del players[player_id]
        update.message.reply_text(f"{update.message.from_user.first_name} has exited the game.")

    if len(players) < 2:
        notify_players(update, context, "Game ended due to insufficient players.")
        reset_game()

def main():
    """Start the bot."""
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Commands
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("join", join))
    dispatcher.add_handler(CommandHandler("startgame", start_game))
    dispatcher.add_handler(CommandHandler("exit", exit_game))

    # Button Handler
    dispatcher.add_handler(CallbackQueryHandler(button_handler))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
