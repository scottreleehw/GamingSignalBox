import discord
import os
from dotenv import load_dotenv # type: ignore
import json
import aiofiles # type: ignore
from pathlib import Path

# Webhook storage file
WEBHOOKS_FILE = "webhooks.json"

async def load_webhooks():
    """Load webhooks from JSON file"""
    try:
        if Path(WEBHOOKS_FILE).exists():
            async with aiofiles.open(WEBHOOKS_FILE, 'r') as f:
                content = await f.read()
                return json.loads(content)
        return {}
    except Exception as e:
        print(f"Error loading webhooks: {e}")
        return {}

async def save_webhooks(webhooks_data):
    """Save webhooks to JSON file"""
    try:
        async with aiofiles.open(WEBHOOKS_FILE, 'w') as f:
            await f.write(json.dumps(webhooks_data, indent=2))
        print(f"Saved {len(webhooks_data)} webhooks to {WEBHOOKS_FILE}")
    except Exception as e:
        print(f"Error saving webhooks: {e}")

load_dotenv()

token = os.getenv('DISCORD_BOT_TOKEN')
channel_id = int(os.getenv('GAMING_CHANNEL_ID'))

device_webhooks = {}

# Create intents
intents = discord.Intents.default()
intents.message_content = True

bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has logged in!')
    
    channel = bot.get_channel(channel_id)
    if channel:
        await channel.send("🎮 Gaming bot is online!")
        
        # Load webhooks from JSON file first
        saved_webhooks = await load_webhooks()
        
        # Get current webhooks from Discord
        webhooks = await channel.webhooks()
        
        for webhook in webhooks:
            if webhook.name.startswith("Gaming-"):
                device_name = webhook.name.replace("Gaming-", "")
                device_webhooks[device_name] = {
                    'webhook': webhook,
                    'url': webhook.url,
                    'webhook_id': webhook.id
                }
                print(f"Reloaded webhook for {device_name}")
        
        # Merge with saved data (in case of any discrepancies)
        for device_name, data in saved_webhooks.items():
            if device_name not in device_webhooks:
                # This handles cases where webhook exists in file but not Discord
                print(f"Webhook for {device_name} exists in file but not Discord")
        
        # Save current state
        webhook_data = {name: {'url': data['url'], 'webhook_id': data['webhook_id']} 
                       for name, data in device_webhooks.items()}
        await save_webhooks(webhook_data)

@bot.event
async def on_message(message):
    # Don't respond to our own messages
    if message.author == bot.user:
        return
    
    print(f"Message from {message.author}: {message.content}")
    
    # Handle commands
    if message.content.startswith("!create webhook "):
        device_name = message.content.replace("!create webhook ", "").strip()
        webhook_url = await create_device_webhook(device_name)
        if webhook_url:
            await message.channel.send(f"✅ Created webhook for **{device_name}**\n```{webhook_url}```")
        return
    
    # Rename command
    if message.content.startswith("!rename "):
        # Format: !rename OldName NewName
        parts = message.content.replace("!rename ", "").strip().split(" ", 1)
        if len(parts) != 2:
            await message.channel.send("❌ Format: `!rename OldName NewName`")
            return
            
        old_name, new_name = parts
        
        if old_name in device_webhooks:
            # Move the webhook data to new name
            device_webhooks[new_name] = device_webhooks[old_name]
            del device_webhooks[old_name]
            
            # Save to JSON file
            webhook_data = {name: {'url': data['url'], 'webhook_id': data['webhook_id']} 
                           for name, data in device_webhooks.items()}
            await save_webhooks(webhook_data)
            
            await message.channel.send(f"✅ Renamed **{old_name}** to **{new_name}**")
            print(f"Renamed device: {old_name} → {new_name}")
        else:
            await message.channel.send(f"❌ Device **{old_name}** not found")
        return
    
    # List devices command
    if message.content == "!list devices":
        if device_webhooks:
            device_list = "\n".join([f"• **{name}**" for name in device_webhooks.keys()])
            await message.channel.send(f"📱 **Registered Devices:**\n{device_list}")
        else:
            await message.channel.send("❌ No devices registered yet")
        return
    
    # Check if this is a webhook message (from ESP32)
    if message.webhook_id:
        await handle_webhook_message(message)
        return
    
    # Check for gaming signals from humans
    content_lower = message.content.lower()
    
    if any(phrase in content_lower for phrase in ["want to game", "gaming time", "let's play", "🎮"]):
        # Someone wants to game!
        await message.channel.send(f"🎮 **{message.author.display_name}** wants to play!")
        
        # Send broadcast message for ESP32s to read
        broadcast_message = f"SIGNAL:{message.author.display_name}:GAME_ON"
        await message.channel.send(broadcast_message)
        
        print(f"GAMING SIGNAL from {message.author.display_name}")

    # Delete webhook command
    if message.content.startswith("!delete webhook "):
        device_name = message.content.replace("!delete webhook ", "").strip()
        
        if device_name in device_webhooks:
            try:
                # Delete from Discord
                webhook = device_webhooks[device_name]['webhook']
                await webhook.delete()
                
                # Remove from memory
                del device_webhooks[device_name]
                
                # Save updated JSON
                webhook_data = {name: {'url': data['url'], 'webhook_id': data['webhook_id']} 
                            for name, data in device_webhooks.items()}
                await save_webhooks(webhook_data)
                
                await message.channel.send(f"✅ Deleted webhook for **{device_name}**")
                print(f"Deleted webhook for {device_name}")
            except Exception as e:
                await message.channel.send(f"❌ Error deleting webhook: {str(e)}")
        else:
            await message.channel.send(f"❌ Device **{device_name}** not found")
        return

async def handle_webhook_message(message):
    """Handle messages from ESP32 webhooks"""
    print(f"Webhook message: {message.content}")
    print(f"Webhook ID: {message.webhook_id}")

    # Find device name by webhook ID
    device_name = "Unknown"  # Fixed typo here
    for name, webhook_data in device_webhooks.items():
        if webhook_data['webhook_id'] == message.webhook_id:
            device_name = name
            break

    print(f"Identified device: {device_name}")

    if "🎮" in message.content or "wants to game" in message.content.lower():
        # ESP gaming signal
        await message.channel.send(f"🎮 **{device_name}** (ESP32) wants to play!")

        broadcast_message = f"SIGNAL:{device_name}:GAME_ON"
        await message.channel.send(broadcast_message)

        print(f"ESP32 GAMING SIGNAL from {device_name}")

async def create_device_webhook(device_name):
    """Create a webhook for a device and save to JSON"""
    try:
        channel = bot.get_channel(channel_id)
        if not channel:
            print(f"Could not find channel {channel_id}")
            return None
        
        # Create webhook
        webhook = await channel.create_webhook(name=f"Gaming-{device_name}")
        webhook_url = webhook.url
        
        # Store it
        device_webhooks[device_name] = {
            'webhook': webhook,
            'url': webhook_url,
            'webhook_id': webhook.id
        }
        
        # Save to JSON file
        webhook_data = {name: {'url': data['url'], 'webhook_id': data['webhook_id']} 
                       for name, data in device_webhooks.items()}
        await save_webhooks(webhook_data)
        
        print(f"Created webhook for {device_name}: {webhook_url}")
        return webhook_url
        
    except Exception as e:
        print(f"Error creating webhook: {e}")
        return None

bot.run(token)