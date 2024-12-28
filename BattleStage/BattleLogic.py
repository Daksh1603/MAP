import base
import Settings
from BattleStage.AutoCapture import auto_capture

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

tracking_list = None
with open("TrackingMiscrits.txt", "r") as f:
    tracking_list = eval(f.read() or "[]")

def battle(app_window,battle_found_event,resume_live_feed_event,active_window=False):
    global tracking_list
    right_pokemon_name_region = (1180, 72, 80, 15)
    skip_region = (934,607,40,20)
    close_region = (938,782,60,20)
    turn_region = (1031,941,90,15)
    skip_new_miscrit_caught = (930,743,70,20)
    capture_rate_region = (951,150,20,20)
    common_miscrits_file = 'CommonMiscrits.txt'

    need_to_train = None
    register_cap = 1
    
    if battle_found_event.is_set():
        print('Cleared resume_live_feed_event')
        resume_live_feed_event.clear()


        with open(common_miscrits_file, 'r') as file:
            file_content = file.read().strip()
        commonAreaPokemon = ast.literal_eval(file_content)

        print("Battle Started")

        sct = mss()
        ###########################

        timeout = 0
        discord_battle_completed = 0
        raise_alert = 0

        existing_list = None
        with open('capRates.txt', 'r') as file:
            content = file.read().strip()
            existing_list = eval(content)
        

        while True:
            screenshot = sct.grab(app_window)
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            current_miscrit = base.extract_text_region_name(frame, *right_pokemon_name_region)
            close = base.extract_text_region_name(frame,*close_region) # -> close (t1)
            turn = base.extract_text_region_name(frame,*turn_region)
            cap_rate = base.extract_text_region_name(frame, *capture_rate_region)

            if 'turn' in turn.lower() or 'your' in turn.lower():
                ######################## RARE MISCRIT LOGIC ###############################
                if cap_rate not in existing_list:
                        if cap_rate == 'ry:':
                            cap_rate = 'ry'
                        filepath = os.path.join('capRates', f"{cap_rate}.png")
                        cv2.imwrite(filepath, frame)
                        existing_list.append(cap_rate)
                        with open('capRates.txt', 'w') as file:
                            file.write(str(existing_list))
                            
                if register_cap:
                    register_cap = 0
                    if str(cap_rate) in Settings.RATING_ALERT_LIST:
                        raise_alert = 1
                    base.LOG_STRING += f"MISCRIT:{current_miscrit.strip()} CAP_RATE:{cap_rate} "

                if (current_miscrit not in commonAreaPokemon or (Settings.AUTO_CAPTURE_MODE and current_miscrit in tracking_list) or raise_alert) and not timeout and not active_window and Settings.RAISE_DISCORD_ALERT:
                    print('Unkown Miscrit: ')
                    if Settings.AUTO_CAPTURE_MODE:
                        auto_capture(app_window,current_miscrit,cap_rate)

                        with open("TrackingMiscrits.txt", "r") as f:
                            tracking_list = eval(f.read() or "[]")
                        
                        break


                    process = subprocess.Popen(
                        ["python", "-u", os.path.join("BattleStage", "DiscordBot.py")],  # Adjust for Python3 if needed
                        stdin=subprocess.PIPE,          # Allow sending input to stdin
                        stdout=subprocess.PIPE,         # Capture standard output
                        stderr=subprocess.PIPE,         # Capture standard error
                        text=True,                      # Automatically decode the output as text
                        bufsize=1                       # Line-buffered output for real-time reading
                    )

                    # Send the input to the subprocess
                    process.stdin.write(json.dumps(app_window) + "\n")
                    process.stdin.flush()

                    # Capture and display output in real time
                    for line in iter(process.stdout.readline, ""):  # Read lines from stdout
                        print(line, end="")  # Print output as it is produced

                        # Process the output
                        if 'complete' in line.lower() or 'defeated' in line.lower() or 'caught' in line.lower():
                            print('Successful Discord Battle')
                            process.terminate()
                            discord_battle_completed = 1
                            time.sleep(1)
                            break
                        elif 'add' in line.lower():
                            timeout = 1
                            commonAreaPokemon.append(current_miscrit)
                            updated_content = str(commonAreaPokemon)
                            with open(common_miscrits_file, 'w') as file:
                                file.write(updated_content)
                        elif 'skip' in line.lower():
                            timeout = 1
                        else:
                            timeout = 1

                    process.stdout.close()
                    process.stderr.close()
                    process.wait()

                    # Break out of the loop if the condition is met
                    # if process.returncode == 0:
                    #     break
                    
                if discord_battle_completed:
                    break
                ########################### ADD DISCORD LOGIC ############################## Only Defeating Currently, Can Add Capture Logic Later
                print('Attacking!')
                base.click_on(app_window,base.click_coord['attack_1'])
                time.sleep(1.5)
                print('Ending Turn\n#####################################################')
                ############################################################################
            elif 'close' in close.lower():
                need_to_train = check_if_train_req(frame)
                base.click_on(app_window,base.click_coord["close"])
                time.sleep(1.5)
                print("Finished Battle")
                break
            else:
                pass
        
        screenshot = sct.grab(app_window)
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        Skip = base.extract_text_region_name(frame, *skip_new_miscrit_caught)
        if 'skip' in Skip.lower():
            base.click_on(app_window,base.click_coord["caughCritSkip"])
            time.sleep(1)
    
    if need_to_train is not None:
        base.train_check(app_window,*need_to_train)
    resume_live_feed_event.set()

def check_if_train_req(frame):
    miscrit1ready_region = (680,482,93,10)
    miscrit2ready_region = (824,482,93,10)
    miscrit3ready_region = (680,576,93,10)
    miscrit4ready_region = (824,576,93,10)

    M1R = base.extract_text_region_name(frame,*miscrit1ready_region)
    M2R = base.extract_text_region_name(frame,*miscrit2ready_region)
    M3R = base.extract_text_region_name(frame,*miscrit3ready_region)
    M4R = base.extract_text_region_name(frame,*miscrit4ready_region)

    if 'train' in M1R.lower() or 'train' in M2R.lower() or 'train' in M3R.lower() or 'train' in M4R.lower():
        return (M1R,M2R,M3R,M4R)
    else:
        return None