import base

import cv2
from mss import mss
import time
import numpy as np
import threading
import asyncio
import subprocess
import json
import ast
import os

def battle(app_window,battle_found_event,resume_live_feed_event,active_window=False):
    right_pokemon_name_region = (1180, 72, 80, 15)
    skip_region = (934,607,40,20)
    close_region = (938,782,60,20)
    turn_region = (1031,941,90,15)
    common_miscrits_file = 'CommonMiscrits.txt'

    # Check if program is stuck
    # if no_battle_counter >= 5:
    #     send_discord_webhook(f"Program Stuck.") exit by turning of both threads counter
    
    if battle_found_event.is_set():
        print('Cleared resume_live_feed_event')
        resume_live_feed_event.clear()


        with open(common_miscrits_file, 'r') as file:
            file_content = file.read().strip()
        commonAreaPokemon = ast.literal_eval(file_content)

        print("Battle Started")

        sct = mss()
        screenshot = sct.grab(app_window)
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

        right_pokemon_name = base.extract_text_region_name(frame, *right_pokemon_name_region)

        timeout = 0
        
        while True:
            screenshot = sct.grab(app_window)
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            skip = base.extract_text_region_name(frame,*skip_region) # -> skip close keep (t1,t2,t3)
            close = base.extract_text_region_name(frame,*close_region) # -> close (t1)
            turn = base.extract_text_region_name(frame,*turn_region)


            if 'turn' in turn.lower() or 'your' in turn.lower():
                ######################## RARE MISCRIT LOGIC ###############################
                if right_pokemon_name not in commonAreaPokemon and not timeout and not active_window:
                    print('Unkown Miscrit: ')

                    # Start the subprocess
                    process = subprocess.Popen(
                        ["python", os.path.join("BattleStage", "DiscordBot.py")],  # Adjust if using python3 or another path
                        stdin=subprocess.PIPE,             # Allow sending input to stdin
                        stdout=subprocess.PIPE,            # Capture standard output (optional)
                        stderr=subprocess.PIPE             # Capture standard error (optional)
                    )

                    stdout, stderr = process.communicate(input=json.dumps(app_window).encode())
                    #print("Subprocess errors:", stderr.decode())

                    outputDiscordBattle = stdout.decode()
                    print("Subprocess Output:", stdout.decode())

                    if 'complete' in outputDiscordBattle.lower():
                        print('Successful Discord Battle')
                        break
                    elif 'add' in outputDiscordBattle.lower():
                        timeout = 1
                        commonAreaPokemon.append(right_pokemon_name)
                        updated_content = str(commonAreaPokemon)
                        with open(common_miscrits_file, 'w') as file:
                            file.write(updated_content)
                    else:
                        timeout = 1
                ########################### ADD DISCORD LOGIC ############################## Only Defeating Currently, Can Add Capture Logic Later
                print('Attacking!')
                base.click_on(app_window,base.click_coord['attack_1'])
                print('Ending Turn\n#####################################################')
                ############################################################################
            elif 'skip' in skip.lower():
                base.click_on(app_window,base.click_coord["keep"])
                time.sleep(1)
                base.click_on(app_window,base.click_coord["close"])
                time.sleep(1)
                base.click_on(app_window,base.click_coord["skip"])
                time.sleep(1.5)
                print("Finished Battle")
                break
            elif 'close' in close.lower():
                base.click_on(app_window,base.click_coord["close"])
                time.sleep(1.5)
                print("Finished Battle")
                break
            else:
                pass

    resume_live_feed_event.set()