# pylint: disable=invalid-name
"""
This file contains the base achievement model.
This class must be inherited to all other achievement models.
"""

import base64
from datetime import datetime
import os

class Achievement:
    """
    Base achievement model. This class
    incorportates all management and procedures for
    achievement completion and scoring.

    Parameters
    ----------

    discord_user_id : int
        Discord user id which triggered the event

    achievement_name : str
        Name of the achievement

    achievement_description : str
        Description of the achievement

    score_total : dict
        Dict of triggers required to complete
        the achievement

    score_func : Callable
        Function to score achievement at each trigger

    db_client : DbClient
        DbClient object instance
    """

    TABLE_NAME = 'progress'

    def __init__(self,user_name, achievement_name, achievement_description, achievement_earning,
        score_threshold, score_func, xp, db_client
    ):
        self.user_name = user_name
        self.achievement_name = achievement_name
        self.achievement_id = self.get_id()
        self.db_client = db_client
        self.load_achievement()
        self.achievement_description = achievement_description
        self.achievement_earning = achievement_earning
        self.score_threshold = score_threshold
        self.score_func = score_func
        self.completed_by_last_action = False
        self._scored = False
        self.xp = xp
        # self.complete_func = complete_func

    def get_xp(self):
        return self.xp

    def load_achievement(self):
        """
        Loads the current achievement from database
        """
        query = {
            'user_name': self.user_name,
            'achievement_id': self.achievement_id
        }
        ach = self.db_client.get('progress', query)
        ach = [a for a in ach]
        if ach:
            ach = ach[0]
        else:
            ach = {
                'unlock_date': None,
                'score_current': 0,
                'completed': False,
                'last_update': None
            }
        self.unlock_date = ach["unlock_date"]
        self.score_current = ach["score_current"]
        self.completed = ach["completed"]
        self.last_update = ach["last_update"]


    # @property
    # def icon_url(self):
    #     """
    #     Returns the URL for achievement logo.
    #     """
    #     # I could not think a better way to do this
    #     # Because it would need to pass config object to all classes.
    #     if self.__class__.__name__ == 'GivenAchievement':
    #         return os.getenv('IWK__ACH__' + self.__class__.__name__)
    #     return os.getenv('IWK__ACH__' + self.__class__.__name__)


    def score(self):
        """
        Score function.
        If current counter reachs total score,
        call self.complete function
        """
        if not self.completed:
            # score_before = self.score_current
            # self.score_func()
            # score_after = self.score_current
            # if score_before == score_after:
            #     self._scored = False
            # else:
            #     self._scored = True
            
            self._scored = False
            self._scored = self.score_func()
            complete_condition = 1
            for k, v in self.score_threshold.items():
                if self.score_current[k] < v:
                    complete_condition = 0
            if complete_condition:
                self.complete()


    def complete(self):
        """
        Completion function.
        This unlocks achievement for the user.
        Its called when current score reaches total score
        """
        # Maybe later each achievement gets its
        # own completion funciton
        #
        # self.complete_func(self._document)
        self.completed = True #pylint: disable=attribute-defined-outside-init
        self.unlock_date = datetime.today().utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ') #pylint: disable=attribute-defined-outside-init
        self.last_update = self.unlock_date #pylint: disable=attribute-defined-outside-init
        self.completed_by_last_action = True


    def to_json(self):
        """
        Returns current object as a json object
        """
        return {
            'user_name': self.user_name,
            'achievement_id': self.achievement_id,
            'achievement_name': self.achievement_name,
            'achievement_description': self.achievement_description,
            'achievement_earning': self.achievement_earning, #pylint: disable=no-member
            'unlock_date': self.unlock_date,
            # 'icon_url': self.icon_url,
            'score_current': self.score_current,
            'score_threshold': self.score_threshold,
            'completed': self.completed,
            'last_update': self.last_update
        }


    def get_id(self):
        """
        Returns an unique id for each achievement.
        (But it is only the name encoded with base64 :()
        """
        return base64.b64encode(self.achievement_name.encode()).decode('utf-8')


    def update(self, db_client):
        """
        Updates current object into database

        Parameters
        ----------

        db_client : DbClient
            DbClient object class
        """
        db_client.update(
            self.TABLE_NAME,
            {
                'user_name': self.user_name,
                'achievement_id': self.achievement_id
            },
            self.to_json(),
            upsert=True
        )
