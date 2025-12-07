"""
AI Personality Module for Natural Voice Assistant
Provides friendly responses and conversational capabilities 
"""

import random
from datetime import datetime
import json

class AIPersonality:
    """Lightweight AI personality engine for natural conversation"""
    
    def __init__(self):
        self.user_name = self.load_user_name() or "there"
        self.conversation_history = []
        
    def load_user_name(self):
        try:
            with open("user_settings.json", "r") as f:
                return json.load(f).get("user_name", "there")
        except:
            return "there"
        self.conversation_memory = []
        
    def remember_command(self, command):
        self.conversation_memory.append(command)
        if len(self.conversation_memory) > 5:
            self.conversation_memory.pop(0)
        
    def get_greeting_response(self, greeting_type):
        """Return natural greeting responses"""
        time_hour = datetime.now().hour
        
        if greeting_type == "hello":
            if 5 <= time_hour < 12:
                greetings = [
                    f"Good morning {self.user_name}! How can I help you today?",
                    f"Morning {self.user_name}! What would you like me to do?",
                    f"Hello {self.user_name}! Ready to start the day?"
                ]
            elif 12 <= time_hour < 18:
                greetings = [
                    f"Good afternoon {self.user_name}! How can I assist you?",
                    f"Hello {self.user_name}! What can I do for you?",
                    f"Hey {self.user_name}! How can I help?"
                ]
            else:
                greetings = [
                    f"Good evening {self.user_name}! What can I do for you?",
                    f"Hello {self.user_name}! How can I help?",
                    f"Hey there! What would you like me to do?"
                ]
            return random.choice(greetings), "friendly"
            
        elif greeting_type == "how_are_you":
            responses = [
                "I'm functioning perfectly, thank you for asking! How can I assist you?",
                "I'm doing great! All systems running smoothly. What do you need?",
                "I'm excellent! Ready to help with anything you need.",
                "I'm wonderful, thank you! How can I help you today?"
            ]
            return random.choice(responses), "friendly"
            
        elif greeting_type == "my_name":
            responses = [
                "I'm your personal AI assistant, Nova! I'm here to help you control your computer with voice commands.",
                "You can call me Nova! I'm your friendly AI assistant ready to help.",
                "I'm Nova, your voice-controlled personal assistant!"
            ]
            return random.choice(responses), "friendly"
            
        elif greeting_type == "thanks":
            responses = [
                "You're very welcome! Happy to help anytime.",
                "My pleasure! Let me know if you need anything else.",
                "Anytime! I'm always here to assist you.",
                "Glad I could help! What else can I do for you?",
                "You're welcome! Feel free to ask me anything."
            ]
            return random.choice(responses), "friendly"
            
        elif greeting_type == "goodbye":
            responses = [
                "Goodbye! Have a great day!",
                "See you later! Take care!",
                "Bye! Let me know when you need me again.",
                "Farewell! I'll be here whenever you need me."
            ]
            return random.choice(responses), "calm"
            
        elif greeting_type == "help":
            response = ("I can help you with many things! Try saying:\n"
                       "- Open Chrome, Notepad, or any application\n"
                       "- Search for something on Google\n"
                       "- Control volume, take screenshots\n"
                       "- Tell time, date, check weather\n"
                       "- Open files and folders\n"
                       "- Enable virtual mouse with hand gestures\n"
                       "Just speak naturally and I'll understand!")
            return response, "friendly"
            
        elif greeting_type == "creator":
            responses = [
                "I was created to be your helpful AI assistant! Designed to make your computer interaction easier.",
                "I'm your personal AI assistant, built to help you control your system with voice commands!",
                "I was designed to be a friendly voice assistant that makes using your computer more natural!"
            ]
            return random.choice(responses), "friendly"
            
        elif greeting_type == "joke":
            jokes = [
                "Why don't programmers like nature? It has too many bugs!",
                "Why do programmers prefer dark mode? Because light attracts bugs!",
                "How many programmers does it take to change a light bulb? None, that's a hardware problem!",
                "Why did the developer go broke? Because he used up all his cache!",
                "What's a computer's favorite snack? Microchips!"
            ]
            return random.choice(jokes), "excited"
            
        return "Hello! How can I help you?", "friendly"
    
    def get_action_response(self, action_type, action_data="", success=True):
        """Generate contextual responses for different actions"""
        
        if not success:
            error_responses = [
                "Sorry, I couldn't complete that. Could you try again?",
                "Hmm, that didn't work. Let me know if you need help with something else.",
                "I ran into an issue there. Would you like to try a different command?",
                "Oops, something went wrong. I'm here if you want to try again.",
                "I couldn't do that right now. Is there something else I can help with?"
            ]
            return random.choice(error_responses), "calm"
        
        responses_map = {
            "application": {
                "texts": [
                    f"Opening {action_data} for you now.",
                    f"Sure thing! Launching {action_data}.",
                    f"Got it! Starting {action_data}.",
                    f"Right away! Opening {action_data}.",
                    f"There you go! {action_data} is starting."
                ],
                "emotion": "friendly"
            },
            "application_close": {
                "texts": [
                    f"Closing {action_data} now.",
                    f"Sure, shutting down {action_data}.",
                    f"Done! {action_data} is closed."
                ],
                "emotion": "friendly"
            },
            "web": {
                "texts": [
                    "Opening that in your browser.",
                    "Sure! Taking you there now.",
                    "Right away! Loading that for you.",
                    "Got it! Searching that up.",
                    "On it! Opening your browser."
                ],
                "emotion": "friendly"
            },
            "volume_up": {
                "texts": [
                    "Volume increased!",
                    "Turning it up!",
                    "There you go, louder now!",
                    "Volume up!"
                ],
                "emotion": "neutral"
            },
            "volume_down": {
                "texts": [
                    "Volume decreased!",
                    "Quieter now!",
                    "Turning it down!",
                    "Volume down!"
                ],
                "emotion": "neutral"
            },
            "mute": {
                "texts": [
                    "Muted!",
                    "All quiet now!",
                    "Sound is off!"
                ],
                "emotion": "neutral"
            },
            "screenshot": {
                "texts": [
                    "Screenshot captured!",
                    "Got it! Screenshot taken.",
                    "Done! Screen captured."
                ],
                "emotion": "friendly"
            },
            "lock": {
                "texts": [
                    "Locking your computer now. Stay secure!",
                    "Locking the screen for you.",
                    "Computer locked! See you soon."
                ],
                "emotion": "serious"
            },
            "shutdown": {
                "texts": [
                    "Shutting down your computer. Goodbye!",
                    "Powering off now. Take care!",
                    "Shutting down the system."
                ],
                "emotion": "serious"
            },
            "restart": {
                "texts": [
                    "Restarting your computer now.",
                    "System will restart shortly.",
                    "Rebooting the system."
                ],
                "emotion": "serious"
            },
            "sleep": {
                "texts": [
                    "Putting the computer to sleep. See you later!",
                    "Going to sleep mode now.",
                    "System hibernating."
                ],
                "emotion": "calm"
            },
            "time": {
                "texts": [
                    f"It's currently {action_data}.",
                    f"The time is {action_data}.",
                    f"Right now, it's {action_data}."
                ],
                "emotion": "friendly"
            },
            "date": {
                "texts": [
                    f"Today is {action_data}.",
                    f"It's {action_data}.",
                    f"The date is {action_data}."
                ],
                "emotion": "friendly"
            },
            "file_created": {
                "texts": [
                    "Done! File created successfully.",
                    "All set! Your file is ready.",
                    "Created! Check your desktop.",
                    "File created! Anything else?"
                ],
                "emotion": "friendly"
            },
            "folder_created": {
                "texts": [
                    "Done! Folder created successfully.",
                    "All set! Your folder is ready.",
                    "Folder created on your desktop!",
                    "Created! You'll find it on your desktop."
                ],
                "emotion": "friendly"
            },
            "folder_opened": {
                "texts": [
                    "Opening that folder for you.",
                    "There you go! Folder opened.",
                    "Got it! Opening now."
                ],
                "emotion": "friendly"
            },
            "gesture_enabled": {
                "texts": [
                    "Virtual mouse is now enabled! Use hand gestures to control your cursor.",
                    "Hand gesture control activated! Show five fingers to toggle.",
                    "Gesture mode enabled! You're ready to go.",
                    "Virtual mouse is on! Use your hands to control the cursor."
                ],
                "emotion": "excited"
            },
            "gesture_disabled": {
                "texts": [
                    "Virtual mouse disabled.",
                    "Hand gesture control is now off.",
                    "Gesture mode deactivated."
                ],
                "emotion": "neutral"
            },
            "internet_connected": {
                "texts": [
                    "Your internet connection is active and working!",
                    "You're connected to the internet!",
                    "Internet connection is good!"
                ],
                "emotion": "friendly"
            },
            "internet_disconnected": {
                "texts": [
                    "It seems you're not connected to the internet.",
                    "No internet connection detected.",
                    "You appear to be offline."
                ],
                "emotion": "calm"
            },
            "media_play": {
                "texts": [
                    "Playing your media!",
                    "Starting playback!",
                    "Music is playing!"
                ],
                "emotion": "friendly"
            },
            "media_pause": {
                "texts": [
                    "Paused!",
                    "Media paused!",
                    "Playback paused!"
                ],
                "emotion": "neutral"
            },
            "media_next": {
                "texts": [
                    "Next track!",
                    "Skipping to next song!",
                    "Next!"
                ],
                "emotion": "neutral"
            },
            "media_previous": {
                "texts": [
                    "Previous track!",
                    "Going back!",
                    "Previous!"
                ],
                "emotion": "neutral"
            },
            "minimize_window": {
                "texts": [
                    "Window minimized!",
                    "Minimizing the window!",
                    "There you go, minimized!"
                ],
                "emotion": "neutral"
            },
            "maximize_window": {
                "texts": [
                    "Window maximized!",
                    "Making it full screen!",
                    "Maximizing now!"
                ],
                "emotion": "neutral"
            },
            "close_window": {
                "texts": [
                    "Window closed!",
                    "Closing it now!",
                    "Done, window is closed!"
                ],
                "emotion": "neutral"
            },
            "switch_tab": {
                "texts": [
                    "Switching tabs!",
                    "Next tab!",
                    "Changing tabs now!"
                ],
                "emotion": "neutral"
            },
            "new_tab": {
                "texts": [
                    "New tab opened!",
                    "Fresh tab ready!",
                    "Opening a new tab!"
                ],
                "emotion": "neutral"
            },
            "close_tab": {
                "texts": [
                    "Tab closed!",
                    "Closing that tab!",
                    "Done, tab is closed!"
                ],
                "emotion": "neutral"
            },
            "scroll": {
                "texts": [
                    "Scrolling!",
                    "There you go!",
                    "Scrolling the page!"
                ],
                "emotion": "neutral"
            },
            "brightness_up": {
                "texts": [
                    "Brightness increased!",
                    "Making it brighter!",
                    "Turning up the brightness!"
                ],
                "emotion": "neutral"
            },
            "brightness_down": {
                "texts": [
                    "Brightness decreased!",
                    "Dimming the screen!",
                    "Lowering brightness!"
                ],
                "emotion": "neutral"
            },
            "next_window": {
                "texts": [
                    "Switching windows!",
                    "Next window!",
                    "Changing to next window!"
                ],
                "emotion": "neutral"
            },
            "previous_window": {
                "texts": [
                    "Going back!",
                    "Previous window!",
                    "Switching to previous window!"
                ],
                "emotion": "neutral"
            },
            "switch_to_window": {
                "texts": [
                    "Switching windows!",
                    "Opening that for you!",
                    "Bringing that to front!"
                ],
                "emotion": "neutral"
            },
            "typing": {
                "texts": [
                    "Typing that for you!",
                    "There you go!",
                    "Done typing!"
                ],
                "emotion": "neutral"
            },
            "selection": {
                "texts": [
                    "Selected!",
                    "Text selected!",
                    "Done!"
                ],
                "emotion": "neutral"
            },
            "arrow_right": {
                "texts": [
                    "Moving right!",
                    "Going to the next option!",
                    "Next!"
                ],
                "emotion": "neutral"
            },
            "arrow_left": {
                "texts": [
                    "Moving left!",
                    "Going back!",
                    "Previous!"
                ],
                "emotion": "neutral"
            },
            "arrow_up": {
                "texts": [
                    "Moving up!",
                    "Going up!"
                ],
                "emotion": "neutral"
            },
            "arrow_down": {
                "texts": [
                    "Moving down!",
                    "Going down!"
                ],
                "emotion": "neutral"
            },
            "navigation": {
                "texts": [
                    "Navigating!",
                    "Moving as requested!"
                ],
                "emotion": "neutral"
            }
        }
        
        if action_type in responses_map:
            response_data = responses_map[action_type]
            return random.choice(response_data["texts"]), response_data["emotion"]
        
        # Default friendly response
        defaults = [
            "Done! Anything else I can help with?",
            "All set! Let me know if you need anything else.",
            "Completed! What would you like to do next?",
            "Got it done! How else can I assist you?",
            "Task completed! I'm here if you need more help."
        ]
        return random.choice(defaults), "friendly"
    
    def get_unknown_command_response(self):
        """Response when command is not understood"""
        responses = [
            "I didn't quite catch that. Could you repeat it?",
            "Sorry, I didn't understand. Can you try saying it differently?",
            "I'm not sure what you mean. Could you rephrase that?",
            "Hmm, I didn't get that. Try saying it another way?",
            "I'm still learning! Could you say that again more clearly?"
        ]
        return random.choice(responses), "calm"
    
    def get_wake_word_response(self):
        """Response when wake word is detected"""
        responses = [
            "Yes? I'm listening!",
            "I'm here! What do you need?",
            "How can I help you?",
            "Yes? What can I do for you?",
            "I'm listening! Go ahead.",
            "At your service! What do you need?"
        ]
        return random.choice(responses), "excited"
