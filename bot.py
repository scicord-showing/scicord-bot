import discord
import random
import json
import os
import aiohttp
from datetime import datetime, timezone
from dotenv import load_dotenv

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)

async def save_attachment(attachment):
    filename = attachment.filename
    file_path = os.path.join(WELCOME_MEDIA_PATH, attachment.filename)

    # Ensure unique filename
    base_name, extension = os.path.splitext(filename)
    counter = 1
    # Check if the file already exists and modify filename if needed
    while os.path.exists(file_path):
        filename = f"{base_name}_{counter}{extension}"
        file_path = os.path.join(WELCOME_MEDIA_PATH, filename)
        counter += 1

    await attachment.save(file_path)
    return filename

async def add_welcome(message, prefix):
    if message.content.startswith(prefix):
        content = message.content[len(prefix):].strip()
    else:
        content = message.content

    attachment = None
    if message.attachments:
        attachment = message.attachments[0]
        filename = await save_attachment(attachment)
    else:
        filename = None

    new_entry = {
        "text": content,
        "media": filename
    }

    update_data_file(new_entry)


def update_data_file(new_entry):
    if os.path.exists(WELCOME_DATA_PATH):
        with open(WELCOME_DATA_PATH, 'r') as file:
            data = json.load(file)
    else:
        data = []
    data.append(new_entry)

    with open(WELCOME_DATA_PATH, 'w') as file:
        json.dump(data, file, indent=4)

    print(f"Saved entry: {new_entry}")

class WelcomeMessage:
    def __init__(self, text, media=None):
        self.text = text 
        self.media = media
        if self.media:
            self.media_name = os.path.basename(media)
        else:
            self.media_name = None

    def _create_embed(self, username, avatar_url, footer_icon_url, footer_text):
        welcome_message = self.text.replace('{user}', username)
        
        embed_var = discord.Embed(
            title="User Get!", 
            description=welcome_message, 
            color=0x350f0a
        )
        embed_var.set_thumbnail(url=avatar_url) # This should still work if user has no pfp
        embed_var.set_image(url=f'attachment://{self.media_name}')
        embed_var.set_footer(text=footer_text, icon_url=footer_icon_url)
        
        return embed_var

    def generate_user_welcome(self, user, guild):
        username = user.name 
        avatar_url = user.avatar.url

        if guild and guild.icon:
            footer_icon_url = guild.icon.url 
        else:
            footer_icon_url = None

        # Current UTC time
        current_utc_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        footer_text = f"Check out rules idk • {current_utc_time} UTC"

        if self.media:
            file = discord.File(self.media, filename=self.media_name)
        else:
            file = None
        embed = self._create_embed(username, avatar_url, footer_icon_url, footer_text)

        return file, embed

def random_welcome_message():
    with open(WELCOME_DATA_PATH, 'r') as file:
        data = json.load(file)
    random_entry = random.choice(data)
    if random_entry['media']:
        media_path = os.path.join(WELCOME_MEDIA_PATH, random_entry['media'])
    else:
        media_path = None
    return WelcomeMessage(random_entry['text'], media_path)

async def send_welcome(member):
    print(f'{member.name} joined')
    W = random_welcome_message() 
    try:
        # TODO: probably better to use cached versions of this, once retrieved
        guild = await client.fetch_guild(GUILD_ID)
        welcome_channel = await client.fetch_channel(WELCOME_CHANNEL_ID)

        file, embed_object = W.generate_user_welcome(member, guild)
        welcome_message = await welcome_channel.send(f'<@{member.id}>', file=file, embed=embed_object)
        await welcome_message.add_reaction('👆🏿') # could use custom emoji?
        print('Sent welcome message')
    except Exception as e:
        print(f'Shit. {e}')

@client.event
async def on_ready():
    print(f'Successfully logged in as {client.user}')

@client.event 
async def on_member_join(member):
   await send_welcome(member)

@client.event 
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello') and True: # For debugging
        await send_welcome(message.author)

    prefix = '$cum'
    if message.content.startswith(prefix) and message.channel.id == SUGGESTIONS_CHANNEL_ID:
        await message.add_reaction('👍')
        def confirmation(reaction, user): # TODO: add role checking
            return True and str(reaction.emoji) == '👍'

        await client.wait_for('reaction_add', check=confirmation)
        await add_welcome(message, prefix)


WELCOME_DATA_PATH = 'data/data.json'
WELCOME_MEDIA_PATH = 'data/media'

# Access the environment variables
# Perhaps this should be stored somewhere other than .env 
# Just don't hard code the token like an idiot
SUGGESTIONS_CHANNEL_ID = int(os.getenv('SUGGESTIONS_CHANNEL_ID'))
WELCOME_CHANNEL_ID = int(os.getenv('WELCOME_CHANNEL_ID'))
GUILD_ID = int(os.getenv('GUILD_ID'))
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

client.run(DISCORD_TOKEN)

