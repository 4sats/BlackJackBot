# -*- coding: utf-8 -*-
import logging
import os
import sqlite3
from time import time


class Database(object):
    dir_path = os.path.dirname(os.path.abspath(__file__))

    _instance = None
    _initialized = False

    def __new__(cls):
        if not Database._instance:
            Database._instance = super(Database, cls).__new__(cls)
        return Database._instance

    def __init__(self):
        if not self._initialized:
            database_path = os.path.join(self.dir_path, "users.db")
            self.logger = logging.getLogger(__name__)

            if not os.path.exists(database_path):
                self.logger.debug("File '{}' does not exist! Trying to create one.".format(database_path))
                try:
                    self.create_database(database_path)
                except Exception:
                    self.logger.error("An error has occurred while creating the database!")

            self.connection = sqlite3.connect(database_path)
            self.connection.text_factory = lambda x: str(x, 'utf-8', "ignore")
            self.cursor = self.connection.cursor()

            self._initialized = True

    @staticmethod
    def create_database(database_path):
        """
        Create database file and add admin and users table to the database
        :param database_path:
        :return:
        """
        open(database_path, 'a').close()

        connection = sqlite3.connect(database_path)
        connection.text_factory = lambda x: str(x, 'utf-8', "ignore")
        cursor = connection.cursor()

        cursor.execute("CREATE TABLE 'admins' "
                       "('userID' INTEGER NOT NULL,"
                       "'first_name' TEXT,"
                       "'username' TEXT,"
                       "PRIMARY KEY('userID'));")

        cursor.execute("CREATE TABLE 'users'"
                       "('userID' INTEGER NOT NULL,"
                       "'languageID' TEXT,"
                       "'first_name' TEXT,"
                       "'last_name' TEXT,"
                       "'username' TEXT,"
                       "'gamesPlayed' INTEGER,"
                       "'gamesWon' INTEGER,"
                       "'gamesTie' INTEGER,"
                       "'lastPlayed' INTEGER,"
                       "PRIMARY KEY('userID'));")
        connection.commit()
        connection.close()

    def get_user(self, user_id):
        self.cursor.execute("SELECT * FROM users WHERE userID=?;", [str(user_id)])

        result = self.cursor.fetchone()
        if result:
            if len(result) > 0:
                return result

        return ()

    def get_recent_players(self):
        one_day_in_secs = 60 * 60 * 24
        current_time = int(time())
        self.cursor.execute("SELECT userID FROM users WHERE lastPlayed>=?;", [current_time - one_day_in_secs])

        return self.cursor.fetchall()

    def get_played_games(self, user_id):
        self.cursor.execute("SELECT gamesPlayed FROM users WHERE userID=?;", [str(user_id)])

        result = self.cursor.fetchone()

        if not result:
            return 0

        if len(result) > 0:
            return int(result[0])
        else:
            return 0

    def get_all_users(self):
        self.cursor.execute("SELECT rowid, * FROM users;")
        return self.cursor.fetchall()

    def get_admins(self):
        self.cursor.execute("SELECT userID from admins;")
        admins = self.cursor.fetchall()
        admin_list = []
        for admin in admins:
            admin_list.append(admin[0])
        return admin_list

    def get_lang_id(self, user_id):
        self.cursor.execute("SELECT languageID FROM users WHERE userID=?;", [str(user_id)])
        result = self.cursor.fetchone()
        if result:
            return result[0]
        else:
            return "en"

    def add_user(self, user_id, lang_id, first_name, last_name, username):
        if self.is_user_saved(user_id):
            return
        self._add_user(user_id, lang_id, first_name, last_name, username)

    def _add_user(self, user_id, lang_id, first_name, last_name, username):
        try:
            self.cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, 0, 0, 0, 0);", [str(user_id), lang_id, first_name, last_name, username])
            self.connection.commit()
        except sqlite3.IntegrityError:
            return

    def insert(self, column_name, value, user_id):
        self.cursor.execute("UPDATE users SET " + column_name + "= ? WHERE userID = ?;", [value, str(user_id)])
        self.connection.commit()

    def is_user_saved(self, user_id):
        self.cursor.execute("SELECT rowid, * FROM users WHERE userID=?;", [str(user_id)])

        result = self.cursor.fetchall()
        if len(result) > 0:
            return True
        else:
            return False

    def user_data_changed(self, user_id, first_name, last_name, username):
        self.cursor.execute("SELECT * FROM users WHERE userID=?;", [str(user_id)])

        result = self.cursor.fetchone()

        # check if user is saved
        if result:
            if result[2] == first_name and result[3] == last_name and result[4] == username:
                return False
            return True
        else:
            return True

    def update_user_data(self, user_id, first_name, last_name, username):
        self.cursor.execute("UPDATE users SET first_name=?, last_name=?, username=? WHERE userID=?;", [first_name, last_name, username, str(user_id)])
        self.connection.commit()

    def reset_stats(self, user_id):
        self.cursor.execute("UPDATE users SET gamesPlayed='0', gamesWon='0', gamesTie='0', lastPlayed='0' WHERE userID=?;", [str(user_id)])
        self.connection.commit()

    def close_conn(self):
        self.connection.close()
