# -*- coding: utf-8 -*-

from telegram.parsemode import ParseMode
from telegram import ForceReply,Bot
import blackjack.errors as errors
from blackjack.game import BlackJackGame
from blackjackbot.commands.util import html_mention, get_game_keyboard, get_join_keyboard, get_start_keyboard, remove_inline_keyboard
from blackjackbot.commands.util.decorators import needs_active_game
from blackjackbot.errors import NoActiveGameException
from blackjackbot.gamestore import GameStore
from blackjackbot.lang import Translator
from blackjackbot.util import get_cards_string
from database import Database
from .functions import create_game, players_turn, next_player, is_button_affiliated
from blackjackbot.util.userstate import UserState
from telethon import TelegramClient, events
import config,requests


def start_cmd(update, context):
    """Handles messages contianing the /start command. Starts a game for a specific user"""
    user = update.effective_user
    chat = update.effective_chat
    lang_id = Database().get_lang_id(chat.id)
    translator = Translator(lang_id=lang_id)

    Database().add_user(user.id, user.language_code, user.first_name, user.last_name, user.username)

    try:
        GameStore().get_game(update.effective_chat.id)
        # TODO notify user that there is a running game already?
        update.effective_message.reply_text("There is a game already running stop it using this command /stop")
    except NoActiveGameException:
        # If there is no game, we create one
        #create_game(update, context)
        balance = Database().get_balance(user.id)
        if balance > 0:
            context.user_data["state"] = UserState.BETTING
            update.effective_message.reply_text("Your balance is "+str(balance)+"sats \nPlease send the amount you want to bet in sats:", reply_markup=ForceReply())            
        else:
            update.effective_message.reply_text("please deposit some sats by using the command /deposit <amount in sats>")

def bet_amount(update, context):
    #update.message.reply_text("kkkkkk")
        # Only handle the message, if the user is currently in the "betting" state
    if context.user_data.get("state", None) != UserState.BETTING:
        return

    user = update.effective_user
    chat = update.effective_chat
    balance = Database().get_balance(user.id) 
    text = update.effective_message.text
    try:
        string_int = int(text)
        if string_int<0:
            update.message.reply_text("the amount is not acceptable please send a correct amount:")
            return
        # not more than 100 webd to bet
        if string_int>10000:
            update.message.reply_text("The bot is in beta mode now so you can't bet more than 10000 sats for now! \nsend a less amount:")
            return
        if (balance >= string_int) :
            Database().set_bet(user.id, string_int)
            Database().set_balance(user.id, balance - string_int)
            context.user_data["state"] = UserState.IDLE
            create_game(update, context)
        else:
            update.message.reply_text("Bet amount is more than your balance! please enter less amount:")
    except ValueError:
        update.message.reply_text("Please send a number:")


def start_callback(update, context):
    """Starts a game that has been created already"""
    user = update.effective_user
    chat = update.effective_chat
    lang_id = Database().get_lang_id(chat.id)
    translator = Translator(lang_id=lang_id)

    try:
        game = GameStore().get_game(update.effective_chat.id)

        if not is_button_affiliated(update, context, game, lang_id):
            return
    except NoActiveGameException:
        update.callback_query.answer(translator("mp_no_created_game_callback"))
        remove_inline_keyboard(update, context)
        return

    try:
        game.start(user.id)
        update.callback_query.answer(translator("mp_starting_game_callback"))
    except errors.GameAlreadyRunningException:
        update.callback_query.answer(translator("mp_game_already_begun_callback"))
        return
    except errors.NotEnoughPlayersException:
        update.callback_query.answer(translator("mp_not_enough_players_callback"))
        return
    except errors.InsufficientPermissionsException:
        update.callback_query.answer(translator("mp_only_creator_start_callback").format(user.first_name))
        return

    if game.type != BlackJackGame.Type.SINGLEPLAYER:
        players_are = translator("mp_players_are")
        for player in game.players:
            players_are += "👤{}\n".format(player.first_name)
        players_are += "\n"
    else:
        players_are = ""

    update.effective_message.edit_text(translator("game_starts_now").format(players_are, get_cards_string(game.dealer, lang_id)))
    players_turn(update, context)


