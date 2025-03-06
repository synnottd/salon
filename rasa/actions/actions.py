from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

class ActionDefaultFallback(Action):
    def name(self) -> Text:
        return "action_default_fallback"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(text="I'm sorry, I didn't quite understand that. Could you rephrase?")
        return []

class ActionHandleInform(Action):
    def name(self) -> Text:
        return "action_handle_inform"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Get current slot values
        service = tracker.get_slot('service')
        date = tracker.get_slot('date')
        time = tracker.get_slot('time')
        stylist = tracker.get_slot('stylist')

        # Check what information we have and what's missing
        missing_info = []
        if not service:
            missing_info.append("service")
        if not date:
            missing_info.append("date")
        if not time:
            missing_info.append("time")
        if not stylist:
            missing_info.append("stylist")

        # If we have all information, confirm the booking
        if not missing_info:
            response = f"Great! I'll book your {service} appointment with {stylist} for {date} at {time}. Would you like me to confirm this booking?"
            dispatcher.utter_message(text=response)
            return []

        # If we're missing information, ask for the first missing item
        if len(missing_info) == 1:
            if missing_info[0] == "service":
                dispatcher.utter_message(text="What service would you like to book?")
            elif missing_info[0] == "date":
                dispatcher.utter_message(text="What date would you like to book for?")
            elif missing_info[0] == "time":
                dispatcher.utter_message(text="What time would you prefer?")
            elif missing_info[0] == "stylist":
                dispatcher.utter_message(text="Which stylist would you like to book with?")
        else:
            # If multiple pieces of information are missing, summarize what we have and what we need
            have_info = []
            if service:
                have_info.append(f"a {service}")
            if date:
                have_info.append(f"on {date}")
            if time:
                have_info.append(f"at {time}")
            if stylist:
                have_info.append(f"with {stylist}")

            if have_info:
                response = f"I see you want to book {', '.join(have_info)}. "
            else:
                response = "I'd be happy to help you book an appointment. "

            response += f"I just need to know your preferred {' and '.join(missing_info)}. "
            response += "Which would you like to specify first?"
            
            dispatcher.utter_message(text=response)

        return [] 