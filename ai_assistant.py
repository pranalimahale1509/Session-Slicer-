"""
AI Assistant Module for SessionSlice
Provides intelligent chatbot capabilities with offline knowledge base and Hugging Face AI integration.
"""

import os
import random
import difflib
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

# Optional Hugging Face integration
try:
    from huggingface_hub import InferenceClient
    _HF_AVAILABLE = True
except Exception:
    _HF_AVAILABLE = False


class AIAssistant:
    """Hugging Face-powered AI assistant for advanced conversational capabilities"""
    
    def __init__(self, api_key=None):
        self.enabled = False
        # Using a reliable, currently available model from Hugging Face
        self.model = os.getenv("HUGGINGFACE_MODEL", "meta-llama/Llama-3.2-3B-Instruct")
        self.system_prompt = (
            "You are SessionSlice's friendly AI assistant. "
            "You can answer ANY question the user asks - from productivity tips to general knowledge, coding help, or casual conversation. "
            "Be warm, concise, and helpful. When discussing productivity, be practical and encouraging. "
            "Use emojis occasionally to keep things friendly. Keep responses under 200 words unless asked for more detail."
        )
        
        # Determine key to use (Env var or passed key)
        env_key = os.getenv("HUGGINGFACE_API_KEY")
        self.api_key = api_key if api_key else env_key
        
        # Debug logging
        print(f"🔍 AIAssistant Init Debug:")
        print(f"  - Passed API key: {'Yes' if api_key else 'No'}")
        print(f"  - Env API key: {'Yes' if env_key else 'No'}")
        print(f"  - Final API key: {'Yes' if self.api_key else 'No'}")
        print(f"  - HF Hub available: {_HF_AVAILABLE}")
        
        if _HF_AVAILABLE and self.api_key:
            try:
                self.client = InferenceClient(token=self.api_key, timeout=30)
                self.enabled = True
                print(f"  - ✅ AI ENABLED with model: {self.model}")
            except Exception as e:
                self.client = None
                self.enabled = False
                print(f"  - ❌ AI INIT FAILED: {e}")
        else:
            self.client = None
            self.enabled = False
            print(f"  - ❌ AI DISABLED (hf_hub={_HF_AVAILABLE}, key={bool(self.api_key)})")

    def set_key(self, api_key):
        """Update the API key at runtime"""
        if not _HF_AVAILABLE:
            return False
        try:
            self.api_key = api_key
            self.client = InferenceClient(token=api_key, timeout=30)
            self.enabled = True
            return True
        except Exception:
            self.client = None
            self.enabled = False
            return False

    def generate(self, history, user_message):
        """Generate AI response using Hugging Face Inference API"""
        print(f"🤖 Generating response for: {user_message}")
        if not self.enabled or not self.client:
            raise RuntimeError("AI assistant not enabled")
        
        # Build conversation history for chat models
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Add recent history (last 10 messages)
        trimmed = history[-10:] if history else []
        for m in trimmed:
            if isinstance(m, dict) and "role" in m and "content" in m:
                messages.append({"role": m["role"], "content": m["content"]})
        
        # Add current message
        messages.append({"role": "user", "content": user_message})
        
        try:
            # Use chat completion for instruction-tuned models
            print(f"  - Sending chat_completion request to {self.model}...")
            response = self.client.chat_completion(
                messages=messages,
                model=self.model,
                max_tokens=300,
                temperature=0.7,
            )
            print("  - Response received!")
            
            # Extract the generated text
            if hasattr(response, 'choices') and len(response.choices) > 0:
                return response.choices[0].message.content.strip()
            else:
                return str(response).strip()
                
        except Exception as e:
            print(f"  - ⚠️ Chat completion failed: {e}")
            # Fallback to text generation if chat completion fails
            try:
                # Build a simple prompt
                prompt = f"{self.system_prompt}\n\nUser: {user_message}\nAssistant:"
                print("  - Attempting fallback text_generation...")
                response = self.client.text_generation(
                    prompt,
                    model=self.model,
                    max_new_tokens=300,
                    temperature=0.7,
                )
                print("  - Fallback successful!")
                return response.strip()
            except Exception as e2:
                print(f"  - ❌ All AI attempts failed: {e2}")
                raise RuntimeError(f"AI request failed: {str(e2)}")


