import discord
import requests
import inspect
from collections import Counter
from pymongo import MongoClient
import os
import textwrap
import io
import _pickle as pk
import random
from datetime import datetime, timedelta
from datetime import time

import asyncio
from discord.ext import tasks

from .GivenAchievement import GivenAchievement
from . import BehaviorAchievements
from .BehaviorAchievements import *
from .db_client import DbClient
from .utils import *

from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

class Bot:
    """
    Bot class. It handles the majority of Bot services, including
    commands, achievements, etc.

    Parameters
    ----------

    discord_client : discord
        Discord client object

    iwakura_client : Bot
        Bot class instance
    """
    ach_classes = BehaviorAchievements
    
    def __init__(self, discord_client, environment, config):
        """
        Creates the instance of main controller.
        This class self handles the biggest part of command
        routines, like connecting to db, manage environment, trigger and
        update achievements.

        Parameters
        ----------

        discord_client : Discord
            instance of discord client class

        environment : str
            environment name, enuns to prod, dev, hml.
            MongoDb tables are used based on this variable
        """
        
        self.discord_client = discord_client
        self.environment = environment
        self.config = config
        self.connect_to_db()

    async def insert_user(self, user_name, user_id):
        self.db_client.update_author(user_name, {'user_id': user_id}, upsert=True)

    async def send_notification(self, user_id, cls, xp):
        """
        Sends a notification to the user when
        a achievement is unlocked

        Parameters
        ----------

        user_id : int
            discord message class
        
        cls : Achievement
            instance of achievement class which have been
            unlocked
        """
        user = await self.discord_client.fetch_user(user_id)
        cls = cls.to_json()
        msg = f"[Achievement] {cls['achievement_name']} : {cls['achievement_description']} \n ({cls['achievement_earning']}) \n Now, your exp is {xp}!"
        await user.send(content=msg)
        # msg = self.mount_notication(cls)

        # with io.BytesIO() as image_binary:
        #     msg.save(image_binary, format='PNG')
        #     image_binary.seek(0)
        #     await user.send(file=discord.File(fp=image_binary, filename='achievement.png'))
        print(f"Sent {cls['achievement_name']} to", user.name)
        

    async def trigger_achievement(self, user_name, _class, *args, **kwargs):
        """
        Triggers an achievement, increases its scores
        and updates into db. It also sends the notification
        if score reaches the total to unlock.

        Parameters
        ----------

        user_name : str
            user_name
        
        _class : Achievement
            class that is being triggered

        args : list
            List of optional arguments
            may message, message.contents, configs, etc
        """
        
        send_to = None
        if _class == GivenAchievement:
            cls = GivenAchievement(args[0], self.db_client, args[1], args[2])
            send_to = args[0]
        else:
            cls = _class(user_name, self.db_client, args, kwargs)
            send_to = self.db_client.get_author(user_name)["user_id"]
        
        if not cls.completed:
            cls.score()
            if cls._scored:
                cls.update(self.db_client)

        if cls.completed_by_last_action:
            xp = cls.get_xp()
            self.db_client.increase_author(user_name, {"xp": xp})
            xp = self.db_client.get_author(user_name)["xp"]
            await self.send_notification(send_to, cls, xp)


    async def show_achievements(self, context, user_name):
        """
        Mounts a message with all unlocked achievements from
        selected user id, and sends to the requester DM.

        Parameters
        ----------

        context : discord.message
            discord message class

        target : int
            target discord user id
        """
        
        _db_unlocked = self.db_client.get('progress', {'user_name': user_name, 'completed': True})
        db_unlocked = [a for a in _db_unlocked]
        all_achs = {}
        for cls in inspect.getmembers(self.ach_classes):
            _cls_dict = {}
            _cls = inspect.getmembers(cls[1])
            for member in _cls:
                _cls_dict[member[0]] = member[1]
            if 'achievement_name' in _cls_dict:
                all_achs[cls[0]] = (_cls_dict)
                # all_achs[cls[0]]["icon_url"] = self.config.get_attr('achievement', cls[0])

        db_unlocked = [ach["achievement_name"] for ach in db_unlocked]
        for cls in all_achs:
            if all_achs[cls]["achievement_name"] in db_unlocked:
                all_achs[cls]["show"] = True
            else:
                all_achs[cls]["show"] = False

        for cls in _db_unlocked:
            if cls["completed"]:
                cls["show"] = True
                all_achs[cls["achievement_name"]] = cls

        # msg = self.mount_image(all_achs)
        msg = 'Your achievement list: ' + ", ".join(db_unlocked)
        await context.author.send(msg)
        # with io.BytesIO() as image_binary:
        #     msg.save(image_binary, format='PNG')
        #     image_binary.seek(0)
        #     await context.author.send(file=discord.File(fp=image_binary, filename='achievements.png'))
        print('Sent achievements to', context.author.name)

    async def send_message(self, user_name, message):
        user_id = self.db_client.get_author(user_name)['user_id']
        user = await self.discord_client.fetch_user(user_id)
        await user.send(content=message)

    async def return_success(self, user_name):
        user_id = self.db_client.get_author(user_name)["user_id"]
        user = await self.discord_client.fetch_user(user_id)
        msg = "You sent a valid message for today!"
        await user.send(msg)

    async def return_fail(self, user_name):
        user_id = self.db_client.get_author(user_name)["user_id"]
        user = await self.discord_client.fetch_user(user_id)
        msg = "You failed to send a valid message! (Please check the number of sentences)"
        await user.send(msg)

    async def record_message(self, timestamp, user_name, tags, series, sentences, raw_message):
        """
        Record a message and metadata

        Parameters
        ----------

        timestamp : datetime.datetime object

        user_name : str
            target discord user name
        
        tag : list
            list of tag
        
        message: str
            contents of message
        """
        self.db_client.insert('message', {'timestamp': timestamp, 'user_name': user_name, 'tags': tags, 'series': series,'sentences': sentences, 'raw_message': raw_message})
            
            
    def update_scores(self, timestamp, user_name, tags, series, sentences):
        """
        update score for message author

        scores
        ----------

        zeroth_order_score:
            calculated by time stamp
        
        first_order_score:

            contents of message
        """

        buzzer_beater, valid, early_bird = 0, 0, 0
        if self.isintempo(timestamp):
            if timestamp.hour == 21 and timestamp.minute == 59:
                buzzer_beater = 1
            if timestamp.hour < 16 and timestamp.hour > 4:
                early_bird = 1
            
            valid = int(len(sentences) > 2)

        if valid:
            self.update_tag_stats(user_name, tags)
            
            # check keys:
            if not self.db_client.key_existence(user_name, 'daily'):
                self.db_client.update_author(user_name, {"daily": 0})
            if not self.db_client.key_existence(user_name, 'last_day'):
                self.db_client.update_author(user_name, {"last_day": 0})
            if not self.db_client.key_existence(user_name, 'sequence'):
                self.db_client.update_author(user_name, {"sequence": 0})
            if not self.db_client.key_existence(user_name, 'series'):
                self.db_client.update_author(user_name, {"series": 0})

            if self.db_client.get_author(user_name)['daily'] == 0 and self.db_client.get_author(user_name)['last_day']:
                self.db_client.increase_author(user_name, {"sequence": 1})
                self.db_client.update_author(user_name, {"daily": 1}, upsert=True)
                self.db_client.update_author(user_name, {"buzzer_beater": buzzer_beater}, upsert=True)
                self.db_client.update_author(user_name, {"early_bird": early_bird}, upsert=True)
        return valid

    def update_tag_stats(self, user_name, tags):
        author = self.db_client.get_author(user_name)
        if "tag_stats" not in author.keys():
            self.db_client.update_author(user_name, {"tag_stats": Counter(tags)}, upsert=True)
        else:
            updated_stats = Counter(author["tag_stats"]) + Counter(tags)
            self.db_client.update_author(user_name, {"tag_stats": updated_stats, "tag_diversity": len(updated_stats.keys())}, upsert=True)


    def connect_to_db(self):
        """
        Creates a connection to the database and
        to discord API, based on previously loaded
        .env values
        """
        
        MONGO_URI = self.config.get_attr('api', 'mongo_uri')
        print(f'**********uri: {MONGO_URI}')
        client_mongo = MongoClient(MONGO_URI, connect=False)
        # client_mongo = MongoClient(MONGO_URI, connect=False, ssl=True, ssl_cert_reqs=ssl.CERT_NONE)
        self.db_client = DbClient(client_mongo, "achievement_bot", self.environment)

    async def get_random_three_keywords(self):
        with open('keywords.pkl', 'rb') as f:
            keyword = pk.load(f)
        idx = list(range(len(keyword)))
        random.shuffle(idx)
        return [keyword[i] for i in idx[:3]]

    # @tasks.loop(hours=24, time=time(15, 39, 0))
    # async def daily_reset(self):
    #     print('a')
    #     print('b')

    async def check_daily_reset(self, timestamp, channel):
        """
        Daily reset at 10 pm
        
        If we got message check daily reset 

        """
        sys = self.db_client.get("Sys", {})
        if len(sys) == 0:
            last_day = datetime(2022, 10, 5, 22, 0, 0, 0)
            self.db_client.insert("Sys", {"last_day": last_day})
        else:
            last_day = sys[0]['last_day']

        if not self.isintempo(timestamp):
            keywords = await self.get_random_three_keywords()
            m0 = "========= 날짜 변경! ========="
            m1 = f"오늘의 랜덤 키워드 1.{keywords[0]} 2.{keywords[1]} 3.{keywords[2]}"
            m2 = "from https://blog.naver.com/zu_hg/222447687783"
            await channel.send(f"{m0}\n{m1}\n{m2}")
            
            i = 2
            while timestamp > last_day + timedelta(days=i):
                i += 1
            self.db_client.update("Sys", {}, query={"last_day": last_day + timedelta(days=i-1)})
            if i == 2:
                self.db_client.update_many(table='Author', match={'daily': 1}, query={'daily': 0, 'last_day': 1})
                self.db_client.update_many(table='Author', match={'daily': 0}, query={'daily': 0, 'last_day': 0})
            else:
                self.db_client.update_many(table='Author', match={'daily': 1}, query={'daily': 0})

    def isintempo(self, timestamp):
        return timestamp < self.db_client.get("Sys", {})[0]['last_day'] + timedelta(days=1)

    def mount_notication(self, achievement):
        """
        Mount achievement completion image.
        WARNING: THIS IS VERY BAD DONE, SORRY.

        Parameters
        ----------

        achievement : Achievement
            instance of Achievement class
        """
        
        ach = achievement.to_json()
        # Base coord values
        x_max = 400
        y_max = 140
        x_logo = 10
        y_logo = 10
        x_title = 120
        y_title = 45
        x_desc = 120
        y_desc = 65
        x_ann = 120
        y_ann = 10
        x_foot = (x_max / 2) - (int(len(ach['achievement_earning']) / 2) * 5.7)
        y_foot = 120

        # Base empty image
        new_im = Image.new('RGB', (x_max, y_max))
        print(f'ach!!! {ach}')
        print(f'cwd: {os.getcwd()}')
        im = Image.open(ach["icon_url"]).convert("RGBA")
        #im = Image.open(requests.get(ach["icon_url"], stream=True).raw)

        # Inserting achievement logo into empty image
        new_im.paste(im, (x_logo,y_logo), im)
        
        # Instancing fonts
        title_font = ImageFont.truetype("arial.ttf", 18)
        desc_font = ImageFont.truetype("arial.ttf", 14)
        foot_font = ImageFont.truetype("arial.ttf", 12)

        def write_lines(text, font, img, x, y, color, max_size=40):
            lines = textwrap.wrap(text, width=max_size)
            y_text = 0
            for line in lines:
                width, height = font.getsize(line)
                img.text((x, y + y_text),line,color,font=font)
                y_text += 15
        
        # Writing texts
        text_im = ImageDraw.Draw(new_im)
        write_lines('Congratulations! You have unlocked:', desc_font, text_im, x_ann, y_ann, (255,255,255), max_size=100)
        write_lines(ach["achievement_name"], title_font, text_im, x_title, y_title, (255,255,255))
        write_lines(ach["achievement_description"], desc_font, text_im, x_desc, y_desc, (135,135,135))
        text_im.text((x_foot, y_foot),ach['achievement_earning'],(0, 202, 224),font=foot_font)

        return new_im

    def mount_image(self, achievements):
        """
        Mounts the image with all locked and unlocked achievements.
        WARNING: THIS IS VERY BAD DONE, SORRY.

        Parameters
        ----------

        achievements : list
            List of all achievements dicts
        """
        
        # Initial coord values
        x_start = 10
        y_start = 20
        footer_size = 100
        y_max = 1000 + y_start
        x_max = round((len(achievements) * 100) / (y_max - y_start)) * 410
        new_im = Image.new('RGB', (x_max, y_max + footer_size))
        x_index = x_start
        y_index = y_start

        # Instancing fonts
        title_font = ImageFont.truetype(self.config.get_attr('global', 'fontfile'), 20)
        desc_font = ImageFont.truetype(self.config.get_attr('global', 'fontfile'), 18)

        def write_lines(text, font, img, option, x, y):
            lines = textwrap.wrap(text, width=30)
            y_text = 0
            for line in lines:
                width, height = font.getsize(line)
                if option == 'title':
                    img.text((x, y + y_text),line,(255,255,255),font=font)
                else:
                    img.text((x, y + y_text),line,(135,135,135),font=font)
                y_text += 15

        # Inserting achievement info into
        # empty image
        for _cls in achievements:
            cls = achievements[_cls]
            text_im = ImageDraw.Draw(new_im)
            if not cls['icon_url']:
                continue
            if cls['show']:
                im = Image.open(requests.get(cls['icon_url'], stream=True).raw)
                write_lines(
                    cls["achievement_name"], title_font, text_im, 'title', x_index + 110, y_index + 20
                )
                write_lines(
                    cls["achievement_description"], desc_font, text_im, 'description', x_index + 110, y_index + 40
                )
            else:
                # Loading default image whrn achievement was not
                # unlocked by user.
                im = Image.open(requests.get(
                    self.config.get_attr('achievement', 'QuestionmarksIcon')
                    , stream=True).raw
                )
                text_im.text((x_index + 110, y_index + 20),'LOCKED ACHIEVEMENT',(255,255,255),font=title_font)
                text_im.text((x_index + 110, y_index + 40),'????????????',(135,135,135),font=desc_font)
            
            # Pastes the image and set coords for the next one
            im=Image.eval(im,lambda x: x+(x_index+y_index)/30)
            new_im.paste(im, (x_index,y_index), im)
            y_index += 110
            if y_index >= y_max - 110:
                y_index = y_start
                x_index += 410

        # Getting values to the % footer text
        unlocked = len(
            [key for key in achievements if achievements[key]["show"] and achievements[key]['score_total'] != -1]
        )
        unlockable = len([key for key in achievements if achievements[key]['score_total'] != -1])
        completion = f'Completion: {round((unlocked / unlockable) * 100, 2)}% of achievements unlocked'
        text_im.text((50, y_max + 30), completion,(255,255,255),font=title_font)

        return new_im

    def mount_notication2(self, achievement):
        """
        Mount achievement completion image.
        WARNING: THIS IS VERY BAD DONE, SORRY.

        Parameters
        ----------

        achievement : Achievement
            instance of Achievement class
        """
        
        ach = achievement.to_json()
        # Base coord values
        x_max = 400
        y_max = 140
        x_logo = 10
        y_logo = 10
        x_title = 120
        y_title = 45
        x_desc = 120
        y_desc = 65
        x_ann = 120
        y_ann = 10
        x_foot = (x_max / 2) - (int(len(ach['achievement_earning']) / 2) * 5.7)
        y_foot = 120

        # Base empty image
        new_im = Image.new('RGB', (x_max, y_max))
        print(f'ach!!! {ach}')
        print(f'cwd: {os.getcwd()}')
        im = Image.open(ach["icon_url"]).convert("RGBA")
        #im = Image.open(requests.get(ach["icon_url"], stream=True).raw)

        # Inserting achievement logo into empty image
        new_im.paste(im, (x_logo,y_logo), im)
        
        # Instancing fonts
        title_font = ImageFont.truetype("arial.ttf", 18)
        desc_font = ImageFont.truetype("arial.ttf", 14)
        foot_font = ImageFont.truetype("arial.ttf", 12)

        def write_lines(text, font, img, x, y, color, max_size=40):
            lines = textwrap.wrap(text, width=max_size)
            y_text = 0
            for line in lines:
                width, height = font.getsize(line)
                img.text((x, y + y_text),line,color,font=font)
                y_text += 15
        
        # Writing texts
        text_im = ImageDraw.Draw(new_im)
        write_lines('Congratulations! You have unlocked:', desc_font, text_im, x_ann, y_ann, (255,255,255), max_size=100)
        write_lines(ach["achievement_name"], title_font, text_im, x_title, y_title, (255,255,255))
        write_lines(ach["achievement_description"], desc_font, text_im, x_desc, y_desc, (135,135,135))
        text_im.text((x_foot, y_foot),ach['achievement_earning'],(0, 202, 224),font=foot_font)

        return new_im


    def mount_image2(self, achievements):
        """
        Mounts the image with all locked and unlocked achievements.
        WARNING: THIS IS VERY BAD DONE, SORRY.

        Parameters
        ----------

        achievements : list
            List of all achievements dicts
        """
        
        # Initial coord values
        x_start = 10
        y_start = 20
        footer_size = 100
        y_max = 1000 + y_start
        x_max = round((len(achievements) * 100) / (y_max - y_start)) * 410
        new_im = Image.new('RGB', (x_max, y_max + footer_size))
        x_index = x_start
        y_index = y_start

        # Instancing fonts
        title_font = ImageFont.truetype(self.config.get_attr('global', 'fontfile'), 20)
        desc_font = ImageFont.truetype(self.config.get_attr('global', 'fontfile'), 18)

        def write_lines(text, font, img, option, x, y):
            lines = textwrap.wrap(text, width=30)
            y_text = 0
            for line in lines:
                width, height = font.getsize(line)
                if option == 'title':
                    img.text((x, y + y_text),line,(255,255,255),font=font)
                else:
                    img.text((x, y + y_text),line,(135,135,135),font=font)
                y_text += 15

        # Inserting achievement info into
        # empty image
        for _cls in achievements:
            cls = achievements[_cls]
            text_im = ImageDraw.Draw(new_im)
            if not cls['icon_url']:
                continue
            if cls['show']:
                im = Image.open(requests.get(cls['icon_url'], stream=True).raw)
                write_lines(
                    cls["achievement_name"], title_font, text_im, 'title', x_index + 110, y_index + 20
                )
                write_lines(
                    cls["achievement_description"], desc_font, text_im, 'description', x_index + 110, y_index + 40
                )
            else:
                # Loading default image whrn achievement was not
                # unlocked by user.
                im = Image.open(requests.get(
                    self.config.get_attr('achievement', 'QuestionmarksIcon')
                    , stream=True).raw
                )
                text_im.text((x_index + 110, y_index + 20),'LOCKED ACHIEVEMENT',(255,255,255),font=title_font)
                text_im.text((x_index + 110, y_index + 40),'????????????',(135,135,135),font=desc_font)
            
            # Pastes the image and set coords for the next one
            im=Image.eval(im,lambda x: x+(x_index+y_index)/30)
            new_im.paste(im, (x_index,y_index), im)
            y_index += 110
            if y_index >= y_max - 110:
                y_index = y_start
                x_index += 410

        # Getting values to the % footer text
        unlocked = len(
            [key for key in achievements if achievements[key]["show"] and achievements[key]['score_total'] != -1]
        )
        unlockable = len([key for key in achievements if achievements[key]['score_total'] != -1])
        completion = f'Completion: {round((unlocked / unlockable) * 100, 2)}% of achievements unlocked'
        text_im.text((50, y_max + 30), completion,(255,255,255),font=title_font)

        return new_im