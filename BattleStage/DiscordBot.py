import discord
from discord.ext import commands
from discord.ui import Button, View
import cv2
from mss import mss
import numpy as np
import tempfile
import os
import asyncio
import atexit
import sys
import json
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import base
import Settings

HD_TAB = Settings.HEAVY_DAMAGE[0]
HD_NO = Settings.HEAVY_DAMAGE[1]

MD_TAB = Settings.MEDIUM_DAMAGE[0]
MD_NO = Settings.MEDIUM_DAMAGE[1]


LD_TAB = Settings.LIGHT_DAMAGE[0]
LD_NO = Settings.LIGHT_DAMAGE[1]

BUFF_TAB = Settings.NON_DAMAGE[0]
BUFF_NO = Settings.NON_DAMAGE[1]

#input_data = sys.stdin.read()
input_data = json.dumps({'top': -56, 'left': 2552, 'width': 1936, 'height': 1096})

app_window = json.loads(input_data)


# Discord bot setup
TOKEN = "MTMxMzIyOTQwMzgxMDk1OTQ1MQ.G9ALgc.Txp8YJUToVj8E-d8YoslV2eAnFwz9o4wTHgxS8"
# CHANNEL_ID = 781141447369162803  # General Channel
CHANNEL_ID = 1313425120567496715
USER_ID = 236268536950030337

# Intents and bot initialization
intents = discord.Intents.default()
bot = discord.Client(intents=intents)

# Function to send a message with buttons
async def send_message_with_buttons(channel, message, screenshot, buttons, wait_time=10):
    message = f"<@{USER_ID}> {message}"

    class ButtonView(View):
        def __init__(self, timeout):
            super().__init__(timeout=timeout)
            self.result = None

            for button in buttons:
                for label, style in button.items():
                    button_style = (
                    discord.ButtonStyle.danger if style == "red" else
                    discord.ButtonStyle.success if style == "green" else
                    discord.ButtonStyle.secondary if style == "grey" else
                    discord.ButtonStyle.primary
                    )
                    button_instance = Button(label=label, style=button_style)
                    button_instance.callback = self.create_button_callback(label)
                    self.add_item(button_instance)

        def create_button_callback(self, label):
            async def button_callback(interaction: discord.Interaction):
                self.result = label
                #await interaction.response.send_message(f"You selected: {self.result}", ephemeral=True)
                # Delete the original message once a button is clicked
                await interaction.message.delete()
                self.stop()
            return button_callback

        async def on_timeout(self):
            # Disable buttons after timeout
            for child in self.children:
                if isinstance(child, Button):
                    child.disabled = True

    # Create temporary file for the screenshot
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
        temp_file_path = temp_file.name
        cv2.imwrite(temp_file_path, screenshot)

        file = discord.File(temp_file_path, filename="screenshot.png")
        view = ButtonView(timeout=wait_time)
        msg = await channel.send(content=message, file=file, view=view)

    # Wait for user interaction or timeout via the view
    await view.wait()

    if view.result is None:  # Check if there was no interaction (timeout)
        await msg.delete()  # Delete the original message on timeout

        # Send new message saying the user missed the battle
        # await channel.send(content="U missed the battle :(", file=discord.File(temp_file_path, filename="screenshot.png"))
        os.remove(temp_file_path)
        return "timeout"

    os.remove(temp_file_path)
    return view.result

async def send_message_to_channel(channel, content, screenshot=None):
    """Sends a simple message to the channel, with an optional image (screenshot)."""
    
    # If screenshot is provided, send the image along with the message
    print('Preparing to send message...')
    temp_file_path = None
    try:
        if screenshot is not None:
            print('Screenshot provided. Preparing to send with attachment...')
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
                temp_file_path = temp_file.name
                cv2.imwrite(temp_file_path, screenshot)
                print('CV2 Written...')

                file = discord.File(temp_file_path, filename="screenshot.png")
                await asyncio.wait_for(channel.send(content=content, file=file), timeout=15)
        else:
            print('Sending text message...')
            await asyncio.wait_for(channel.send(content=content), timeout=15)

        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)    
        print('Message sent successfully!')

    except asyncio.TimeoutError:
        print("Timeout: Failed to send the message.")
    except Exception as e:
        print(f"Error sending message: {e}")