class ProductivityChatbot:
    """Friendly productivity chatbot with offline knowledge base and optional AI integration"""
    
    def __init__(self, app, ai_assistant=None):
        self.app = app
        self.ai = ai_assistant
        self.history = []
        
        self.greetings = [
            "Hey there! Ready to crush some goals today? 💪",
            "What's up! Let's make today productive! 🎯",
            "Hi friend! How can I help you focus today? 😊",
            "Yo! Let's get stuff done together! 🚀"
        ]
        
        self.encouragements = [
            "You're doing amazing! Keep it up! 🌟",
            "Great job! You're on fire today! 🔥",
            "That's the spirit! Let's keep this momentum going! 💪",
            "Awesome work! You're crushing it! 🎉",
            "Nice! You're making real progress! ⭐"
        ]
        
        self.break_reminders = [
            "Hey, time for a quick break! Your brain needs to recharge 🧠☕",
            "You've been working hard! Take 5 and stretch a bit 🙆‍♀️",
            "Break time! Go grab some water and rest your eyes 💧👀",
            "Psst... how about a little break? You've earned it! 😌"
        ]
        
        self.tips = [
            "Pro tip: Try the 25-5 rule - 25 min focus, 5 min break. It works wonders! ⏰",
            "Keep your phone in another room while working. Out of sight, out of mind! 📱",
            "Break big tasks into smaller chunks. Makes them less scary! 📝",
            "Morning sessions hit different! Try tackling hard stuff early 🌅",
            "Hydration = concentration! Keep that water bottle nearby 💧",
            "Quick wins build momentum. Start with something easy! 🎯",
            "Turn off notifications during focus time. Your future self will thank you! 🔕"
        ]

        self.knowledge_base = {
            "pomodoro": "The Pomodoro Technique: Work 25 mins, break 5 mins. After 4 cycles, take a 15-30 min break. 🍅",
            "gtd": "GTD (Getting Things Done): Capture everything into an external system, clarify, organize, and review. Clear your mind! 🧠",
            "eat the frog": "Eat the Frog: Do your hardest task first thing in the morning when your energy is highest. 🐸",
            "time blocking": "Time Blocking: Schedule specific chunks of time for deep work. Don't just list tasks, schedule them! 🗓️",
            "two minute rule": "2-Minute Rule: If it takes < 2 mins, do it NOW. ⚡",
            "pareto": "Pareto Principle (80/20): 80% of results come from 20% of your efforts. Focus on the vital few tasks. 📊",
            "flow": "Flow: The zone where you are fully immersed. Balance challenge with skill and remove distractions. 🌊",
            "kanban": "Kanban: Visualize work with columns (To Do -> Doing -> Done). Limit work in progress! 📋",
            "smart goals": "SMART Goals: Specific, Measurable, Achievable, Relevant, Time-bound. 🎯",
            "procrastination": "Procrastination often comes from fear or unclear tasks. Break it down into a 5-minute 'micro-task' and just start. 🚀",
            "burnout": "Burnout signs: exhaustion, cynicism, inefficiency. Take a real break, disconnect, and prioritize sleep. 🛌",
            "deep work": "Deep Work: Distraction-free concentration that pushes your cognitive capabilities to their limit. 🧠",
            "email": "Email Tip: Check email only 2-3 times a day (e.g., 11am, 4pm). Don't let it dictate your morning. 📧",
            "meeting": "Meetings: Ensure every meeting has an agenda. If you can't contribute, decline it or ask for a summary. 🤝",
            "multitasking": "Multitasking is a myth! It reduces IQ and productivity. Single-task handling is the way. 🚫",
            "habit": "Habit loop: Cue -> Routine -> Reward. Start small (e.g., 'After I pour coffee, I will write one sentence'). 🔄",
            "sleep": "Sleep is productivity's foundation. Aim for 7-9 hours to consolidate memory and clear brain toxins. 😴",
            "meditation": "Meditation improves focus and reduces stress. Try just 3 minutes of observing your breath. 🧘",
            "exercise": "Exercise boosts BDNF (brain fertilizer). Even a 20-min walk improves focus for hours! 🏃",
            "diet": "Brain food: Water, nuts, berries, fish. avoid heavy carb lunches to prevent the afternoon slump. 🍎",
            "music": "Music: Video game soundtracks or Lo-Fi beats are great for focus as they have no distracting lyrics. 🎧",
            "phone": "Phone addiction? Put it in another room or use grayscale mode to make it less stimulating. 📱",
            "motivation": "Motivation is fickle; habit is reliable. Don't wait to 'feel' like it. rely on discipline. 💪",
            "planning": "Plan your day the night before. You'll wake up with purpose instead of reacting to chaos. 🌙",
            "review": "Weekly Review: Every Friday, look back at what you achieved and plan the next week. 📅",
            "batching": "Batching: Group similar tasks (emails, calls, admin) and do them all at once to save mental energy. 📦",
            "say no": "Saying 'No' to the non-essential is saying 'Yes' to your goals. Protect your time! 🛡️"
        }

    def get_greeting(self):
        return random.choice(self.greetings)

    def get_encouragement(self):
        return random.choice(self.encouragements)

    def get_break_reminder(self):
        return random.choice(self.break_reminders)

    def get_tip(self):
        return random.choice(self.tips)

    def get_today_summary(self):
        """Get summary of today's productivity stats"""
        stats = self.app.data.user_profile.get('stats', {})
        total_mins = stats.get('total_minutes', 0)
        return f"You've focused for {total_mins} minutes total! Keep racking up those numbers! 📈"

    def get_response(self, user_message):
        """Generate response based on user message using offline knowledge base"""
        message = user_message.lower().strip()
        
        # 1. Check Knowledge Base (Fuzzy Match)
        # First check exact substrings to be fast
        for key, answer in self.knowledge_base.items():
            if key in message:
                return f"🧠 **{key.title()}**: {answer}"
                
        # Then check fuzzy matches for typos (e.g., "promodoro")
        keys = list(self.knowledge_base.keys())
        matches = difflib.get_close_matches(message, keys, n=1, cutoff=0.6)
        if matches:
            key = matches[0]
            answer = self.knowledge_base[key]
            return f"🤔 Did you mean **{key.title()}**? \n\n{answer}"

        # 2. Greetings
        if any(word in message for word in ['hi', 'hello', 'hey', 'sup', 'greetings']):
            return self.get_greeting()
        
        # 3. Session stats
        elif any(word in message for word in ['today', 'stats', 'progress', 'how am i']):
            return self.get_today_summary()
        
        # 4. Motivation
        elif any(word in message for word in ['motivate', 'encourage', 'inspire', 'sad', 'tired']):
            return self.get_encouragement()
        
        # 5. Break reminder
        elif any(word in message for word in ['break', 'rest', 'pause']):
            return self.get_break_reminder()
        
        # 6. Tips
        elif any(word in message for word in ['tip', 'help', 'advice', 'how', 'hack']):
            return self.get_tip()
        
        # 7. Start session
        elif any(word in message for word in ['start', 'begin', 'focus', 'work']):
            return "Let's do this! Head to the **Add Task** page and hit that Start button! 🚀 You got this!"
        
        # 8. Distraction help
        elif any(word in message for word in ['distract', 'focus', 'concentrate', 'bored']):
            return "I feel you! Try this: close unnecessary tabs, put phone away, and take 3 deep breaths. Then dive in! 🎯"
        
        # 9. Fallback / AI Upsell
        else:
            responses = [
                "I'm smart with topics like 'Pomodoro', 'Sleep', 'GTD', or 'Burnout'. Ask me! 📚",
                "I'm focused on productivity teaching! For open-ended AI chat, please add an API Key in Settings ⚙️",
                "I don't know that one yet! Try asking about 'Habits' or 'Deep Work'. 🧠",
                "To unlock my full brain power for *any* question, go to Settings > AI Integration! 🤖"
            ]
            return random.choice(responses)

    def get_ai_response(self, user_message):
        """Generate AI-powered response if available, otherwise fallback to offline mode"""
        # ALWAYS try AI first if available
        if self.ai and getattr(self.ai, 'enabled', False):
            try:
                reply = self.ai.generate(self.history, user_message)
                self.history.append({"role": "user", "content": user_message})
                self.history.append({"role": "assistant", "content": reply})
                if len(self.history) > 40:
                    self.history = self.history[-40:]
                return reply
            except Exception as e:
                # AI failed, fallback to offline
                return self.get_response(user_message) + "\n\n⚠️ (AI temporarily unavailable, using offline mode)"
        else:
            # No AI configured, use offline mode
            return self.get_response(user_message)
