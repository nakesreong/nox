from app.actions.light_actions import turn_on, set_color_temperature, turn_off, HA_URL, HA_TOKEN, DEFAULT_LIGHT_ENTITY_IDS

if not (HA_URL and HA_TOKEN and DEFAULT_LIGHT_ENTITY_IDS):
    print("Home Assistant configuration not loaded. Example calls will be skipped.")
else:
    print(turn_on(brightness_percent=100))
    print(set_color_temperature("warm"))
    print(turn_off())
