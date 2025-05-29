# app/intent_handlers/device_control_handler.py

from app.actions import light_actions
# Import other action modules as they are created
# from app.actions import pc_actions
# from app.actions import air_purifier_actions

def handle_device_control(entities: dict) -> dict:
    """
    Handles the 'control_device' intent.
    Determines the target_device and action, then calls the appropriate action module.
    Returns a dictionary with the "technical" result for response generation.
    """
    print(f"DeviceControlHandler: Received entities: {entities}")
    
    target_device = entities.get("target_device")
    action = entities.get("action")
    
    # --- Light Control ---
    if target_device == "light":
        result = None
        # These will be populated by light_actions for a more detailed response generation
        brightness_set = None
        temp_qualitative_set = None
        temp_kelvin_set = None
        
        if action == "turn_on":
            result = light_actions.turn_on()
        elif action == "turn_off":
            result = light_actions.turn_off()
        elif action == "toggle":
            result = light_actions.toggle()
        elif action == "setting": # Unified action for all light settings
            brightness_pct = entities.get("brightness_pct")
            color_temp_qualitative = entities.get("color_temp_qualitative")
            color_temp_kelvin = entities.get("color_temp_kelvin")
            
            # We need to call light_actions in a way that it can handle these parameters.
            # Our light_actions.turn_on() was designed to accept brightness and kelvin.
            # Let's adapt to call it correctly.
            
            final_kelvin_to_set = None
            if color_temp_kelvin is not None:
                final_kelvin_to_set = color_temp_kelvin
                temp_kelvin_set = final_kelvin_to_set
            elif color_temp_qualitative is not None:
                # Convert qualitative to Kelvin using the preset in light_actions
                # This logic might be better inside light_actions.set_color_temperature
                # or a new light_actions.apply_settings function.
                # For now, let's assume light_actions.set_color_temperature handles this.
                # We'll call set_color_temperature first, then set_brightness if needed,
                # or ideally, a single function that takes all params.
                
                # Let's use the existing light_actions.set_color_temperature
                # which internally calls turn_on with kelvin.
                # And light_actions.set_brightness which calls turn_on with brightness_pct.
                # This means two separate calls if both are present, which is not ideal for HA.
                # The best is to pass all to light_actions.turn_on()
                
                temp_to_use_for_turn_on = None
                if color_temp_qualitative in light_actions.COLOR_TEMPERATURE_PRESETS_KELVIN:
                    final_kelvin_to_set = light_actions.COLOR_TEMPERATURE_PRESETS_KELVIN[color_temp_qualitative.lower()]
                    temp_qualitative_set = color_temp_qualitative # For response
                    temp_kelvin_set = final_kelvin_to_set # For response
                else: # Invalid qualitative temp
                    return {"success": False, 
                            "details_or_error": f"Unknown qualitative temperature: '{color_temp_qualitative}'. Use 'warm', 'cool', or 'natural'.",
                            "action_performed": "setting_error"}

            # Now call light_actions.turn_on with all available parameters
            # It will only include brightness_pct and final_kelvin_to_set in service_data if they are not None.
            result = light_actions.turn_on(
                brightness_percent=brightness_pct, 
                kelvin=final_kelvin_to_set
            )
            if brightness_pct is not None:
                brightness_set = brightness_pct


        else:
            return {"success": False, "details_or_error": f"Unknown action '{action}' for light.", "action_performed": "unknown_light_action"}

        # Prepare response based on the result from light_actions
        if result and result.get("success"):
            return {
                "success": True,
                "action_performed": action, # Or a more specific description
                "target_device": target_device,
                "location": entities.get("location", "room"), # Keep location if NLU provided it
                "brightness_pct_set": brightness_set,
                "color_temp_qualitative_set": temp_qualitative_set,
                "color_temp_kelvin_set": temp_kelvin_set,
                "details_or_error": result.get("message", "Light command executed successfully.")
            }
        else:
            return {
                "success": False,
                "action_performed": action,
                "target_device": target_device,
                "location": entities.get("location"),
                "details_or_error": result.get("error", "Failed to execute light command.") if result else "Unknown error with light action."
            }

    # --- Placeholder for other target_devices ---
    # elif target_device == "pc":
    #     # ... pc_actions ...
    #     pass
        
    else:
        return {
            "success": False,
            "action_performed": "unknown_target_device",
            "target_device": target_device,
            "details_or_error": f"I don't know how to control the device '{target_device}' yet."
        }