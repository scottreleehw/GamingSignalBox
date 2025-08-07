# Gaming Signal Bot

A Discord bot that coordinates gaming sessions between friends using ESP32-powered physical gaming signal boxes.

## Overview

When someone wants to play games, they can either:
- Send a message in Discord with gaming keywords
- Press a physical button on their ESP32 gaming box

The bot will then:
- Notify everyone in the channel
- Send signals to light up all other ESP32 boxes
- Track who's online and ready to game

## Prerequisites

- Python 3.11+
- Discord server with admin permissions
- `uv` package manager installed

## Discord Setup

### 1. Create Discord Application
1. Go to https://discord.com/developers/applications
2. Click "New Application"
3. Name it (e.g., "Gaming Signal Bot")
4. Go to **Bot** section
5. Click "Add Bot"
6. Copy the **Bot Token** (save for later)
7. Enable **"Message Content Intent"** under Privileged Gateway Intents
8. Save changes

### 2. Set Bot Permissions
1. Go to **OAuth2 → URL Generator**
2. Select scopes: 
   - ✅ `bot`
   - ✅ `applications.commands` (for slash commands)
   - ✅ `webhook.incoming` (for webhook creation)
3. Select bot permissions:
   - ✅ View Channels
   - ✅ Send Messages
   - ✅ Read Message History
   - ✅ Manage Webhooks
4. Copy the generated URL and open it in browser
5. Select your Discord server and authorize

### 3. Create Gaming Channel
1. Create a private channel for gaming signals (e.g., `#gaming-signals`)
2. Right-click the channel → "Copy Channel ID" (requires Developer Mode enabled)
3. Ensure the bot has access to this channel

## Installation

### 1. Clone and Setup Project
```bash
git clone <repository-url>
cd gaming-signal-bot
uv init
uv add discord.py python-dotenv
```

### 2. Create Environment File
Create a `.env` file in the project root:
```env
DISCORD_BOT_TOKEN=your_bot_token_here
GAMING_CHANNEL_ID=your_channel_id_here
```

### 3. Run the Bot
```bash
uv run bot.py
```

You should see:
- "gaming-notification-test#XXXX has logged in!" in terminal
- "🎮 Gaming bot is online!" message in your Discord channel

## Usage

### Bot Commands

| Command | Description | Example |
|---------|-------------|---------|
| `!create webhook DeviceName` | Create webhook for ESP32 device | `!create webhook Alice` |
| `!rename OldName NewName` | Rename a device | `!rename Alice AliceESP32` |
| `!list devices` | Show all registered devices | `!list devices` |

### Human Gaming Signals

Send any message containing these phrases:
- "want to game"
- "gaming time"
- "let's play"
- "🎮"

The bot will broadcast the signal to all ESP32 devices.

### ESP32 Setup

Each ESP32 gaming box needs:
1. **Webhook URL**: Create using `!create webhook DeviceName`
2. **Device Name**: Used for identification
3. **WiFi Access**: To send signals and receive broadcasts
#### 4. Configure Credentials ####
1. Copy `src/config.h.example` to `src/config.h`
2. Update `src/config.h` with your actual credentials:
   - WiFi SSID and password
   - Discord webhook URL (from `!create webhook` command)
   - Discord bot token and channel ID
   - Unique device name for this ESP32

## ESP32 Gaming Box Setup

### Hardware Requirements
Each ESP32 gaming box needs:
- ESP32 development board (ESP-WROOM-32 recommended)
- SPST switch (momentary or toggle)
- Breadboard and jumper wires
- USB-C cable for power
- 220Ω resistor (optional, for external LED)

### Hardware Wiring
```
ESP32 GPIO 4 ──── One terminal of SPST switch
ESP32 GND ───────── Other terminal of SPST switch

Built-in LED on GPIO 2 (no wiring needed)
```

### Software Setup

#### 1. Install PlatformIO
- Install VSCode
- Install PlatformIO IDE extension
- Restart VSCode

#### 2. Create ESP32 Project
1. Click PlatformIO icon → "New Project"
2. Name: "gaming-signal-esp32"
3. Board: "Espressif ESP32 Dev Module"
4. Framework: Arduino

#### 3. Install Required Libraries
In PlatformIO, install these libraries:
- ArduinoJson (for Discord message parsing)

#### 4. Rename config.h.example to config.h
Update these values in `src/config.cpp`:
```cpp
// WiFi credentials
const char* ssid = "YOUR_WIFI_NAME";
const char* password = "YOUR_WIFI_PASSWORD";

// Discord configuration (get these from bot setup)
const char* webhook_url = "YOUR_WEBHOOK_URL";    // From !create webhook command
const char* bot_token = "YOUR_BOT_TOKEN";        // From Discord Developer Portal
const char* channel_id = "YOUR_CHANNEL_ID";      // Same as Discord bot
const char* device_name = "YourName";            // Unique name for this box
```

