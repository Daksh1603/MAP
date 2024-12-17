import base
import Settings
from BattleStage.BattleLogic import battle
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
from datetime import datetime

tracking_list = None
with open("TrackingMiscrits.txt", "r") as f:
    tracking_list = eval(f.read() or "[]")

def playWildHunt(app_window,shared_data,resume_live_feed_event):
    search_count_wh = [0]
    def search_cooldown(search_count_wh):

        if search_count_wh[0] % 100 == 0 and search_count_wh[0] != 0:
            base.send_discord_webhook(f"We are on Search {search_count_wh[0]}!")

        if search_count_wh[0] >= Settings.WILD_HUNT_SEARCH_COUNT:
            base.send_discord_webhook(f"Tired af, fininshed all {Settings.WILD_HUNT_SEARCH_COUNT} searches , imma chill now ")
            time.sleep(24*60*60)
        else:
            search_count_wh[0] += 1
            time.sleep(20)

    file_name = os.path.join('PlayRegime','Stored Regimes',Settings.REGIME_FILE) # Add file not found when creating UI
    with open(file_name, "r") as file:
        first_line = file.readline().strip() 
    coord = eval(first_line.split()[0])

    ############# LOGGING #######################    
    start_time = datetime.now()
    logs_file = start_time.strftime("Logs %m-%d.txt") #  %H-%M
    logs_file = os.path.join('Logs',logs_file)

    if os.path.exists(logs_file):
        with open(logs_file, 'r') as log:
            log_lines = log.readlines()
            if log_lines:  # Check if the file is not empty
                last_line = log_lines[-1].strip()  # Get the last line and remove any trailing whitespace
                parts = last_line.split(' ')  # Split the line by spaces
                if parts:  # Ensure there are parts to process
                    first_part = parts[0]  # Get the first part
                    separated = first_part.split(':')  # Split it by ':'
                    if separated:  # Ensure there are sub-parts
                        base.SEARCH_COUNT = int(separated[1]) + 1
        with open(logs_file, 'a') as logs:
                    logs.write("##################################### ")
    else:
        open(logs_file, 'w').close()
    ###############################################

    while True:
        print('Search No. : ',search_count_wh[0])
        current_time = datetime.now()
        time_difference = current_time - start_time
        hours, remainder = divmod(time_difference.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        base.LOG_STRING = f"\nSearchNo:{base.SEARCH_COUNT} {int(hours)}h:{int(minutes)}m:{int(seconds)}s "
        base.SEARCH_COUNT += 1
            
        waiting_event = threading.Event()
        battle_found_event = threading.Event()
        
        ##### WILD HUNT #####
        wild_hunt_thread = threading.Thread(target=WildHunt_WRAPPER,args=(app_window,shared_data,battle_found_event,waiting_event,coord,))
        wild_hunt_thread.start()
        search_cooldown_thread = threading.Thread(target=search_cooldown,args=(search_count_wh,))
        search_cooldown_thread.start()
        wild_hunt_thread.join()
        search_cooldown_thread.join()
        ######################

        if not battle_found_event.is_set():
            no_battle_counter +=1
        else:
            no_battle_counter = 0
        if no_battle_counter >= 5:
            base.send_discord_webhook(f"<@{Settings.DISCORD_USER_ID}> The program is stuck lmao xd")
            break

        with open(logs_file, 'a') as logs:
            logs.write(base.LOG_STRING)

def WildHunt_WRAPPER(app_window,shared_data,battle_found_event,resume_live_feed_event,coord):
    def wait_for_battle(battle_found_event,wait_event):
        repeat = 0
        while not battle_found_event.is_set() and repeat<10:
            time.sleep(1)
            repeat+=1
            print(repeat)
        if not battle_found_event.is_set():
            base.LOG_STRING += f"NoBattle "
            print('No Battle...\n')
            wait_event.set()

    print('Clicking on Object...')
    base.click_on(app_window,coord)
    print('Looking for battle...')

    ## BATTLE SCAN ####
    waiting_event = threading.Event()
    battle_thread = threading.Thread(target=base.searching_for_battle,args=(app_window,shared_data,battle_found_event,waiting_event,))
    battle_thread.start()
    waiting_thread = threading.Thread(target=wait_for_battle,args=(battle_found_event,waiting_event,))
    waiting_thread.start()
    battle_thread.join()
    waiting_thread.join()
    ######################
    
    WildHunt(app_window, battle_found_event, resume_live_feed_event)



def WildHunt(app_window,battle_found_event,resume_live_feed_event,active_window=False):
    global tracking_list
    
    right_pokemon_name_region = (1180, 72, 80, 15)
    close_region = (938,782,60,20)
    turn_region = (1031,941,90,15)
    capture_rate_region = (951,150,20,20)
    common_miscrits_file = 'CommonMiscrits.txt'

    auto_capture_successful = 0
    register_cap = 1
    
    if battle_found_event.is_set():
        resume_live_feed_event.clear()
        with open(common_miscrits_file, 'r') as file:
            file_content = file.read().strip()
        commonAreaPokemon = ast.literal_eval(file_content)

        sct = mss()
        screenshot = sct.grab(app_window)
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

        right_pokemon_name = base.extract_text_region_name(frame, *right_pokemon_name_region)
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
                    base.LOG_STRING += f"MISCRIT:{right_pokemon_name.strip()} CAP_RATE:{cap_rate} "
                

                if (right_pokemon_name not in commonAreaPokemon or (Settings.AUTO_CAPTURE_MODE and right_pokemon_name in tracking_list) or raise_alert) and not timeout and not active_window:
                    print('Unkown Miscrit : ',right_pokemon_name)
                    ############################################################################
                    # AUTO CAPTURE
                    if Settings.AUTO_CAPTURE_MODE:
                        auto_capture(app_window,right_pokemon_name,cap_rate)

                        with open("TrackingMiscrits.txt", "r") as f:
                            tracking_list = eval(f.read() or "[]")
                        
                        break

                    # DISCORD BATTLE
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
                            base.click_on(app_window,base.click_coord['heal'])
                            time.sleep(1)
                            break
                        elif 'add' in line.lower():
                            timeout = 1
                            commonAreaPokemon.append(right_pokemon_name)
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
                    battle(app_window, battle_found_event, resume_live_feed_event)
                    ############################################################################
                base.click_on(app_window,base.click_coord["run_away_from_battle"])
                time.sleep(1.5)
            elif 'close' in close.lower():
                base.click_on(app_window,base.click_coord["close"])
                time.sleep(1.5)
                print("Finished Battle")
                break
            else:
                pass

        resume_live_feed_event.set()