import pyautogui
import re

import ocr_common

# --- Configuration ---------------------------------------------------------

# Certre of minimap
MINIMAP_ORIGIN = (1837, 107)
SCALE = 2
WAYPOINT_TIMEOUT_SECONDS = 15
WAYPOINT_TOLERANCE = 2
# Loaded once at startup -- see capture_templates.py to build/update this.
try:
    _templates = ocr_common.load_templates()
except FileNotFoundError:
    exit(
        "No character templates found. Run capture_templates.py first to "
        "build the template library, then run this script again."
    )

# --- Zone definitions --------------------------------------------------

geRange = [(3141, 3513), (3186, 3469)]
edgevillerange = [(3072, 3515), (3110, 3466)]
rimmingtonMine = [(2980, 3244), (2989, 3234)]

GeToRimmington = [
    [3163, 3477], [3163, 3466], [3161, 3455], [3151, 3445], [3140, 3441],
    [3130, 3435], [3121, 3424], [3111, 3420], [3100, 3420], [3091, 3410],
    [3088, 3399], [3079, 3389], [3074, 3378], [3071, 3367], [3071, 3356],
    [3069, 3345], [3064, 3334], [3064, 3323], [3058, 3313], [3054, 3304],
    [3053, 3293], [3051, 3282], [3045, 3272], [3035, 3264], [3026, 3257],
    [3016, 3251], [3005, 3245], [2994, 3238], [2988, 3235], [2987, 3239]
]

GeToEdgeville = [
    [3162, 3488], [3163, 3477], [3163, 3466], [3152, 3463], [3142, 3465],
    [3136, 3471], [3137, 3482], [3137, 3493], [3135, 3504], [3135, 3515],
    [3124, 3514], [3113, 3507], [3102, 3500], [3094, 3493]
]

RimmingtinToGe = [
    [2987, 3239], [2990, 3234], [3001, 3244], [3007, 3254],
    [3013, 3265], [3021, 3275], [3032, 3280], [3034, 3291], [3039, 3300],
    [3047, 3305], [3056, 3311], [3063, 3319], [3071, 3330], [3071, 3341],
    [3071, 3352], [3076, 3363], [3079, 3374], [3084, 3384], [3087, 3395],
    [3093, 3406], [3096, 3417], [3107, 3420], [3117, 3425], [3121, 3436],
    [3131, 3445], [3139, 3455], [3150, 3456], [3160, 3464], [3163, 3473],
    [3163, 3484], [3162, 3488]
]

edgevilleToGe = [
    [3094, 3493], [3104, 3502], [3115, 3512], [3126, 3515],
    [3134, 3513], [3134, 3502], [3137, 3491], [3136, 3480], [3136, 3469],
    [3144, 3465], [3154, 3463], [3163, 3468], [3163, 3479], [3162, 3488]
]


# --- Core functions ----------------------------------------------------

def coords():
    #Reads the player's current in-game coordinates via template matching.
    text = ocr_common.read_text(_templates)
    if text is None:
        print("cant find coords (a character didn't match any template "
              "confidently -- check debug_ocr_last.png, and consider "
              "running capture_templates.py again)")
        return None

    numbers = re.findall(r'-?\d+', text)
    if len(numbers) < 2:
        print(f"cant find coords (parsed text: '{text}')")
        return None

    return int(numbers[0]), int(numbers[1])


def walker(target):
    #Clicks the minimap position corresponding to the given target game-coordinate, based on the player's current OCR'd position.
    current = coords()
    if current is None:
        return

    x_value, y_value = current
    clickpos = (target[0] - x_value, target[1] - y_value)
    print(f"Click Position: {clickpos}")

    target_x = MINIMAP_ORIGIN[0] + SCALE * clickpos[0]
    target_y = MINIMAP_ORIGIN[1] - SCALE * clickpos[1]

    print(f"Target Position: {target_x}, {target_y}")

    pyautogui.moveTo(target_x, target_y)
    pyautogui.sleep(0.1)
    pyautogui.click()
    pyautogui.sleep(1)


def in_range(pos, zone):
    """Checks whether pos=(x, y) falls within a zone's bounding box."""
    (x1, y1), (x2, y2) = zone
    min_x, max_x = min(x1, x2), max(x1, x2)
    min_y, max_y = min(y1, y2), max(y1, y2)
    return min_x <= pos[0] <= max_x and min_y <= pos[1] <= max_y


def walk_path(path):
    """Walks a sequence of waypoints by repeatedly checking position and
    clicking toward the next waypoint once the current one is reached exactly.
    If a waypoint isn't matched within WAYPOINT_TIMEOUT_SECONDS, advances
    anyway rather than hanging forever on a possible OCR misread."""

    # Kick off movement toward the first waypoint immediately — otherwise
    # the loop below waits for an exact match to a position we're not
    # already standing on, and nothing ever moves.
    walker(path[0])

    for index in range(len(path) - 1):
        current_waypoint = path[index]
        next_waypoint = path[index + 1]

        elapsed = 0
        while True:
            pos = coords()
            if pos is None:
                pyautogui.sleep(1)
                elapsed += 1
                continue

            print(f"loop - current pos: {pos}")


            x_diff = abs(pos[0] - current_waypoint[0])
            y_diff = abs(pos[1] - current_waypoint[1])
            if x_diff <= WAYPOINT_TOLERANCE and y_diff <= WAYPOINT_TOLERANCE:
                walker(next_waypoint)
                print("walker")
                break


            if elapsed >= WAYPOINT_TIMEOUT_SECONDS:
                print(f"WARNING: waypoint {current_waypoint} not confirmed "
                      f"after {WAYPOINT_TIMEOUT_SECONDS}s (last read: {pos}). "
                      f"Advancing anyway — check {ocr_common.DEBUG_IMAGE_PATH} "
                      f"if this keeps happening.")
                walker(next_waypoint)
                break

            pyautogui.sleep(1)
            elapsed += 1


# --- Main ----------------------------------------------------------------

def main():
    pos = coords()
    if pos is None:
        exit("Could not read starting coordinates, aborting.")

    print(f"Starting position (OCR): {pos}")

    if in_range(pos, geRange):
        print("The coordinates are within the Grand Exchange range.")
        selection = input("where would you like to go?\n1: edgeville\n2: rimmingtonMine\n")

        if selection == "1":
            path = GeToEdgeville
        elif selection == "2":
            path = GeToRimmington
        else:
            exit("error: invalid selection")

    elif in_range(pos, edgevillerange):
        print("The coordinates are within the Edgeville range.")
        selection = input("where would you like to go?\n1: Ge\n")

        if selection == "1":
            path = edgevilleToGe
        else:
            exit("error: invalid selection")

    elif in_range(pos, rimmingtonMine):
        print("The coordinates are within the Rimmington Mine range.")
        selection = input("where would you like to go?\n1: Ge\n")

        if selection == "1":
            path = RimmingtinToGe
        else:
            exit("error: invalid selection")

    else:
        exit("The coordinates are not in any specified range.")

    walk_path(path)


if __name__ == "__main__":
    main()