@needs_active_game
def stop_cmd(update, context):
    """Stops a game for a specific user"""
    user = update.effective_user
    chat = update.effective_chat
    lang_id = Database().get_lang_id(chat.id)
    translator = Translator(lang_id=lang_id)

    game = GameStore().get_game(chat.id)

    user_id = user.id
    try:
        if chat.type == "group" or chat.type == "supergroup":
            # If yes, get the chat admins
            admins = context.bot.get_chat_administrators(chat_id=chat.id)
            # if user.id in chat admin IDs, let them end the game with admin powers
            if user.id in [x.user.id for x in admins]:
                user_id = -1

        game.stop(user_id)
        update.effective_message.reply_text(translator("game_ended"))
    except errors.InsufficientPermissionsException:
        update.effective_message.reply_text(translator("mp_only_creator_can_end"))


@needs_active_game
def join_callback(update, context):
    """
    CallbackQueryHandler callback for the 'join' inline button. Adds the executing player to the game of the specific chat
    """
    user = update.effective_user
    chat = update.effective_chat
    lang_id = Database().get_lang_id(chat.id)
    translator = Translator(lang_id=lang_id)

    game = GameStore().get_game(chat.id)

    if not is_button_affiliated(update, context, game, lang_id):
        return

    try:
        game.add_player(user.id, user.first_name)
        update.effective_message.edit_text(text=translator("mp_request_join").format(game.get_player_list()),
                                           reply_markup=get_join_keyboard(game.id, lang_id))
        update.callback_query.answer(translator("mp_join_callback").format(user.first_name))

        # If players are full, replace join keyboard with start keyboard
        if len(game.players) >= game.MAX_PLAYERS:
            update.effective_message.edit_reply_markup(reply_markup=get_start_keyboard(lang_id))
    except errors.GameAlreadyRunningException:
        remove_inline_keyboard(update, context)
        update.callback_query.answer(translator("mp_game_already_begun_callback"))
    except errors.MaxPlayersReachedException:
        update.effective_message.edit_reply_markup(reply_markup=get_start_keyboard(lang_id))
        update.callback_query.answer(translator("mp_max_players_callback"))
    except errors.PlayerAlreadyExistingException:
        update.callback_query.answer(translator("mp_already_joined_callback"))


@needs_active_game
def hit_callback(update, context):
    """
    CallbackQueryHandler callback for the 'hit' inline button. Draws a card for you.
    """
    user = update.effective_user
    chat = update.effective_chat
    lang_id = Database().get_lang_id(chat.id)
    translator = Translator(lang_id=lang_id)

    game = GameStore().get_game(chat.id)

    if not is_button_affiliated(update, context, game, lang_id):
        return

    player = game.get_current_player()
    user_mention = html_mention(user_id=player.user_id, first_name=player.first_name)

    try:
        if user.id != player.user_id:
            update.callback_query.answer(translator("mp_not_your_turn_callback").format(user.first_name))
            return

        game.draw_card()
        player_cards = get_cards_string(player, lang_id)
        text = translator("your_cards_are").format(user_mention, player.cardvalue, player_cards)
        update.effective_message.edit_text(text=text, parse_mode=ParseMode.HTML, reply_markup=get_game_keyboard(game.id, lang_id))
    except errors.PlayerBustedException:
        player_cards = get_cards_string(player, lang_id)
        text = (translator("your_cards_are") + "\n\n" + translator("you_busted")).format(user_mention, player.cardvalue, player_cards)
        update.effective_message.edit_text(text=text, parse_mode=ParseMode.HTML, reply_markup=None)
        next_player(update, context)
    except errors.PlayerGot21Exception:
        player_cards = get_cards_string(player, lang_id)
        if player.has_blackjack():
            text = (translator("your_cards_are") + "\n\n" + translator("got_blackjack")).format(user_mention, player.cardvalue, player_cards)
            update.effective_message.edit_text(text=text, parse_mode=ParseMode.HTML, reply_markup=None)
            next_player(update, context)
        elif player.cardvalue == 21:
            text = (translator("your_cards_are") + "\n\n" + translator("got_21")).format(user_mention, player.cardvalue, player_cards)
            update.effective_message.edit_text(text=text, parse_mode=ParseMode.HTML, reply_markup=None)
            next_player(update, context)


