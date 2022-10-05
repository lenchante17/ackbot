"""
Class models for achievements unlocked by user actions.
All achievements inherits BaseModel.Achievement class.
"""

import random
import re

from discord import message
from .BaseModel import Achievement
from collections import defaultdict

class Welcome(Achievement):

    achievement_name = 'Welcome'
    achievement_description = '__init__'
    achievement_earning = '처음으로 글을 제출'
    score_threshold = {"base": 1}
    xp = 10
    
    def __init__(self, discord_user_id, db_client, args=None, kwargs=None):
        self.args = args
        self.kwargs = kwargs
        super().__init__(discord_user_id, self.achievement_name, self.achievement_description, 
        self.achievement_earning, self.score_threshold, self._score, self.xp, db_client
        )

    def _score(self):
        self.score_current = {"base": 1}
        return True

class Accidentals(Achievement):
    
    achievement_name = 'Accidentals'
    achievement_description = 'tag를 많이 써주세요'
    achievement_earning = '글에 tag를 사용'
    score_threshold = {"base": 1}
    xp = 10

    def __init__(self, discord_user_id, db_client, args=None, kwargs=None):
        self.args = args
        self.kwargs = kwargs
        super().__init__(discord_user_id, self.achievement_name, self.achievement_description, 
        self.achievement_earning, self.score_threshold, self._score, self.xp, db_client
        )

    def _score(self):
        self.score_current = {"base": 1}
        return True

class Fermata(Achievement):
    """
    You tried achievement. Given when user asks for it, using
    >gimme command.

    Parameters
    ----------

    discord_user_id : int
        Discord user id from user which triggered the achievement

    db_client : DbClient
        Instance of DbClient class

    args : list [Optional]
        List of additional args
    """
    
    achievement_name = 'Fermate'
    achievement_description = '꾸준히'
    achievement_earning = '1주 연속으로 글을 제출'
    score_threshold = {"base": 1}
    xp = 1

    def __init__(self, discord_user_id, db_client, args=None, kwargs=None):
        self.args = args
        self.kwargs = kwargs
        super().__init__(discord_user_id, self.achievement_name, self.achievement_description, 
        self.achievement_earning, self.score_threshold, self._score, self.xp, db_client
        )

    def _score(self):
        self.score_current = {"base": 1}
        return True

class BuzzerBeater(Achievement):
    """
    You tried achievement. Given when user asks for it, using
    >gimme command.

    Parameters
    ----------

    discord_user_id : int
        Discord user id from user which triggered the achievement

    db_client : DbClient
        Instance of DbClient class

    args : list [Optional]
        List of additional args
    """
    
    score_total = 1 
    achievement_name = 'Buzzer Beater'
    achievement_description = '마감보다 빠른'
    achievement_earning = '마감 1분이내 제출 성공'
    score_threshold = {"base": 1}
    xp = 1

    def __init__(self, discord_user_id, db_client, args=None, kwargs=None):
        self.args = args
        self.kwargs = kwargs
        super().__init__(discord_user_id, self.achievement_name, self.achievement_description, 
        self.achievement_earning, self.score_threshold, self._score, self.xp, db_client
        )

    def _score(self):
        self.score_current = {"base": 1}
        return True

class EarlyBird(Achievement):
    """
    You tried achievement. Given when user asks for it, using
    >gimme command.

    Parameters
    ----------

    discord_user_id : int
        Discord user id from user which triggered the achievement

    db_client : DbClient
        Instance of DbClient class

    args : list [Optional]
        List of additional args
    """
    
    score_total = 1
    achievement_name = 'Early Bird'
    achievement_description = '당신은 일찍 일어나는 새'
    achievement_earning = '마감 6시간 전 제출'
    score_threshold = {"base": 1}
    xp = 1

    def __init__(self, discord_user_id, db_client, args=None, kwargs=None):
        self.args = args
        self.kwargs = kwargs
        super().__init__(discord_user_id, self.achievement_name, self.achievement_description, 
        self.achievement_earning, self.score_threshold, self._score, self.xp, db_client
        )

    def _score(self):
        self.score_current = {"base": 1}
        return True