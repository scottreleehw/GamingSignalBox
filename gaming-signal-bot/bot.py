import discord
import os
from dotenv import load_dotenv # type: ignore

load_dotenv()

token = os.getenv('DISCORD_BOT_TOKEN')
channel_id = int(os.getenv('GAMING_CHANNEL_ID'))

device_webhooks={}

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
        
        # Reload existing webhooks
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
    else:
        print(f"Could not find channel with ID {channel_id}")

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
    # Handle commands
    if message.content.startswith("!create webhook "):
        device_name = message.content.replace("!create webhook ", "").strip()
        webhook_url = await create_device_webhook(device_name)
        if webhook_url:
            await message.channel.send(f"✅ Created webhook for **{device_name}**\n```{webhook_url}```")
        return
    
    # Add this new rename command
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
            await message.channel.send(f"✅ Renamed **{old_name}** to **{new_name}**")
            print(f"Renamed device: {old_name} → {new_name}")
        else:
            await message.channel.send(f"❌ Device **{old_name}** not found")
        return
    
    # Add list command to see all devices
    if message.content == "!list devices":
        if device_webhooks:
            device_list = "\n".join([f"• **{name}**" for name in device_webhooks.keys()])
            await message.channel.send(f"📱 **Registered Devices:**\n{device_list}")
        else:
            await message.channel.send("❌ No devices registered yet")
        return


async def handle_webhook_message(message):
    """Handle messages from ESP32 webhooks"""
    print(f"Webhook message: {message.content}")
    print(f"Webhook ID: {message.webhook_id}")

    # Find device name by webhook ID
    deviec_name = "Unknown"
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
    """Create a webhook for a device"""
    try:
        channel = bot.get_channel(channel_id)
        if not channel:
            print(f"Could not find channel {channel_id}")
            return None
        
        # Create webhook
        webhook = await channel.create_webhook(name=f"Gaming-{device_name}")
        webhook_url = webhook.url
        
        # Store it with the device name we want to use
        device_webhooks[device_name] = {
            'webhook': webhook,
            'url': webhook_url,
            'webhook_id': webhook.id  # Store the ID for lookup
        }
        
        print(f"Created webhook for {device_name}: {webhook_url}")
        print(f"Webhook ID: {webhook.id}")
        return webhook_url
        
    except discord.Forbidden:
        print("Bot doesn't have permission to create webhooks!")
        return None
    except Exception as e:
        print(f"Error creating webhook: {e}")
        return None



bot.run(token)