# The automatic loop logic
async def auto_loop():
    """
    Automatically runs a loop, taking screenshots and interacting with Discord.
    """
    miscritRegion = (1060,630,250,200) # Make more defined
    right_pokemon_name_region = (1180, 72, 80, 15)
    skip_region = (934,607,40,20)
    close_region = (938,782,60,20)
    turn_region = (1031,941,90,15) # Region to check for "turn" text
    sct = mss()
    capturedOnce = 0
    on_tab = 1
    timeoutTurnTime = 5
    miscritFrame = None
    miscritName = 'Unknown'
    # Wait until the bot is ready
    await bot.wait_until_ready()
    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        #print("Error: Unable to fetch the Discord channel. Check CHANNEL_ID.")
        return

    while True:
        frame = None
        turn = 'None'
        
        print('Waiting for turn to send message')
        # Wait for Turn -> Send Message #
        repeat = 0
        while repeat<=timeoutTurnTime:
            if 'turn' in turn.lower() or 'your' in turn.lower():
                print('Our Turn')
                break
            await asyncio.sleep(1)
            repeat+=1
            print(repeat)
            screenshot = sct.grab(app_window)
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            turn = base.extract_text_region_name(frame,*turn_region)

        # Send a message with a screenshot and buttons, and wait for user input
        if miscritFrame is None:
            miscritFrame = frame
            miscritName = base.extract_text_region_name(frame, *right_pokemon_name_region)
        print('Sending Message')
        buttons = [{"Heavy Damage": "red"},{"Medium Damage": "red"},{"Light Damage":"blue"}, {"Buff/Debuff": "grey"}, {"Capture": "green"}, {"Add To List": "blue"},{"Skip":"blue"}]
        if capturedOnce:
            buttons = [button for button in buttons if "Capture" not in button]
            buttons.append({'Capture Again':'green'})
        message = f"Rare Miscrit Found : {miscritName}"
        user_input = await send_message_with_buttons(
            channel=channel,
            message=message,
            screenshot=frame,
            buttons=buttons,
            wait_time=10,
        )
        print('Message Sent')
        ###################################

        # Wait for Turn -> Actual Play Turn #
        print('Waiting for turn to Play')
        repeat = 0
        while repeat<=timeoutTurnTime:
            if 'turn' in turn.lower() or 'your' in turn.lower():
                print('Our Turn')
                break
            await asyncio.sleep(1)
            repeat+=1
            print(repeat)
            screenshot = sct.grab(app_window)
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            turn = base.extract_text_region_name(frame,*turn_region)
        # Handle user input
        print('Playing Turn...')
        if user_input == "timeout":
            while on_tab > BUFF_TAB:
                base.click_on(app_window,base.click_coord['attackLeftTab'])
                time.sleep(0.5)
                on_tab-=1
            while on_tab < BUFF_TAB:
                base.click_on(app_window,base.click_coord['attackRightTab'])
                time.sleep(0.5)
                on_tab+=1

            base.click_on(app_window,base.click_coord[f'attack_{BUFF_NO}'])
            # print("Timeout")
            # sys.exit(0)
            # break

        elif user_input == "Heavy Damage":

            while on_tab > HD_TAB:
                base.click_on(app_window,base.click_coord['attackLeftTab'])
                time.sleep(0.5)
                on_tab-=1
            while on_tab < HD_TAB:
                base.click_on(app_window,base.click_coord['attackRightTab'])
                time.sleep(0.5)
                on_tab+=1

            base.click_on(app_window,base.click_coord[f'attack_{HD_NO}'])
        
        elif user_input == "Medium Damage":

            while on_tab > MD_TAB:
                base.click_on(app_window,base.click_coord['attackLeftTab'])
                time.sleep(0.5)
                on_tab-=1
            while on_tab < MD_TAB:
                base.click_on(app_window,base.click_coord['attackRightTab'])
                time.sleep(0.5)
                on_tab+=1

            base.click_on(app_window,base.click_coord[f'attack_{MD_NO}'])
            
        elif user_input == "Light Damage":

            while on_tab > LD_TAB:
                base.click_on(app_window,base.click_coord['attackLeftTab'])
                time.sleep(0.5)
                on_tab-=1
            while on_tab < LD_TAB:
                base.click_on(app_window,base.click_coord['attackRightTab'])
                time.sleep(0.5)
                on_tab+=1

            base.click_on(app_window,base.click_coord[f'attack_{LD_NO}'])

        elif user_input == "Buff/Debuff":

            while on_tab > BUFF_TAB:
                base.click_on(app_window,base.click_coord['attackLeftTab'])
                time.sleep(0.5)
                on_tab-=1
            while on_tab < BUFF_TAB:
                base.click_on(app_window,base.click_coord['attackRightTab'])
                time.sleep(0.5)
                on_tab+=1

            base.click_on(app_window,base.click_coord[f'attack_{BUFF_NO}'])

        elif user_input == "Capture":
            capturedOnce = 1
            base.click_on(app_window,base.click_coord['capture'])
            time.sleep(3)

        elif user_input == "Capture Again":
            base.click_on(app_window,base.click_coord['capture'])
            time.sleep(1.5)
            base.click_on(app_window,base.click_coord['capture2prompt'])
            time.sleep(3)
            
        elif user_input == "Add To List":
            while on_tab > 1:
                base.click_on(app_window,base.click_coord['attackLeftTab'])
                time.sleep(0.5)
                on_tab-=1
            print('Add')
            sys.exit(0)

        elif user_input == "Skip":
            while on_tab > 1:
                base.click_on(app_window,base.click_coord['attackLeftTab'])
                time.sleep(0.5)
                on_tab-=1
            print('Skip')
            sys.exit(0)
        else:
            break
        print('Turn Played')
        time.sleep(5)
        #########################################

        # Scan For Skip Close #
        print('Scanning results...')
        screenshot = sct.grab(app_window)
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        skip = base.extract_text_region_name(frame,*skip_region) # -> skip close keep (t1,t2,t3)
        close = base.extract_text_region_name(frame,*close_region) # -> close (t1)

        if 'skip' in skip.lower():
            #await send_message_to_channel(channel, "Captured Miscrit.. LFG",screenshot=miscritFrame[miscritRegion[1]:miscritRegion[1] + miscritRegion[3],miscritRegion[0]:miscritRegion[0] + miscritRegion[2]])
            base.click_on(app_window,base.click_coord["skip"])
            time.sleep(2)
            base.click_on(app_window,base.click_coord["close"])
            time.sleep(2)

            screenshot = sct.grab(app_window)
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            await send_message_to_channel(channel, "Captured Miscrit.. LFG",screenshot=frame[int(frame.shape[0]*0.3):int(frame.shape[0]*0.7), int(frame.shape[1]*0.3):int(frame.shape[1]*0.7)]) # add only stats part ##### TEMP ONLY CENTRAL 40% 
            
            base.click_on(app_window,base.click_coord["keep"])
            time.sleep(1)
            print('Caught')
            break
        elif 'close' in close.lower():
            await send_message_to_channel(channel, "The Miscrit Dipped :(",screenshot=miscritFrame[miscritRegion[1]:miscritRegion[1] + miscritRegion[3],miscritRegion[0]:miscritRegion[0] + miscritRegion[2]])
            base.click_on(app_window,base.click_coord["close"])
            time.sleep(1.5)
            print('Defeated')
            break
        else:
            print('Neither : The Battle Continues \n ##################################################### \n')
            pass
        ############################################

    print("Complete")
    await bot.close()  # Gracefully shutdown bot
    await bot.logout()


# Automatically start the loop when the bot is ready
@bot.event
async def on_ready():
    await auto_loop()

# Gracefully close the bot on script exit
def shutdown_bot():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(bot.close())

# Register the shutdown function
atexit.register(shutdown_bot)


# Main entry point
if __name__ == "__main__":
    bot.run(TOKEN)