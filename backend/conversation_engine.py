import re
import json
from typing import Tuple, Dict, Any, Optional
from datetime import datetime

from schemas import ConversationState
import models  # <- replace “from models import …” to avoid circular import


class ConversationEngine:
    def __init__(self):
        self.state_prompts = {
            ConversationState.start: "Hello! I'll help you with your insurance onboarding. Let's start by getting your zip code.",
            ConversationState.collecting_zip: "What's your 5-digit zip code?",
            ConversationState.collecting_name: "Great! What's your full name?",
            ConversationState.collecting_email: "Thanks! What's your email address?",
            ConversationState.vehicle_intro: "Perfect! Now let's add your vehicle. I'll need either your VIN or your vehicle's year, make, and body type.",
            ConversationState.collecting_vehicle_info: "Please provide either your VIN or Year Make Body‑Type (like '2022 Honda Civic').",
            ConversationState.collecting_vehicle_use: "How do you primarily use this vehicle? (commuting, commercial, farming, or business)",
            ConversationState.collecting_blind_spot: "Does this vehicle have blind spot warning? (Yes or No)",
            ConversationState.collecting_commute_days: "How many days per week do you commute with this vehicle?",
            ConversationState.collecting_commute_miles: "What's your one‑way distance to work/school in miles?",
            ConversationState.collecting_annual_mileage: "What's the estimated annual mileage for this vehicle?",
            ConversationState.ask_more_vehicles: "Would you like to add another vehicle? (Yes or No)",
            ConversationState.collecting_license_type: "What type of license do you have? (Foreign, Personal, or Commercial)",
            ConversationState.collecting_license_status: "What's your license status? (Valid or Suspended)",
            ConversationState.completed: "Thank you! Your onboarding is complete."
        }

        self.validators = {
            ConversationState.collecting_zip: self._validate_zip,
            ConversationState.collecting_name: self._validate_name,
            ConversationState.collecting_email: self._validate_email,
            ConversationState.collecting_vehicle_info: self._validate_vehicle_info,
            ConversationState.collecting_vehicle_use: self._validate_vehicle_use,
            ConversationState.collecting_blind_spot: self._validate_yes_no,
            ConversationState.collecting_commute_days: self._validate_days,
            ConversationState.collecting_commute_miles: self._validate_miles,
            ConversationState.collecting_annual_mileage: self._validate_mileage,
            ConversationState.ask_more_vehicles: self._validate_yes_no,
            ConversationState.collecting_license_type: self._validate_license_type,
            ConversationState.collecting_license_status: self._validate_license_status,
        }

    # --------------------------------------------------------------------- #
    #  Public helpers
    # --------------------------------------------------------------------- #
    def get_prompt(self, state: ConversationState) -> str:
        return self.state_prompts.get(state, "")

    def validate_input(self, state: ConversationState, user_input: str) -> Tuple[bool, Any, Optional[str]]:
        validator = self.validators.get(state)
        if validator:
            return validator(user_input)
        return True, user_input, None

    def get_next_state(self, current_state: ConversationState, validated_data: Any, state_data: Dict) -> ConversationState:
        transitions = {
            ConversationState.start: ConversationState.collecting_zip,
            ConversationState.collecting_zip: ConversationState.collecting_name,
            ConversationState.collecting_name: ConversationState.collecting_email,
            ConversationState.collecting_email: ConversationState.vehicle_intro,
            ConversationState.vehicle_intro: ConversationState.collecting_vehicle_info,
            ConversationState.collecting_vehicle_info: ConversationState.collecting_vehicle_use,
            ConversationState.collecting_vehicle_use: ConversationState.collecting_blind_spot,
            ConversationState.collecting_blind_spot: self._next_after_blind_spot,
            ConversationState.collecting_commute_days: ConversationState.collecting_commute_miles,
            ConversationState.collecting_commute_miles: ConversationState.ask_more_vehicles,
            ConversationState.collecting_annual_mileage: ConversationState.ask_more_vehicles,
            ConversationState.ask_more_vehicles: self._next_after_more_vehicles,
            ConversationState.collecting_license_type: self._next_after_license_type,
            ConversationState.collecting_license_status: ConversationState.completed,
            ConversationState.completed: ConversationState.completed,
        }

        next_state = transitions.get(current_state)
        if callable(next_state):
            return next_state(validated_data, state_data)
        return next_state or current_state

    def calculate_progress(self, state: ConversationState) -> float:
        progress_map = {
            ConversationState.start: 0,
            ConversationState.collecting_zip: 10,
            ConversationState.collecting_name: 20,
            ConversationState.collecting_email: 30,
            ConversationState.vehicle_intro: 35,
            ConversationState.collecting_vehicle_info: 40,
            ConversationState.collecting_vehicle_use: 50,
            ConversationState.collecting_blind_spot: 60,
            ConversationState.collecting_commute_days: 65,
            ConversationState.collecting_commute_miles: 70,
            ConversationState.collecting_annual_mileage: 70,
            ConversationState.ask_more_vehicles: 75,
            ConversationState.collecting_license_type: 85,
            ConversationState.collecting_license_status: 95,
            ConversationState.completed: 100,
        }
        return progress_map.get(state, 0)

    # --------------------------------------------------------------------- #
    #  Transition helpers
    # --------------------------------------------------------------------- #
    def _next_after_blind_spot(self, validated_data: Any, state_data: Dict) -> ConversationState:
        vehicle_use = state_data.get("current_vehicle", {}).get("vehicle_use")
        if vehicle_use == "commuting":
            return ConversationState.collecting_commute_days
        return ConversationState.collecting_annual_mileage

    def _next_after_more_vehicles(self, validated_data: bool, state_data: Dict) -> ConversationState:
        return ConversationState.vehicle_intro if validated_data else ConversationState.collecting_license_type

    def _next_after_license_type(self, validated_data: str, state_data: Dict) -> ConversationState:
        return ConversationState.completed if validated_data == "foreign" else ConversationState.collecting_license_status

    # --------------------------------------------------------------------- #
    #  Validators
    # --------------------------------------------------------------------- #
    def _validate_zip(self, user_input: str) -> Tuple[bool, Optional[str], Optional[str]]:
        cleaned = user_input.strip()
        if re.match(r'^\d{5}$', cleaned):
            return True, cleaned, None
        return False, None, "Please provide a valid 5‑digit zip code."

    def _validate_name(self, user_input: str) -> Tuple[bool, Optional[str], Optional[str]]:
        cleaned = user_input.strip()
        if len(cleaned) >= 2 and " " in cleaned:
            return True, cleaned, None
        return False, None, "Please provide your full name (first and last)."

    def _validate_email(self, user_input: str) -> Tuple[bool, Optional[str], Optional[str]]:
        cleaned = user_input.strip().lower()
        if re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", cleaned):
            return True, cleaned, None
        return False, None, "Please provide a valid email address."

    def _validate_vehicle_info(self, user_input: str) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        cleaned = user_input.strip().upper()

        # VIN?
        if re.match(r"^[A-HJ-NPR-Z0-9]{17}$", cleaned):
            return True, {"vin": cleaned}, None

        # “Year Make Body‑Type”
        parts = user_input.strip().split(maxsplit=2)
        if len(parts) >= 3:
            try:
                year = int(parts[0])
                if 1900 <= year <= 2030:
                    return True, {
                        "year": year,
                        "make": parts[1].title(),
                        "body_type": parts[2].title(),
                    }, None
            except ValueError:
                pass

        return False, None, "Please provide either a 17‑character VIN or 'Year Make Body‑Type'."

    def _validate_vehicle_use(self, user_input: str) -> Tuple[bool, Optional[str], Optional[str]]:
        cleaned = user_input.strip().lower()
        if cleaned in (v.value for v in models.VehicleUse):
            return True, cleaned, None
        return False, None, "Please choose: commuting, commercial, farming, or business."

    def _validate_yes_no(self, user_input: str) -> Tuple[bool, bool, Optional[str]]:
        cleaned = user_input.strip().lower()
        yes_values = {"yes", "y", "yeah", "yep", "sure", "ok", "okay"}
        no_values = {"no", "n", "nope", "nah"}
        if cleaned in yes_values:
            return True, True, None
        if cleaned in no_values:
            return True, False, None
        return False, None, "Please answer Yes or No."

    def _validate_days(self, user_input: str) -> Tuple[bool, Optional[int], Optional[str]]:
        try:
            days = int(user_input.strip())
            if 1 <= days <= 7:
                return True, days, None
        except ValueError:
            pass
        return False, None, "Please enter a number between 1 and 7."

    def _validate_miles(self, user_input: str) -> Tuple[bool, Optional[int], Optional[str]]:
        try:
            miles = int(user_input.strip())
            if 0 < miles < 1000:
                return True, miles, None
        except ValueError:
            pass
        return False, None, "Please enter the number of miles (1‑999)."

    def _validate_mileage(self, user_input: str) -> Tuple[bool, Optional[int], Optional[str]]:
        try:
            mileage = int(user_input.strip().replace(",", ""))
            if 0 < mileage < 500_000:
                return True, mileage, None
        except ValueError:
            pass
        return False, None, "Please enter annual mileage (e.g., 12000)."

    def _validate_license_type(self, user_input: str) -> Tuple[bool, Optional[str], Optional[str]]:
        cleaned = user_input.strip().lower()
        
        if cleaned in (t.value for t in models.LicenseType):
            return True, cleaned, None
        return False, None, "Please choose: Foreign, Personal, or Commercial."

    def _validate_license_status(self, user_input: str) -> Tuple[bool, Optional[str], Optional[str]]:
        cleaned = user_input.strip().lower()
        
        if cleaned in (s.value for s in models.LicenseStatus):
            return True, cleaned, None
        return False, None, "Please choose: Valid or Suspended."
