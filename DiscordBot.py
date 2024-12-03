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

import base

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
                        discord.ButtonStyle.red if style == "red"
                        else discord.ButtonStyle.green if style == "green"
                        else discord.ButtonStyle.blurple
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
        await channel.send(content="U missed the battle :(", file=discord.File(temp_file_path, filename="screenshot.png"))
        os.remove(temp_file_path)
        return "timeout"

    os.remove(temp_file_path)
    return view.result

async def send_message_to_channel(channel, content, screenshot=None):
    """Sends a simple message to the channel, with an optional image (screenshot)."""
    
    # If screenshot is provided, send the image along with the message
    if screenshot:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
            temp_file_path = temp_file.name
            cv2.imwrite(temp_file_path, screenshot)

            file = discord.File(temp_file_path, filename="screenshot.png")
            await channel.send(content=content, file=file)
            os.remove(temp_file_path)
    else:
        # Just send the content as text if no screenshot is provided
        await channel.send(content=content)

# The automatic loop logic
async def auto_loop():
    """
    Automatically runs a loop, taking screenshots and interacting with Discord.
    """
    skip_region = (934,607,40,20)
    close_region = (938,782,60,20)
    turn_region = (1031,941,90,15)  # Region to check for "turn" text
    sct = mss()
    capturedOnce = 0
    # Wait until the bot is ready
    await bot.wait_until_ready()
    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        #print("Error: Unable to fetch the Discord channel. Check CHANNEL_ID.")
        return

    while True:
        # Wait for Turn -> Send Message #
        frame = None
        turn = 'None'

        while True:
            if 'turn' in turn.lower() or 'your' in turn.lower():
                break
            await asyncio.sleep(1)
            screenshot = sct.grab(app_window)
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            turn = base.extract_text_region_name(frame,*turn_region)

        # Send a message with a screenshot and buttons, and wait for user input
        buttons = [{"Attack 1": "red"}, {"Attack 2": "red"}, {"Add To List":"blue"}, {"Capture": "green"}]
        if capturedOnce:
            buttons = buttons[:-1]
        message = "Rare Miscrit Found!"
        user_input = await send_message_with_buttons(
            channel=channel,
            message=message,
            screenshot=frame,
            buttons=buttons,
            wait_time=30,
        )
        ###################################

        # Wait for Turn -> Actual Play Turn #
        while True:
            if 'turn' in turn.lower() or 'your' in turn.lower():
                break
            await asyncio.sleep(1)
            screenshot = sct.grab(app_window)
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            turn = base.extract_text_region_name(frame,*turn_region)
        # Handle user input
        if user_input == "timeout":
            print("Timeout")
            sys.exit(0)
            break
        elif user_input == "Attack 1":
            base.click_on(app_window,base.click_coord['attack_1'])
        elif user_input == "Attack 2":
            base.click_on(app_window,base.click_coord['attack_2'])
        elif user_input == "Capture":
            capturedOnce = 1
            base.click_on(app_window,base.click_coord['capture'])
            time.sleep(2)
        elif user_input == "Add To List":
            print('Add')
            sys.exit(0)
        else:
            #print("Unexpected input:", user_input)
            break
        time.sleep(5)
        #########################################

        # Scan For Skip Close #
        screenshot = sct.grab(app_window)
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        skip = base.extract_text_region_name(frame,*skip_region) # -> skip close keep (t1,t2,t3)
        close = base.extract_text_region_name(frame,*close_region) # -> close (t1)

        if 'skip' in skip.lower():
            await send_message_to_channel(channel, "Captured Miscrit..", frame)
            base.click_on(app_window,base.click_coord["keep"])
            time.sleep(1)
            base.click_on(app_window,base.click_coord["close"])
            time.sleep(1)
            base.click_on(app_window,base.click_coord["skip"])
            time.sleep(1.5)
            break
        elif 'close' in close.lower():
            await send_message_to_channel(channel, "Defeated Miscrit...")
            base.click_on(app_window,base.click_coord["close"])
            time.sleep(1.5)
            break
        else:
            pass

        ############################################

    print("Complete")
    await bot.close()  # Gracefully shutdown bot
    await bot.logout()


# Automatically start the loop when the bot is ready
@bot.event
async def on_ready():
    #print(f"Bot logged in as {bot.user}")
    # Start the automatic loop
    await auto_loop()

# Gracefully close the bot on script exit
def shutdown_bot():
    """
    Function to gracefully disconnect the bot.
    """
    #print("Shutting down bot...")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(bot.close())

# Register the shutdown function
atexit.register(shutdown_bot)


# Main entry point
if __name__ == "__main__":
    bot.run(TOKEN)