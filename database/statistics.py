# -*- coding: utf-8 -*-
import logging
from datetime import datetime
from time import time

from database import Database

__author__ = 'Rico'
logger = logging.getLogger(__name__)


def set_game_won(user_id):
    if user_id > 0:
        db = Database()
        games_won = int(db.get_user(user_id)[6]) + 1
        logger.debug("Add game won for user: {}".format(user_id))
        db.set_games_won(games_won, user_id)


def add_game_played(user_id):
    db = Database()
    games_played = db.get_played_games(user_id)
    games_played = games_played + 1
    logger.debug("Add game played for user: {}".format(user_id))
    db.set_games_played(games_played, user_id)
    db.set_last_played(str(int(time())), user_id)


def generate_bar_chart(win_percentage):
    """
    Generate a string of emojis representing a bar (10 chars) that indicates wins vs. losses
    :param win_percentage: The percentage of wins
    :return: Example (55.0%-64.9%) '🏆🏆🏆🏆🏆🏆🔴🔴🔴🔴'
    """
    win_portion = round(win_percentage / 10)
    loss_portion = 10 - win_portion
    return "🏆" * win_portion + "🔴" * loss_portion


def get_user_stats(user_id):
    """
    Generates and returns a string displaying the statistics of a user
    :param user_id: The user_id of a specific user
    :return:
    """
    user = Database().get_user(user_id)

    played_games = int(user[5]) or 1
    won_games = user[6]
    last_played = int(user[8])
    last_played_formatted = datetime.utcfromtimestamp(last_played).strftime('%d.%m.%y %H:%M')
    win_percentage = round(float(won_games) / float(played_games), 4) * 100
    bar = generate_bar_chart(win_percentage)

    template = "Here are your statistics 📊:\n\nPlayed Games: {}\nWon Games: {}\nLast Played: {} UTC\n\n{}\n\nWinning rate: {:.2%}"
    statistics_string = template.format(played_games, won_games, last_played_formatted, bar, win_percentage)
    return statistics_string
