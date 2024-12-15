import base
import Settings

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

USER_ID = 236268536950030337

miscritRegion = (1060,630,250,200)
right_pokemon_name_region = (1180, 72, 80, 15)
skip_region = (934,607,40,20)
close_region = (938,782,60,20)
turn_region = (1031,941,90,15)
capture_rate_region = (951,150,20,20)
skip_new_miscrit_caught = (930,743,70,20)
common_miscrits_file = 'CommonMiscrits.txt'
tracking_miscrits_file = 'TrackingMiscrits.txt'

def auto_capture(app_window,miscrit,capRate):
    sct = mss()
    move = Settings.AUTO_CAPTURE_MOVE
    ########### VIDEO LOGGING BASE ############# 
    base_folder = "CaptureAutomaticVODS" # create directory
    date_folder = datetime.now().strftime("%m_%d")
    save_path = os.path.join(base_folder, date_folder)
    os.makedirs(save_path, exist_ok=True)
    output_file = os.path.join(save_path, f"Search No. {base.SEARCH_COUNT}.avi")

    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    fps = 1  # Frames per second
    out = cv2.VideoWriter(output_file, fourcc, fps, (app_window.get('width'), app_window.get('height')))
    ############################################

    with open(common_miscrits_file, 'r') as file:
        file_content = file.read().strip()
    commonAreaPokemon = ast.literal_eval(file_content)

    max_capture = None
    newMiscrit = None
    miscritFrame = None

    if miscrit not in commonAreaPokemon and 'ee' != newMiscrit.lower(): 
        max_capture = 1 + Settings.AUTO_CAPTURE_MAX
        newMiscrit = 1
    elif capRate in Settings.AUTO_CAPTURE_PLAT_LIST: # add flag for discord battle auto_capture_plat  | also if exotic or legendary 
        max_capture = 1 + Settings.AUTO_CAPTURE_MAX
    else: # add flag for discord battle auto_capture_noplat
        max_capture = 1
    
    cap_count = 0
    platWasted = 0
    on_tab = 1

    while True:
        screenshot = sct.grab(app_window)
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        out.write(frame)
        skip = base.extract_text_region_name(frame,*skip_region) # -> skip close keep (t1,t2,t3)
        close = base.extract_text_region_name(frame,*close_region) # -> close (t1)
        turn = base.extract_text_region_name(frame,*turn_region)
        cap_rate = base.extract_text_region_name(frame, *capture_rate_region)

        if miscritFrame is None:
            miscritFrame = frame

        if 'turn' in turn.lower() or 'your' in turn.lower():
            print('################################################\nDeciding Capture')
            # CAP RATE TAKEN LOGIC
            capRate = None
            try:
                capRate = int(cap_rate)
            except:
                capRate = base.cap_rate_dict.get(cap_rate.lower(),-1)

            # CAPTURE LOGIC
            if capRate >= Settings.AUTO_CAPTURE_THRESHOLDRATE and cap_count < max_capture:
                if cap_count == 0:
                    pass
                    base.click_on(app_window,base.click_coord['capture'])
                    time.sleep(7)

                    cap_count += 1
                else:
                    pass
                    base.click_on(app_window,base.click_coord['capture'])
                    time.sleep(1.5)
                    base.click_on(app_window,base.click_coord['capture2prompt'])
                    time.sleep(7)

                    cap_count += 1
                    platWasted += 5

                screenshot = sct.grab(app_window)
                frame = np.array(screenshot)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                out.write(frame)
                skip = base.extract_text_region_name(frame,*skip_region)
                
            else:
                if cap_count >= max_capture:
                    move = Settings.HEAVY_DAMAGE
                ############ ATTACK #############
                while on_tab > move[0]:
                    base.click_on(app_window,base.click_coord['attackLeftTab'])
                    time.sleep(0.5)
                    on_tab-=1
                while on_tab < move[0]:
                    base.click_on(app_window,base.click_coord['attackRightTab'])
                    time.sleep(0.5)
                    on_tab+=1
                base.click_on(app_window,base.click_coord[f'attack_{move[1]}'])
                time.sleep(6)
                #################################
            print('Ending Turn\n#####################################################')
            ############################################################################
        if 'skip' in skip.lower():
            base.click_on(app_window,base.click_coord["skip"])
            time.sleep(1.5)
            base.click_on(app_window,base.click_coord["close"])
            time.sleep(1.5)

            screenshot = sct.grab(app_window)
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            base.click_on(app_window,base.click_coord["keep"])
            time.sleep(1.5)
            if newMiscrit:
                base.send_discord_webhook(f"<@{USER_ID}>  YOOOO NEW MISCRIT CAUGHT (and added to list ofc) '{miscrit}', Also I ended up wasiting {platWasted} Plat :D",frame=frame[int(frame.shape[0]*0.3):int(frame.shape[0]*0.7), int(frame.shape[1]*0.3):int(frame.shape[1]*0.7)])
                
                commonAreaPokemon.append(miscrit)
                updated_content = str(commonAreaPokemon)
                with open(common_miscrits_file, 'w') as file:
                    file.write(updated_content)
                
                if Settings.AUTO_TRACKING:
                    with open(tracking_miscrits_file, 'r+') as f:
                        my_list = eval(f.read() or "[]")  # Safely handle empty file
                        my_list.append(miscrit)
                        f.seek(0)
                        f.truncate()
                        f.write(str(my_list))

                screenshot = sct.grab(app_window)
                frame = np.array(screenshot)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                Skip = base.extract_text_region_name(frame, *skip_new_miscrit_caught)
                if 'skip' in Skip.lower():
                    base.click_on(app_window,base.click_coord["caughCritSkip"])
                    time.sleep(1)
            else:
                base.send_discord_webhook(f"<@{USER_ID}>  YOOOO I Caught this '{miscrit}', Also I ended up wasiting {platWasted} Plat :D",frame=frame[int(frame.shape[0]*0.3):int(frame.shape[0]*0.7), int(frame.shape[1]*0.3):int(frame.shape[1]*0.7)])
                pass

            base.LOG_STRING += f"PLAT WASTED {platWasted} "
            print("Captured Miscrit")
            break
        elif 'close' in close.lower():
            base.send_discord_webhook(f"<@{USER_ID}> I couldn't capture this guy, he too stupid :P",frame=miscritFrame[miscritRegion[1]:miscritRegion[1] + miscritRegion[3],miscritRegion[0]:miscritRegion[0] + miscritRegion[2]])
            base.click_on(app_window,base.click_coord["close"])
            time.sleep(1.5)
            print("Finished Battle")
            break
        else:
            pass
    
    base.click_on(app_window,base.click_coord['heal'])
    time.sleep(1)
    out.release()