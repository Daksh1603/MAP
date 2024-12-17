HEAVY_DAMAGE = (1,1) # TAB 1 2 3 (In Order)
MEDIUM_DAMAGE = (2,2)
LIGHT_DAMAGE = (3,2)
NON_DAMAGE = (1,2)


REGIME_FILE = 'DarkCroaky.txt'
TRAIN_TIME_DELAY = 1.5

APPLICATION_NAME = 'Miscrits (DEBUG)'

DISCORD_USER_ID = 236268536950030337

RAISE_DISCORD_ALERT = 1




############ WILD HUNT #############

WILD_HUNT_SEARCH_COUNT = 500
AUTO_TRACKING = 1

############# AUTO CAPTURE #########
AUTO_CAPTURE_MODE = 1
AUTO_CAPTURE_MOVE = (2,2)
AUTO_CAPTURE_MAX = 2
AUTO_CAPTURE_THRESHOLDRATE = 75
# AUTO_CAPTURE_PLAT_LIST = ['EPIC_SPLUS']
# AUTO_CAPTURE_TRACKING_LIST = ['Dark Ceemky']

ALL_SEARCH_PLAT = None ###########################



COMMON_APLUS = 0
COMMON_S = 0
COMMON_SPLUS = 0


RARE_APLUS = 1
RARE_S = 0
RARE_SPLUS = 0

EPIC_APLUS = 0
EPIC_S = 1
EPIC_SPLUS = 1



RATING_ALERT_LIST = []

if COMMON_APLUS:
    RATING_ALERT_LIST.append('30')
if COMMON_S:
    RATING_ALERT_LIST.extend(['28','28Â°','28�'])
if COMMON_SPLUS:
    RATING_ALERT_LIST.extend(['27','27Â°','27�'])

if RARE_APLUS:
    RATING_ALERT_LIST.append('20')
if RARE_S:
    RATING_ALERT_LIST.extend(['18','18Â°','18�'])
if RARE_SPLUS:
    RATING_ALERT_LIST.extend(['17','17Â°','17�','{7','{7Â°','{7�'])

if EPIC_APLUS:
    RATING_ALERT_LIST.append('10')
if EPIC_S:
    RATING_ALERT_LIST.extend(['8','ry:','ry'])
if EPIC_SPLUS:
    RATING_ALERT_LIST.extend(['7'])


# def update_rating_alert_list(auto_list):
#     RATING_ALERT_LIST_NOPLAT = []

#     if "COMMON_APLUS" in auto_list:
#         RATING_ALERT_LIST_NOPLAT.append('30')
#     if "COMMON_S" in auto_list:
#         RATING_ALERT_LIST_NOPLAT.extend(['28', '28Â°', '28�'])
#     if "COMMON_SPLUS" in auto_list:
#         RATING_ALERT_LIST_NOPLAT.extend(['27', '27Â°', '27�'])

#     if "RARE_APLUS" in auto_list:
#         RATING_ALERT_LIST_NOPLAT.append('20')
#     if "RARE_S" in auto_list:
#         RATING_ALERT_LIST_NOPLAT.extend(['18', '18Â°', '18�'])
#     if "RARE_SPLUS" in auto_list:
#         RATING_ALERT_LIST_NOPLAT.extend(['17', '17Â°', '17�', '{7', '{7Â°', '{7�'])

#     if "EPIC_APLUS" in auto_list:
#         RATING_ALERT_LIST_NOPLAT.append('10')
#     if "EPIC_S" in auto_list:
#         RATING_ALERT_LIST_NOPLAT.extend(['8', 'ry:', 'ry'])
#     if "EPIC_SPLUS" in auto_list:
#         RATING_ALERT_LIST_NOPLAT.extend(['7', 'ry:'])

#     print('Auto caputring new miscrits and the following cap_rates : ',RATING_ALERT_LIST_NOPLAT)
#     return RATING_ALERT_LIST_NOPLAT
# AUTO_CAPTURE_PLAT_LIST = update_rating_alert_list(AUTO_CAPTURE_PLAT_LIST)