#### 5. Upload and Test
1. Connect ESP32 via USB
2. Install CP2102 drivers if needed
3. Upload code using PlatformIO
4. Open Serial Monitor (115200 baud) to verify connection

### ESP32 Behavior

#### Sending Signals
- **Switch ON**: 3 LED blinks + sends Discord signal + LED stays on
- **Switch OFF**: Resets signal + LED turns off

#### Receiving Signals
- **Discord message** ("I want to game"): LED turns on and stays on
- **Other ESP32 signals**: LED turns on and stays on
- **Discord reset** ("gaming off"): LED turns off

#### Reset Options
1. **Physical**: Flip switch to OFF position
2. **Discord**: Type "gaming off", "reset gaming", or "stop gaming" in channel

### Troubleshooting ESP32

#### Upload Issues
- Install CP2102 USB drivers
- Try holding BOOT button during upload
- Check correct board selection in PlatformIO

#### WiFi Connection Issues
- Verify SSID and password are correct
- Check 2.4GHz network (ESP32 doesn't support 5GHz)
- Ensure network allows device connections

#### Discord Integration Issues
- Verify bot token and channel ID are correct
- Check bot has "Read Message History" permission
- Confirm webhook URL is valid

#### LED Not Working
- Verify GPIO 2 is available (built-in LED)
- For external LED: GPIO 5 → 220Ω resistor → LED+ / LED- → GND
- Check switch wiring: GPIO 4 to one terminal, GND to other

### Creating Multiple Boxes

For each additional ESP32:
1. **Create new webhook**: `!create webhook FriendName` in Discord
2. **Use unique device name**: Change `device_name` in code
3. **Use friend's webhook URL**: Update `webhook_url` in code
4. **Keep everything else the same**: WiFi, bot token, channel ID

### ESP32 Integration Details

#### Sending Signals (ESP32 → Discord)
ESP32s send POST requests to their webhook URL:
```json
{
  "content": "🎮 Alice wants to game!"
}
```

#### Receiving Signals (Discord → ESP32)
ESP32s poll the Discord channel every 3 seconds for messages starting with:
```
SIGNAL:DeviceName:GAME_ON
```

## File Structure

```
gaming-signal-bot/
├── .env                 # Environment variables (DO NOT COMMIT)
├── bot.py              # Main bot code
├── pyproject.toml      # UV project configuration
├── README.md           # This file
└── .gitignore          # Exclude .env and other files
```

## Deployment Options

### Option 1: Local Development
- Run `uv run bot.py` on your computer
- Bot stops when computer sleeps/shuts down

### Option 2: Always-On Server
- Deploy to Raspberry Pi, VPS, or cloud service
- Recommended for production use

### Option 3: Cloud Platforms
- Heroku, Railway, DigitalOcean App Platform
- May require slight modifications for deployment

## Troubleshooting

### Bot Won't Connect
- ✅ Check `DISCORD_BOT_TOKEN` in `.env`
- ✅ Verify bot is added to server
- ✅ Check "Message Content Intent" is enabled

### Can't Create Webhooks
- ✅ Ensure bot has "Manage Webhooks" permission
- ✅ Check bot can access the gaming channel

### ESP32 Not Detected
- ✅ Verify webhook URL is correct
- ✅ Check device is sending proper JSON format
- ✅ Look for webhook messages in Discord channel

### Bot Forgets Devices After Restart
This is normal! The bot automatically reloads existing webhooks on startup.

## Security Notes

- **Never commit `.env` file** to version control
- **Keep bot token private** - regenerate if exposed
- **Limit bot permissions** to only what's needed
- **Use private channels** for gaming signals

## Hardware Requirements (ESP32)

Each gaming box needs:
- ESP32 development board
- Momentary switch/button
- LED indicator
- Resistors (220Ω for LED, 10kΩ for button pull-up)
- USB power source
- WiFi network access

## Future Features

- [ ] Device online/offline status tracking
- [ ] Gaming session timers
- [ ] Multiple signal types (ready, busy, offline)
- [ ] Web dashboard for status monitoring
- [ ] Integration with voice channels
- [ ] Mobile app notifications

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/new-feature`)
3. Commit changes (`git commit -am 'Add new feature'`)
4. Push to branch (`git push origin feature/new-feature`)
5. Create Pull Request

## License

[Add your license here]

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review Discord Developer Documentation
3. Open an issue in this repository