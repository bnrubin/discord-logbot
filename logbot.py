#!/usr/bin/env python
from datetime import datetime, timezone
from discord.ext import commands
from dotenv import dotenv_values
from pathlib import Path
from pprint import pprint
from urllib.parse import quote_plus
from urllib.parse import urlparse
import discord
import hashlib
import logging
import motor.motor_asyncio
import requests
import sys
import uuid

discord.utils.setup_logging()

description = """Discord bot intended to log responses from AI image creation bots"""

secrets = dotenv_values('.env')

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='?', description=description, intents=intents)

client = motor.motor_asyncio.AsyncIOMotorClient(username=secrets['MONGO_USER'], password=secrets['MONGO_PASS'], authSource='logbot')

db = client['logbot']

@bot.event
async def on_ready():
    logging.info(f'Logged in as {bot.user} (ID: {bot.user.id})')


def download_image(url):
    resp = requests.get(url)
    
    parsed = urlparse(url)
    ext = Path(parsed.path).suffix

    
    filename = '{}{}'.format(uuid.uuid4(), ext)
    filepath = Path(secrets['IMAGE_PATH'], filename)

    with open(filepath, 'wb') as fd:
        fd.write(resp.content)

    return filename


@bot.event
async def on_message_edit(before, after):
    if not after.author.bot:
        return

    if after.embeds and after.embeds[0].title == 'Done!':
        data = after.embeds[0]

        if data.image.width == 512:
            logging.debug('CSAM response from bot')
            return
        
        fname = download_image(data.image.url)
        now = datetime.now(tz=timezone.utc)

        record =    {'prompt': data.description,
                    'user': {
                        'id': after.interaction.user.id,
                        'name': after.interaction.user.global_name,
                        'display': after.interaction.user.display_name,
                    },
                    'message_id': after.id,
                    'filename': fname,
                    'created': now,
                    'updated': now,
                    'deleted': False,
                    'channel': {
                        'id': after.guild.id,
                        'server': after.guild.name,
                        'name': after.channel.name,
                    }
                 }

        result = await db.ai_interactions.insert_one(record)
        logging.debug('Added {} to db'.format(result.inserted_id))

    # handle embed deletion

    if before.embeds and not after.embeds:
        logging.debug('embed deleted!')
        now = datetime.now(tz=timezone.utc)
        result = await db.ai_interactions.update_one({'message_id': before.id}, {'$set': {'deleted': True, 'updated': now}})

    

bot.run(secrets['DISCORD_TOKEN'])
