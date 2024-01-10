# https://apps.timwhitlock.info/emoji/tables/unicode#block-2-dingbats

from testipy.configs import enums_data

try:
    from termcolor import colored
    __CANNOT_USE = False
except:
    __CANNOT_USE = True


EXCQM = "\U00002049"  # exclamation question mark
P_100 = "\U0001F60D"  # smiling face with heart-shaped eyes
P_095 = "\U0001F604"  # smiling face with open mouth and smiling eyes
P_050 = "\U0001F605"  # smiling face with open mouth and cold sweat
P_010 = "\U0001F631"  # face screaming in fear
P_000 = "\U0001F621"  # pouting face

EMOJI_METER = [(100, P_100), (95, P_095), (50, P_050), (10, P_010), (0, P_000)]


def show_emoji_meter():
    for x, emj in EMOJI_METER:
        print(f">= {x:3} - {emj}")


def get_emoji(float_val):
    for val, emoji in EMOJI_METER:
        if float_val >= val:
            return emoji
    return EXCQM


# Colors --------------------------------------------------------------

def color_state(state: str) -> str:
    if __CANNOT_USE:
        return state

    if state == enums_data.STATE_PASSED:
        return colored(state, "white", "on_green", ["bold"])
    if state == enums_data.STATE_SKIPPED:
        return colored(state, "white", "on_yellow", ["bold"])
    if state == enums_data.STATE_FAILED:
        return colored(state, "white", "on_red", ["bold"])
    if state == enums_data.STATE_FAILED_KNOWN_BUG:
        return colored(state, "white", "on_dark_grey", ["bold"])
    return state


def color_line(text: str) -> str:
    if __CANNOT_USE:
        return text

    result = ""
    for line in text.split("\n"):
        if f"{enums_data.STATE_PASSED}  " in line:
            result += colored(line, "white", "on_green", ["bold"]) + "\n"
        elif f"{enums_data.STATE_SKIPPED}  " in line:
            result += colored(line, "white", "on_yellow", ["bold"]) + "\n"
        elif f"{enums_data.STATE_FAILED}  " in line:
            result += colored(line, "white", "on_red", ["bold"]) + "\n"
        elif f"{enums_data.STATE_FAILED_KNOWN_BUG}  " in line:
            result += colored(line, "white", "on_dark_grey", ["bold"]) + "\n"
        else:
            result += line + "\n"
    return result[:-1]


if __name__ == "__main__":
    show_emoji_meter()