@needs_active_game
def stand_callback(update, context):
    """
    CallbackQueryHandler callback for the 'stand' inline button. Prepares round for the next player.
    """
    chat = update.effective_chat
    lang_id = Database().get_lang_id(chat.id)
    game = GameStore().get_game(update.effective_chat.id)

    if not is_button_affiliated(update, context, game, lang_id):
        return

    next_player(update, context)


def newgame_callback(update, context):
    remove_inline_keyboard(update, context)
    start_cmd(update, context)


def rules_cmd(update, context):
    update.effective_message.reply_text("Rules:\n\n- Black Jack pays 1 to 1\n- Dealer must stand on 17 and must draw to 16")

def send_deposit(update, context):
    user = update.effective_user
    balance = Database().get_balance(user.id)
    try:
        amount = context.args[0]
        try:
            amount = int(amount)
            balance = int(balance)
            if amount>=1:
                try:
                    invoice = requests.post("https://legend.lnbits.com/api/v1/payments", data = '{"out": false,"amount":'+str(amount)+',"webhook": "'+config.webhookurl+str(user.id)+'"}', headers = {"X-Api-Key": config.api_key,"Content-type": "application/json"})
                    kk = invoice.json()
                    update.effective_message.reply_text(kk["payment_request"])
                except Exception as e: print(e)
            else:
                update.effective_message.reply_text("amount more than your balance!\nYour balance:"+str(balance)+"sats")
        except AttributeError:
            update.effective_message.reply_text("Please use the command like this: \n/deposit <amount>")
    except:
        update.effective_message.reply_text("Please use the command like this: \n/deposit <amount>")

def send_withdraw(update, context):
    #update.effective_message.reply_text("Bot is in beta mode can't withdraw for now!")
    user = update.effective_user
    balance = Database().get_balance(user.id)
    try:
        amount = context.args[0]
        try:
            amount = int(amount)
            balance = int(balance)
            if amount<=balance and amount>=1:
                try:
                    invoice = requests.post("https://legend.lnbits.com/withdraw/api/v1/links", data = '{"title": "'+str(user.id)+'", "min_withdrawable": '+str(amount)+', "max_withdrawable": '+str(amount)+', "uses": 1, "wait_time": 1, "is_unique": true}', headers = {"X-Api-Key": config.admin_key,"Content-type": "application/json"})
                    kk = invoice.json()
                    update.effective_message.reply_text(kk["lnurl"])
                    # bot = Bot(token=config.BOT_TOKEN)
                    # bot.send_message(chat_id=Database().get_chat_id("webdblackjack"), text="NEW WITHDRAW REQUEST "+str(user)+" "+str(amount))
                    # with open('withdraw.txt', 'a') as file:
                    #     file.write(user.username + " " + str(amount)+"\n")
                except Exception as e: print(e)
                Database().set_balance(user.id, balance-amount)
                update.effective_message.reply_text("withdraw of "+str(amount)+"sats has been submitted.")
            else:
                update.effective_message.reply_text("amount more than your balance!\nYour balance:"+str(balance)+"sats")
        except AttributeError:
            update.effective_message.reply_text("Please use the command like this: \n/withdraw [amount]")
    except:
        update.effective_message.reply_text("Please use the command like this: \n/withdraw [amount]")
def show_balance(update, context):
    user = update.effective_user
    balance = Database().get_balance(user.id)
    update.effective_message.reply_text("Your Balance: "+str(balance)+ "sats\n\nDeposit more by using the command /deposit <amount in sats>")