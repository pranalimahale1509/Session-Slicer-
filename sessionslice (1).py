import tkinter as tk
import customtkinter as ctk
from tkinter import ttk, messagebox, colorchooser, filedialog, simpledialog, scrolledtext
from datetime import datetime, timedelta, date
import json, os, csv, threading, time, calendar as cal, random, tempfile
from collections import defaultdict
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt, numpy as np
from matplotlib import cm
try: from plyer import notification; NOTIFICATIONS_AVAILABLE = True
except ImportError: NOTIFICATIONS_AVAILABLE = False
# Optional audio/voice dependencies
try:
    import sounddevice as sd
    import soundfile as sf
    AUDIO_AVAILABLE = True
except Exception:
    AUDIO_AVAILABLE = False
try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except Exception:
    SR_AVAILABLE = False
try:
    import pyttsx3
    TTS_AVAILABLE = True
except Exception:
    TTS_AVAILABLE = False
# Load environment variables from .env if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass
APP_TITLE, DATA_DIR = "SessionSlice Productivity Tracker", "data"
os.makedirs(DATA_DIR, exist_ok=True)
FILES = {k: os.path.join(DATA_DIR, f"{k.lower()}.json") for k in ['SESSIONS', 'TASKS', 'SESSION_TYPES', 'GOALS', 'ACHIEVEMENTS', 'USER_PROFILE', 'THEMES', 'THEME_SETTINGS']}
SESSION_FILE, TASKS_FILE, SESSION_TYPES_FILE, GOALS_FILE, ACHIEVEMENTS_FILE, USER_PROFILE_FILE, THEMES_FILE, THEME_SETTINGS_FILE = FILES.values()
COLORS = {
    'primary': "#4474db",        # Modern blue
    'primary_dark': '#1d4ed8',   # Darker blue for hover
    'secondary': '#10b981',      # Modern green
    'secondary_dark': '#059669', # Darker green
    'accent': '#8b5cf6',         # Purple accent
    'accent_dark': '#7c3aed',    # Darker purple
    'background': "#ffffff",     # Light background
    'surface': "#ffffff",        # Card/surface color
    'surface_alt': "#FFFFFF",    # Alternative surface
    'text_primary': '#1e293b',   # Main text
    'text_secondary': '#64748b', # Secondary text
    'border': '#e2e8f0',         # Border color
    'success': '#22c55e',        # Success color
    'warning': '#f59e0b',        # Warning color
    'error': '#ef4444',          # Error color
    'timer': '#dc2626'           # Timer color
}
DEFAULT_TASK_COLOR = COLORS['primary']
DEFAULT_BREAK_COLOR = COLORS['secondary']
FONT_FAMILY = "Segoe UI"
FONT_SIZES = {
    'small': 9,
    'normal': 10,
    'medium': 11,
    'large': 12,
    'xlarge': 14,
    'xxlarge': 16,
    'title': 20,
    'timer': 28
}
def load_json(filepath, default): return json.load(open(filepath, "r")) if os.path.exists(filepath) else default
def save_json(filepath, data): json.dump(data, open(filepath, "w"), indent=2)
class ThemeManager:
    def __init__(self):
        self.themes = self._create_default_themes()
        self.custom_themes = load_json(THEMES_FILE, {})
        self.theme_settings = load_json(THEME_SETTINGS_FILE, {"current_theme": "light"})
        self.current_theme_name = self.theme_settings.get("current_theme", "light")
        self.theme_change_callbacks = []
    def _create_default_themes(self):
        base_colors = {'success': '#22c55e', 'warning': '#f59e0b', 'error': '#ef4444', 'timer': '#dc2626'}
        return {
            "light": {"name": "Light Theme", "colors": {'primary': "#4474db", 'primary_dark': '#1d4ed8', 'secondary': '#10b981', 'secondary_dark': '#059669', 'accent': '#8b5cf6', 'accent_dark': '#7c3aed', 'background': "#ffffff", 'surface': "#f8fafc", 'surface_alt': "#f1f5f9", 'text_primary': '#1e293b', 'text_secondary': '#64748b', 'border': '#e2e8f0', **base_colors}},
            "dark": {"name": "Dark Theme", "colors": {'primary': "#60a5fa", 'primary_dark': '#3b82f6', 'secondary': '#34d399', 'secondary_dark': '#10b981', 'accent': '#a78bfa', 'accent_dark': '#8b5cf6', 'background': "#0f172a", 'surface': "#1e293b", 'surface_alt': "#334155", 'text_primary': '#f1f5f9', 'text_secondary': '#94a3b8', 'border': '#475569', 'success': '#22c55e', 'warning': '#fbbf24', 'error': '#f87171', 'timer': '#f87171'}},
            "blue": {"name": "Ocean Blue", "colors": {'primary': "#0ea5e9", 'primary_dark': '#0284c7', 'secondary': '#06b6d4', 'secondary_dark': '#0891b2', 'accent': '#8b5cf6', 'accent_dark': '#7c3aed', 'background': "#f0f9ff", 'surface': "#e0f2fe", 'surface_alt': "#bae6fd", 'text_primary': '#0c4a6e', 'text_secondary': '#0369a1', 'border': '#7dd3fc', **base_colors}},
            "green": {"name": "Nature Green", "colors": {'primary': "#16a34a", 'primary_dark': '#15803d', 'secondary': '#059669', 'secondary_dark': '#047857', 'accent': '#8b5cf6', 'accent_dark': '#7c3aed', 'background': "#f0fdf4", 'surface': "#dcfce7", 'surface_alt': "#bbf7d0", 'text_primary': '#14532d', 'text_secondary': '#166534', 'border': '#86efac', **base_colors}},
            "purple": {"name": "Royal Purple", "colors": {'primary': "#9333ea", 'primary_dark': '#7c3aed', 'secondary': '#a855f7', 'secondary_dark': '#9333ea', 'accent': '#ec4899', 'accent_dark': '#db2777', 'background': "#faf5ff", 'surface': "#f3e8ff", 'surface_alt': "#e9d5ff", 'text_primary': '#581c87', 'text_secondary': '#6b21a8', 'border': '#c4b5fd', **base_colors}}
        }
    def get_current_theme(self):
        all_themes = {**self.themes, **self.custom_themes}
        return all_themes.get(self.current_theme_name, self.themes["light"])
    def get_theme_colors(self):
        return self.get_current_theme()["colors"]
    def _get_contrasting_text_color(self, background_color):
        """Calculate a contrasting text color based on background brightness"""
        bg = background_color.lstrip('#')
        r, g, b = int(bg[0:2], 16), int(bg[2:4], 16), int(bg[4:6], 16)
        brightness = (0.299 * r + 0.587 * g + 0.114 * b)
        return '#000000' if brightness > 128 else '#ffffff'
    def get_entry_colors(self):
        """Get appropriate colors for entry widgets with good contrast"""
        colors = self.get_theme_colors()
        entry_bg = colors.get('surface', '#ffffff')
        entry_fg = self._get_contrasting_text_color(entry_bg)
        return {
            'fieldbackground': entry_bg,
            'foreground': entry_fg,
            'insertcolor': entry_fg  # Cursor color
        }
    def set_theme(self, theme_name):
        all_themes = {**self.themes, **self.custom_themes}
        if theme_name in all_themes:
            self.current_theme_name = theme_name
            self.theme_settings["current_theme"] = theme_name
            self.save_theme_settings()
            global COLORS
            COLORS.update(self.get_theme_colors())
            for callback in self.theme_change_callbacks:
                callback()
    def get_available_themes(self):
        all_themes = {**self.themes, **self.custom_themes}
        return [(name, data["name"]) for name, data in all_themes.items()]
    def add_theme_change_callback(self, callback):
        self.theme_change_callbacks.append(callback)
    def save_theme_settings(self):
        save_json(THEME_SETTINGS_FILE, self.theme_settings)
    def save_custom_theme(self, theme_id, theme_name, colors):
        self.custom_themes[theme_id] = {
            "name": theme_name,
            "colors": colors.copy()
        }
        save_json(THEMES_FILE, self.custom_themes)
    def delete_custom_theme(self, theme_id):
        if theme_id in self.custom_themes:
            del self.custom_themes[theme_id]
            save_json(THEMES_FILE, self.custom_themes)
            if self.current_theme_name == theme_id:
                self.set_theme("light")
    def export_theme(self, theme_id, filepath):
        try:
            all_themes = {**self.themes, **self.custom_themes}
            if theme_id in all_themes:
                theme_data = all_themes[theme_id].copy()
                theme_data["exported_from"] = "SessionSlice"
                theme_data["export_date"] = datetime.now().isoformat()
                theme_data["theme_id"] = theme_id
                save_json(filepath, theme_data)
                return True
            return False
        except Exception as e:
            print(f"Export error: {e}")
            return False
    def import_theme(self, filepath, theme_id=None):
        try:
            theme_data = load_json(filepath, None)
            if not theme_data or "colors" not in theme_data:
                return False, "Invalid theme file format"
            if not theme_id:
                theme_id = f"imported_{int(time.time())}"
            self.save_custom_theme(
                theme_id,
                theme_data.get("name", "Imported Theme"),
                theme_data["colors"]
            )
            return True, f"Theme imported as '{theme_id}'"
        except Exception as e:
            return False, f"Failed to import theme: {str(e)}"
theme_manager = ThemeManager()
class ThemedDialog(tk.Toplevel):
    """Base class for themed dialog windows that automatically apply and respond to theme changes"""
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.app = None
        self._destroyed = False
        current = parent
        while current and not hasattr(current, 'theme_manager'):
            current = getattr(current, 'master', None) or getattr(current, 'app', None)
        if current and hasattr(current, 'theme_manager'):
            self.app = current
            if hasattr(self.app, '_open_dialogs'):
                self.app._open_dialogs.add(self)
        self._update_theme()
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
    def _update_theme(self):
        """Update dialog appearance based on current theme"""
        if self._destroyed:
            return
        try:
            if self.app and hasattr(self.app, 'theme_manager'):
                colors = self.app.theme_manager.get_theme_colors()
                self.configure(bg=colors.get('background', '#ffffff'))
        except tk.TclError:
            self._destroyed = True
            if self.app and hasattr(self.app, '_open_dialogs'):
                self.app._open_dialogs.discard(self)
    def _on_closing(self):
        """Handle dialog closing - cleanup tracking"""
        self._destroyed = True
        if self.app and hasattr(self.app, '_open_dialogs'):
            self.app._open_dialogs.discard(self)
        self.destroy()
    def destroy(self):
        """Override destroy to ensure cleanup"""
        self._destroyed = True
        if self.app and hasattr(self.app, '_open_dialogs'):
            self.app._open_dialogs.discard(self)
        super().destroy()
class SessionSliceData:
    def __init__(self):
        self.sessions = load_json(SESSION_FILE, [])
        self.tasks = load_json(TASKS_FILE, [{"name": "Sample Task", "color": DEFAULT_TASK_COLOR, "project": "General"}])
        # Normalize tasks to include completion flag
        for t in self.tasks:
            if isinstance(t, dict) and 'completed' not in t:
                t['completed'] = False
        self.session_types = load_json(SESSION_TYPES_FILE, [
            {"name": "Focus", "icon": "🔥", "color": DEFAULT_TASK_COLOR, "hours": 0, "minutes": 25},
            {"name": "Break", "icon": "☕", "color": DEFAULT_BREAK_COLOR, "hours": 0, "minutes": 5}
        ])
        self.goals = load_json(GOALS_FILE, [])
        default_profile = {
            "username": "Productivity Hero",
            "level": 1,
            "xp": 0,
            "total_xp": 0,
            "badges_earned": [],
            "achievements_unlocked": [],
            "join_date": datetime.now().strftime("%Y-%m-%d"),
            "stats": {
                "total_sessions": 0,
                "total_minutes": 0,
                "longest_streak": 0,
                "perfect_sessions": 0  
            }
        }
        self.user_profile = load_json(USER_PROFILE_FILE, default_profile)
        self.achievements = load_json(ACHIEVEMENTS_FILE, self._create_default_achievements())
        self._update_user_stats()
    def _create_default_achievements(self):
        """Create the default achievement definitions"""
        base = {"unlocked": False, "unlock_date": None}
        return [
            {"id": "first_session", "name": "Getting Started", "description": "Complete your first productivity session", "icon": "🎯", "category": "sessions", "requirement": 1, "xp_reward": 50, "badge": "🥇 First Timer", **base},
            {"id": "session_master", "name": "Session Master", "description": "Complete 50 productivity sessions", "icon": "🏆", "category": "sessions", "requirement": 50, "xp_reward": 500, "badge": "🏆 Session Master", **base},
            {"id": "century_club", "name": "Century Club", "description": "Complete 100 productivity sessions", "icon": "💯", "category": "sessions", "requirement": 100, "xp_reward": 1000, "badge": "💯 Century Club", **base},
            {"id": "focused_hour", "name": "Focused Hour", "description": "Accumulate 60 minutes of focused work", "icon": "⏰", "category": "time", "requirement": 60, "xp_reward": 100, "badge": "⏰ Time Keeper", **base},
            {"id": "marathon_runner", "name": "Marathon Runner", "description": "Accumulate 10 hours of focused work", "icon": "🏃", "category": "time", "requirement": 600, "xp_reward": 750, "badge": "🏃 Marathon Runner", **base},
            {"id": "streak_starter", "name": "Streak Starter", "description": "Maintain a 3-day productivity streak", "icon": "🔥", "category": "streak", "requirement": 3, "xp_reward": 150, "badge": "🔥 Streak Starter", **base},
            {"id": "week_warrior", "name": "Week Warrior", "description": "Maintain a 7-day productivity streak", "icon": "⚡", "category": "streak", "requirement": 7, "xp_reward": 400, "badge": "⚡ Week Warrior", **base},
            {"id": "consistency_champion", "name": "Consistency Champion", "description": "Maintain a 30-day productivity streak", "icon": "👑", "category": "streak", "requirement": 30, "xp_reward": 1500, "badge": "👑 Consistency Champion", **base},
            {"id": "focus_ninja", "name": "Focus Ninja", "description": "Complete 10 sessions with zero interruptions", "icon": "🥷", "category": "quality", "requirement": 10, "xp_reward": 300, "badge": "🥷 Focus Ninja", **base},
            {"id": "zen_master", "name": "Zen Master", "description": "Complete 25 sessions with zero interruptions", "icon": "🧘", "category": "quality", "requirement": 25, "xp_reward": 800, "badge": "🧘 Zen Master", **base},
            {"id": "goal_setter", "name": "Goal Setter", "description": "Create your first goal", "icon": "🎯", "category": "goals", "requirement": 1, "xp_reward": 75, "badge": "🎯 Goal Setter", **base},
            {"id": "goal_crusher", "name": "Goal Crusher", "description": "Complete 5 goals", "icon": "🎖️", "category": "goals", "requirement": 5, "xp_reward": 600, "badge": "🎖️ Goal Crusher", **base}
        ]
    def _update_user_stats(self):
        """Update user statistics based on current session data"""
        if not self.sessions:
            return
        stats = self.user_profile["stats"]
        stats["total_sessions"] = len(self.sessions)
        stats["total_minutes"] = sum(s.get("duration", 0) for s in self.sessions)
        stats["longest_streak"] = calculate_streak(self.sessions)
        stats["perfect_sessions"] = sum(1 for s in self.sessions if s.get("interruptions", 0) == 0)
    def calculate_level_from_xp(self, xp):
        """Calculate user level based on total XP (100 XP per level)"""
        return max(1, xp // 100 + 1)
    def xp_for_next_level(self):
        """Calculate XP needed for next level"""
        current_level = self.user_profile["level"]
        xp_for_current_level = (current_level - 1) * 100
        xp_for_next_level = current_level * 100
        return xp_for_next_level - self.user_profile["total_xp"]
    def add_xp(self, amount, reason=""):
        """Add XP to user profile and check for level up"""
        old_level = self.user_profile["level"]
        self.user_profile["xp"] += amount
        self.user_profile["total_xp"] += amount
        new_level = self.calculate_level_from_xp(self.user_profile["total_xp"])
        level_up = False
        if new_level > old_level:
            self.user_profile["level"] = new_level
            level_up = True
        return level_up, amount, reason
    def check_and_unlock_achievements(self):
        """Check all achievements and unlock any that meet requirements"""
        newly_unlocked = []
        for achievement in self.achievements:
            if achievement["unlocked"]:
                continue                
            current_value = 0
            category = achievement["category"]  
            if category == "sessions":
                current_value = self.user_profile["stats"]["total_sessions"]
            elif category == "time":
                current_value = self.user_profile["stats"]["total_minutes"]
            elif category == "streak":
                current_value = calculate_streak(self.sessions)
            elif category == "quality":
                current_value = self.user_profile["stats"]["perfect_sessions"]
            elif category == "goals":
                current_value = len([g for g in self.goals if g.get("completed", False)])     
            if current_value >= achievement["requirement"]:
                achievement["unlocked"] = True
                achievement["unlock_date"] = datetime.now().strftime("%Y-%m-%d")
                
                if achievement["badge"] not in self.user_profile["badges_earned"]:
                    self.user_profile["badges_earned"].append(achievement["badge"])
                
                if achievement["id"] not in self.user_profile["achievements_unlocked"]:
                    self.user_profile["achievements_unlocked"].append(achievement["id"])
                
                level_up, xp_gained, _ = self.add_xp(achievement["xp_reward"], 
                                                   f"Achievement: {achievement['name']}")
                
                newly_unlocked.append({
                    "achievement": achievement,
                    "xp_gained": xp_gained,
                    "level_up": level_up
                })
        return newly_unlocked
    def save_all(self):
        save_json(SESSION_FILE, self.sessions)
        save_json(TASKS_FILE, self.tasks)
        save_json(SESSION_TYPES_FILE, self.session_types)
        save_json(GOALS_FILE, self.goals)
        save_json(ACHIEVEMENTS_FILE, self.achievements)
        save_json(USER_PROFILE_FILE, self.user_profile)
class SessionSliceApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1150x700")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.iconbitmap(r"c:\Users\ADMIN\Downloads\5f1f374b-4242-463f-bbb3-e6f176b14082.jfif")
        self.data = SessionSliceData()
        self.theme_manager = theme_manager
        self._open_dialogs = set()
        global COLORS
        COLORS.update(self.theme_manager.get_theme_colors())
        self.theme_manager.add_theme_change_callback(self._on_theme_change)
        self._init_style()
        # Initialize assistant before building pages so ChatPage can access it
        self.ai_assistant = AIAssistant()
        self.chatbot = ProductivityChatbot(self, self.ai_assistant)
        self._create_main_widgets()
    def _init_style(self):
        style = ttk.Style(self)
        self.configure(bg=COLORS['background'])
        style.theme_use('clam')
        style.configure("Modern.TButton",
                       background=COLORS['primary'],
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       padding=(16, 8),
                       font=(FONT_FAMILY, FONT_SIZES['medium'], 'bold'))
        style.map("Modern.TButton",
                 background=[('active', COLORS['primary_dark']),
                            ('pressed', COLORS['primary_dark'])])
        style.configure("Secondary.TButton",
                       background=COLORS['secondary'],
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       padding=(12, 6),
                       font=(FONT_FAMILY, FONT_SIZES['medium']))
        style.map("Secondary.TButton",
                 background=[('active', COLORS['secondary_dark']),
                            ('pressed', COLORS['secondary_dark'])])
        style.configure("Nav.TButton",
                       background=COLORS['surface'],
                       foreground=COLORS['text_primary'],
                       borderwidth=1,
                       relief='flat',
                       focuscolor='none',
                       padding=(12, 10),
                       font=(FONT_FAMILY, FONT_SIZES['medium']))
        style.map("Nav.TButton",
                 background=[('active', COLORS['surface_alt']),
                            ('pressed', COLORS['primary']),
                            ('!pressed', COLORS['surface'])],
                 foreground=[('pressed', 'white'),
                            ('!pressed', COLORS['text_primary'])])
        style.configure("Timer.TLabel",
                       background=COLORS['background'],
                       foreground=COLORS['timer'],
                       font=(FONT_FAMILY, FONT_SIZES['timer'], 'bold'))
        style.configure("Title.TLabel",
                       background=COLORS['background'],
                       foreground=COLORS['text_primary'],
                       font=(FONT_FAMILY, FONT_SIZES['title'], 'bold'))
        style.configure("Heading.TLabel",
                       background=COLORS['background'],
                       foreground=COLORS['text_primary'],
                       font=(FONT_FAMILY, FONT_SIZES['xxlarge'], 'bold'))
        style.configure("TLabel",
                       background=COLORS['background'],
                       foreground=COLORS['text_primary'],
                       font=(FONT_FAMILY, FONT_SIZES['medium']))
        entry_colors = self.theme_manager.get_entry_colors()
        style.configure("TEntry",
                       fieldbackground=entry_colors['fieldbackground'],
                       foreground=entry_colors['foreground'],
                       insertcolor=entry_colors['insertcolor'],
                       borderwidth=1,
                       relief='solid',
                       padding=8,
                       font=(FONT_FAMILY, FONT_SIZES['medium']))
        style.configure("TCombobox",
                       fieldbackground=entry_colors['fieldbackground'],
                       foreground=entry_colors['foreground'],
                       borderwidth=1,
                       relief='solid',
                       padding=8,
                       font=(FONT_FAMILY, FONT_SIZES['medium']))
        style.map("TEntry",
                 focuscolor=[('focus', COLORS['primary'])],
                 bordercolor=[('focus', COLORS['primary'])])
        style.map("TCombobox",
                 focuscolor=[('focus', COLORS['primary'])],
                 bordercolor=[('focus', COLORS['primary'])])
        style.configure("Card.TFrame",
                       background=COLORS['surface'],
                       relief='solid',
                       borderwidth=1)    
        style.configure("TFrame",
                       background=COLORS['background'])
        style.configure("Treeview",
                       background=COLORS['surface'],
                       foreground=COLORS['text_primary'],
                       fieldbackground=COLORS['surface'],
                       font=(FONT_FAMILY, FONT_SIZES['medium']))
        style.configure("Treeview.Heading",
                       background=COLORS['surface_alt'],
                       foreground=COLORS['text_primary'],
                       font=(FONT_FAMILY, FONT_SIZES['medium'], 'bold'))
    def _create_main_widgets(self):
        self.sidebar = ttk.Frame(self, style="Card.TFrame", width=250)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(10, 5), pady=10)
        self.sidebar.pack_propagate(False)
        title_frame = ttk.Frame(self.sidebar)
        title_frame.pack(fill=tk.X, padx=15, pady=(15, 20))
        ttk.Label(title_frame, text="🎯 SessionSlice", style="Title.TLabel").pack()
        ttk.Label(title_frame, text="Productivity Tracker", 
                 font=(FONT_FAMILY, FONT_SIZES['small']), 
                 foreground=COLORS['text_secondary']).pack()
        self.nav_buttons = {}
        nav_items = [
            ("📊 Dashboard", self.show_dashboard),
            ("💬 Buddy Chat", self.show_chat),
            ("🤖 AI Insights", self.show_ai_insights),
            ("📅 Calendar", self.show_calendar),
            ("📝 Tasks", self.show_tasks),
            ("📈 Analytics", self.show_analytics),
            ("🏆 Goals", self.show_goals),
            ("🎖️ Achievements", self.show_achievements),
            ("⚙️ Settings", self.show_settings),
            ("ℹ️ About", self.show_about)
        ]
        for (txt, cmd) in nav_items:
            btn = ttk.Button(self.sidebar, text=txt, command=cmd, style="Nav.TButton")
            btn.pack(fill=tk.X, padx=10, pady=2)
            self.nav_buttons[txt] = btn
        self.content_frame = ttk.Frame(self)
        self.content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 10), pady=10)
        self.pages = {
            "Dashboard": DashboardPage(self.content_frame, self),
            "Chat": ChatPage(self.content_frame, self),
            "AIInsights": AIInsightsPage(self.content_frame, self),
            "Calendar": CalendarPage(self.content_frame, self),
            "Tasks": TasksPage(self.content_frame, self),
            "Analytics": AnalyticsPage(self.content_frame, self),
            "Goals": GoalsPage(self.content_frame, self),
            "Achievements": AchievementsPage(self.content_frame, self),
            "Reports": ReportsPage(self.content_frame, self),
            "Settings": SettingsPage(self.content_frame, self),
            "About": AboutPage(self.content_frame, self)
        }
        self.show_dashboard()
    def _clear_content(self):
        for child in self.content_frame.winfo_children():
            child.pack_forget()
    def _highlight_button(self, name):
        for button in self.nav_buttons.values():
            button.state(["!pressed"])
        self.nav_buttons[name].state(["pressed"])
    def _show_page(self, page_name, button_name, refresh=True):
        self._clear_content()
        if refresh and hasattr(self.pages[page_name], 'refresh'): self.pages[page_name].refresh()
        self.pages[page_name].pack(fill=tk.BOTH, expand=True)
        self._highlight_button(button_name)
    def show_dashboard(self): self._show_page("Dashboard", "📊 Dashboard")
    def show_tasks(self): self._show_page("Tasks", "📝 Tasks")
    def show_reports(self): self._show_page("Reports", "📈 Reports")
    def show_settings(self): self._show_page("Settings", "⚙️ Settings")
    def show_about(self): self._show_page("About", "ℹ️ About", False)
    def show_calendar(self): self._show_page("Calendar", "📅 Calendar")
    def show_analytics(self): self._show_page("Analytics", "📈 Analytics")
    def show_goals(self): self._show_page("Goals", "🏆 Goals")
    def show_achievements(self): self._show_page("Achievements", "🎖️ Achievements")
    def show_chat(self): self._show_page("Chat", "💬 Buddy Chat")
    def show_ai_insights(self): self._show_page("AIInsights", "🤖 AI Insights")
    def _on_theme_change(self):
        """Called when theme is changed to update all UI components"""
        self._init_style()
        for page in self.pages.values():
            if hasattr(page, '_on_theme_change'):
                page._on_theme_change()
        dialogs_to_remove = []
        for dialog in list(self._open_dialogs):
            try:
                if hasattr(dialog, '_update_theme') and not getattr(dialog, '_destroyed', False):
                    dialog._update_theme()
            except tk.TclError:
                dialogs_to_remove.append(dialog)
        for dialog in dialogs_to_remove:
            self._open_dialogs.discard(dialog)
        self.update_idletasks()


    def on_closing(self):
        if messagebox.askokcancel("Quit", "Save changes and quit?"):
            self.data.save_all()
            self.destroy()
class DashboardPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.session_running = False
        self.session_paused = False
        self.session_left = 0
        self.session_start_time = None
        self.break_count = 0
        self.interrupt_count = 0
        self._build_widgets()
    def _build_widgets(self):
        ttk.Label(self, text="📊 Dashboard", style="Heading.TLabel").pack(pady=(0, 20))
        timer_card = ttk.Frame(self, style="Card.TFrame")
        timer_card.pack(fill=tk.X, pady=(0, 20), padx=20)
        timer_frame = ttk.Frame(timer_card)
        timer_frame.pack(pady=30)
        self.timer_var = tk.StringVar(value="00:00")
        ttk.Label(timer_frame, textvariable=self.timer_var, style="Timer.TLabel").pack()
        self.status_var = tk.StringVar(value="Ready to start")
        ttk.Label(timer_frame, textvariable=self.status_var, font=(FONT_FAMILY, FONT_SIZES['medium']), foreground=COLORS['text_secondary']).pack(pady=(5, 0))
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(timer_frame, variable=self.progress_var, length=300, mode='determinate')
        config_card = ttk.Frame(self, style="Card.TFrame")
        config_card.pack(fill=tk.X, pady=(0, 15), padx=20)
        ttk.Label(config_card, text="Session Configuration", font=(FONT_FAMILY, FONT_SIZES['large'], 'bold')).pack(anchor=tk.W, padx=20, pady=15)
        config_content = ttk.Frame(config_card)
        config_content.pack(fill=tk.X, padx=20, pady=(0, 15))
        task_frame = ttk.Frame(config_content)
        task_frame.pack(fill=tk.X, pady=5)
        ttk.Label(task_frame, text="Task:", width=12).pack(side=tk.LEFT, anchor=tk.W)
        self.task_var = tk.StringVar()
        self.task_select = ttk.Combobox(task_frame, textvariable=self.task_var, state="readonly", width=30)
        self.task_select.pack(side=tk.LEFT, padx=(5, 0))
        self.task_select["values"] = self._task_names()
        type_frame = ttk.Frame(config_content)
        type_frame.pack(fill=tk.X, pady=5)
        ttk.Label(type_frame, text="Type:", width=12).pack(side=tk.LEFT, anchor=tk.W)
        self.type_var = tk.StringVar()
        self.type_select = ttk.Combobox(type_frame, textvariable=self.type_var, state="readonly", width=20)
        self.type_select.pack(side=tk.LEFT, padx=(5, 0))
        self.type_select["values"] = self._session_type_labels()
        # Duration selector
        duration_frame = ttk.Frame(config_content)
        duration_frame.pack(fill=tk.X, pady=5)
        ttk.Label(duration_frame, text="Duration (min):", width=12).pack(side=tk.LEFT, anchor=tk.W)
        self.duration_minutes_var = tk.IntVar(value=25)
        self.duration_spin = tk.Spinbox(duration_frame, from_=1, to=480, width=6, textvariable=self.duration_minutes_var)
        self.duration_spin.pack(side=tk.LEFT, padx=(5, 8))
        # Quick presets
        for val in (10, 25, 45):
            tk.Button(duration_frame, text=str(val), command=lambda v=val: self.duration_minutes_var.set(v),
                     bg=COLORS['surface_alt'], fg=COLORS['text_primary'], relief='flat', padx=6).pack(side=tk.LEFT, padx=2)
        # Tasks management inside Session Configuration
        tasks_card = ttk.Frame(config_card, style="Card.TFrame")
        tasks_card.pack(fill=tk.X, pady=(10, 10), padx=20)
        ttk.Label(tasks_card, text="Tasks", font=(FONT_FAMILY, FONT_SIZES['large'], 'bold')).pack(anchor=tk.W, pady=(10, 5))
        add_row = ttk.Frame(tasks_card)
        add_row.pack(fill=tk.X, padx=10, pady=(0, 8))
        self.new_task_var = tk.StringVar()
        ttk.Entry(add_row, textvariable=self.new_task_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(add_row, text="Add Task", command=self.add_task_from_entry, style="Secondary.TButton").pack(side=tk.LEFT, padx=(8,0))
        # Lists removed from Dashboard per request; task management is available on the Tasks page.
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=15)
        self.start_btn = ttk.Button(button_frame, text="▶️ Start Session", command=self.start_session, style="Modern.TButton")
        self.start_btn.pack(side=tk.LEFT, padx=5)
        self.pause_btn = ttk.Button(button_frame, text="⏸️ Pause", command=self.pause_resume_session, style="Secondary.TButton", state=tk.DISABLED)
        self.pause_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn = ttk.Button(button_frame, text="⏹️ Stop", command=self.stop_session, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        tracking_frame = ttk.Frame(self)
        tracking_frame.pack(pady=10)
        self.break_btn = ttk.Button(tracking_frame, text="☕ Break (0)", command=self.log_break, state=tk.DISABLED)
        self.break_btn.pack(side=tk.LEFT, padx=5)
        self.interrupt_btn = ttk.Button(tracking_frame, text="🚨 Interruption (0)", command=self.log_interrupt, state=tk.DISABLED)
        self.interrupt_btn.pack(side=tk.LEFT, padx=5)
        stats_container = ttk.Frame(self)
        stats_container.pack(fill=tk.X, pady=15, padx=20)
        today_card = ttk.Frame(stats_container, style="Card.TFrame")
        today_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        ttk.Label(today_card, text="📅 Today", font=(FONT_FAMILY, FONT_SIZES['medium'], 'bold')).pack(padx=15, pady=10)
        self.label_today = ttk.Label(today_card, text="0 minutes", font=(FONT_FAMILY, FONT_SIZES['xlarge'], 'bold'), foreground=COLORS['primary'])
        self.label_today.pack(pady=(0, 15))
        streak_card = ttk.Frame(stats_container, style="Card.TFrame")
        streak_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
        ttk.Label(streak_card, text="🔥 Streak", font=(FONT_FAMILY, FONT_SIZES['medium'], 'bold')).pack(padx=15, pady=10)
        self.label_streak = ttk.Label(streak_card, text="0 days", font=(FONT_FAMILY, FONT_SIZES['xlarge'], 'bold'), foreground=COLORS['secondary'])
        self.label_streak.pack(pady=(0, 15))
        sessions_card = ttk.Frame(self, style="Card.TFrame")
        sessions_card.pack(fill=tk.BOTH, expand=True, pady=15, padx=20)
        ttk.Label(sessions_card, text="📜 Recent Sessions", font=(FONT_FAMILY, FONT_SIZES['large'], 'bold')).pack(anchor=tk.W, padx=20, pady=15)
        sessions_content = ttk.Frame(sessions_card)
        sessions_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))
        self.recent_listbox = tk.Listbox(sessions_content, font=(FONT_FAMILY, FONT_SIZES['normal']), height=8, bg=COLORS['surface'], fg=COLORS['text_primary'], selectbackground=COLORS['primary'], selectforeground='white', borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(sessions_content, orient="vertical", command=self.recent_listbox.yview)
        self.recent_listbox.configure(yscrollcommand=scrollbar.set)
        self.recent_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        # Smart Reminders & Automation (right-side attribute)
        smart_card = ttk.Frame(self, style="Card.TFrame")
        smart_card.pack(fill=tk.X, pady=15, padx=20)
        header = ttk.Frame(smart_card)
        header.pack(fill=tk.X, padx=20, pady=(15, 8))
        ttk.Label(header, text="🤖 Smart Reminders & Automation", font=(FONT_FAMILY, FONT_SIZES['large'], 'bold')).pack(anchor=tk.W)
        smart_content = ttk.Frame(smart_card)
        smart_content.pack(fill=tk.X, padx=20, pady=(0, 15))
        # Context-Aware Notifications
        notif_frame = ttk.Frame(smart_content)
        notif_frame.pack(fill=tk.X, pady=4)
        ttk.Label(notif_frame, text="Context-Aware Notifications", font=(FONT_FAMILY, FONT_SIZES['medium'], 'bold')).pack(anchor=tk.W)
        ttk.Label(notif_frame, text="Analyzes your focus activity and suggests a session when you’ve been inactive.", foreground=COLORS['text_secondary']).pack(anchor=tk.W)
        self.notif_var = tk.StringVar(value="Checking inactivity...")
        ttk.Label(notif_frame, textvariable=self.notif_var).pack(anchor=tk.W)
        # Auto Goal Tracking
        goal_frame = ttk.Frame(smart_content)
        goal_frame.pack(fill=tk.X, pady=4)
        ttk.Label(goal_frame, text="Auto Goal Tracking", font=(FONT_FAMILY, FONT_SIZES['medium'], 'bold')).pack(anchor=tk.W)
        ttk.Label(goal_frame, text="Automatically tracks your progress toward long‑term goals from your sessions.", foreground=COLORS['text_secondary']).pack(anchor=tk.W)
        self.auto_goal_var = tk.StringVar(value="Calculating goal progress...")
        ttk.Label(goal_frame, textvariable=self.auto_goal_var).pack(anchor=tk.W)
        # Habit Learning
        habit_frame = ttk.Frame(smart_content)
        habit_frame.pack(fill=tk.X, pady=4)
        ttk.Label(habit_frame, text="Habit Learning", font=(FONT_FAMILY, FONT_SIZES['medium'], 'bold')).pack(anchor=tk.W)
        ttk.Label(habit_frame, text="Learns your rhythm and builds personalized schedule suggestions.", foreground=COLORS['text_secondary']).pack(anchor=tk.W)
        self.habit_var = tk.StringVar(value="Deriving your preferred focus time...")
        ttk.Label(habit_frame, textvariable=self.habit_var).pack(anchor=tk.W)
    def _task_names(self):
        return [t["name"] for t in self.app.data.tasks if not t.get('completed', False)]
    def _session_type_labels(self):
        return [f"{st['icon']} {st['name']}" for st in self.app.data.session_types]
    def start_session(self):
        task_name = self.task_var.get()
        if not task_name:
            messagebox.showwarning("Select Task", "Please select a task before starting the session.")
            return
        session_type_label = self.type_var.get()
        session_type = next((st for st in self.app.data.session_types if f"{st['icon']} {st['name']}" == session_type_label), None)
        if not session_type:
            session_type = self.app.data.session_types[0]
        # Determine duration from UI (spinbox) or session type fallback
        try:
            chosen_minutes = int(self.duration_minutes_var.get())
        except Exception:
            chosen_minutes = 0
        if chosen_minutes and chosen_minutes > 0:
            self.session_left = chosen_minutes * 60
        else:
            self.session_left = session_type.get("hours", 0) * 3600 + session_type.get("minutes", 25) * 60
            if self.session_left == 0:
                self.session_left = 25 * 60
        self.total_session_time = self.session_left
        self.session_start_time = datetime.now()
        self.session_running = True
        self.session_paused = False
        self.break_count = 0
        self.interrupt_count = 0
        self.status_var.set(f"Working on: {task_name}")
        self.progress_bar.pack(pady=(10, 0))
        self.update_buttons_state()
        self.update_timer()
        self.update_stats_labels()
    def pause_resume_session(self):
        if not self.session_running:
            return
        self.session_paused = not self.session_paused
        self.pause_btn.config(text="▶️ Resume" if self.session_paused else "⏸️ Pause")
        self.status_var.set("Session paused" if self.session_paused else f"Working on: {self.task_var.get()}")
        if not self.session_paused:
            self.update_timer()
    def stop_session(self, show_message=True):
        if not self.session_running or self.session_start_time is None:
            return
        elapsed_minutes = round((datetime.now() - self.session_start_time).total_seconds() / 60, 1)
        session_type_label = self.type_var.get()
        task_name = self.task_var.get()
        session_date = self.session_start_time.strftime("%Y-%m-%d") if self.session_start_time else ""
        session_start = self.session_start_time.strftime("%H:%M") if self.session_start_time else ""
        self.app.data.sessions.append({
            "name": task_name,
            "date": session_date,
            "start": session_start,
            "end": datetime.now().strftime("%H:%M"),
            "duration": elapsed_minutes,
            "breaks": self.break_count,
            "interruptions": self.interrupt_count,
            "session_type": session_type_label
        })
        self.app.data._update_user_stats()
        newly_unlocked = self.app.data.check_and_unlock_achievements()
        level_up, xp_gained, _ = self.app.data.add_xp(10, "Session completed")
        self.app.data.save_all()
        for achievement_info in newly_unlocked:
            achievement = achievement_info["achievement"]
            level_up_from_achievement = achievement_info["level_up"]
            xp_from_achievement = achievement_info["xp_gained"]
            message = f"🎉 Achievement Unlocked: {achievement['name']}\n\n"
            message += f"{achievement['description']}\n\n"
            message += f"Reward: {xp_from_achievement} XP"
            if level_up_from_achievement:
                message += f"\n🌟 LEVEL UP! You are now Level {self.app.data.user_profile['level']}"
            if achievement["badge"]:
                message += f"\n🏅 New Badge: {achievement['badge']}"
            messagebox.showinfo("Achievement Unlocked!", message)
        self.session_running = False
        self.session_paused = False
        self.session_left = 0
        self.session_start_time = None
        self.break_count = 0
        self.interrupt_count = 0
        self.timer_var.set("00:00")
        self.status_var.set("Ready to start")
        self.progress_bar.pack_forget()  # Hide progress bar
        self.pause_btn.config(text="⏸️ Pause")  # Reset pause button text
        self.break_btn.config(text="☕ Break (0)")  # Reset break button
        self.interrupt_btn.config(text="🚨 Interruption (0)")  # Reset interrupt button
        self.update_buttons_state()
        self.update_stats()
        if show_message:
            messagebox.showinfo("Session Complete!", f"Great work! Session '{task_name}' completed and saved.\n\nDuration: {elapsed_minutes} minutes")
    def update_buttons_state(self):
        state_running = tk.NORMAL if self.session_running else tk.DISABLED
        self.pause_btn.config(state=state_running)
        self.stop_btn.config(state=state_running)
        self.break_btn.config(state=state_running)
        self.interrupt_btn.config(state=state_running)
        self.start_btn.config(state=tk.DISABLED if self.session_running else tk.NORMAL)
    def update_timer(self):
        if self.session_running and not self.session_paused:
            mins, secs = divmod(self.session_left, 60)
            self.timer_var.set(f"{mins:02d}:{secs:02d}")
            if self.session_left > 0:
                self.session_left -= 1
                # Update progress percentage
                try:
                    progress = ((self.total_session_time - self.session_left) / self.total_session_time) * 100 if self.total_session_time else 0
                    self.progress_var.set(progress)
                except Exception:
                    pass
                self.after(1000, self.update_timer)
            else:
                messagebox.showinfo("Great job!", "Great job! Time's up!")
                self.stop_session(show_message=False)
    def log_break(self):
        if self.session_running and not self.session_paused:
            self.break_count += 1
            self.break_btn.config(text=f"☕ Break ({self.break_count})")
    def log_interrupt(self):
        if self.session_running and not self.session_paused:
            self.interrupt_count += 1
            self.interrupt_btn.config(text=f"🚨 Interruption ({self.interrupt_count})")

    def update_smart_reminders(self):
        try:
            ai = self.app.data.user_profile.get('ai', {})
            # Notifications status
            last_focus = ai.get('lastFocusTime')
            interval = int(ai.get('notificationInterval', 60))
            if last_focus:
                try:
                    last_dt = datetime.fromisoformat(last_focus)
                    mins = int((datetime.now() - last_dt).total_seconds() / 60)
                except Exception:
                    mins = None
            else:
                mins = None
            if mins is None:
                notif_text = f"No recent focus. I can remind you every {interval} min."
            else:
                if mins >= interval*2:
                    notif_text = f"Inactive for {mins} min. Suggest starting a {max(15, interval//2)}‑min session."
                else:
                    notif_text = f"Last focus {mins} min ago. Next gentle reminder in ~{max(1, interval - mins)} min."
            if hasattr(self, 'notif_var'):
                self.notif_var.set(notif_text)
            # Auto goal tracking summary
            goals = self.app.data.goals or []
            if goals:
                avg = int(sum(g.get('completionPercentage', 0) for g in goals) / len(goals))
                completed = sum(1 for g in goals if g.get('completed'))
                auto_text = f"{completed}/{len(goals)} goals completed • Avg progress {avg}%"
            else:
                auto_text = "No goals yet. Create one in Goals to start auto‑tracking."
            if hasattr(self, 'auto_goal_var'):
                self.auto_goal_var.set(auto_text)
            # Habit learning summary
            pref = ai.get('preferredTime') or 'Not learned yet'
            sugg = ai.get('dailySuggestion') or 'Complete a session to get personalized suggestions.'
            habit_text = f"Preferred: {pref}. {sugg}"
            if hasattr(self, 'habit_var'):
                self.habit_var.set(habit_text)
        except Exception:
            pass
    # Task management methods within Dashboard
    def _refresh_task_lists(self):
        if not hasattr(self, 'active_tasks_list'):
            return
        self.active_tasks_list.delete(0, tk.END)
        self.completed_tasks_list.delete(0, tk.END)
        for t in self.app.data.tasks:
            name = t.get('name','')
            if t.get('completed', False):
                self.completed_tasks_list.insert(tk.END, f"✓ {name}")
            else:
                self.active_tasks_list.insert(tk.END, name)
        # Update combobox values to only active tasks
        if hasattr(self, 'task_select'):
            self.task_select["values"] = self._task_names()
    def add_task_from_entry(self):
        name = (self.new_task_var.get() or '').strip()
        if not name:
            messagebox.showwarning("Task", "Enter a task name first.")
            return
        if any(t.get('name','').lower() == name.lower() for t in self.app.data.tasks):
            messagebox.showerror("Duplicate", "A task with this name already exists.")
            return
        self.app.data.tasks.append({"name": name, "project": "", "color": DEFAULT_TASK_COLOR, "completed": False})
        self.app.data.save_all()
        self.new_task_var.set("")
        self._refresh_task_lists()
    def _selected_active_task_name(self):
        sel = self.active_tasks_list.curselection()
        if not sel:
            return None
        return self.active_tasks_list.get(sel[0])
    def _selected_completed_task_name(self):
        sel = self.completed_tasks_list.curselection()
        if not sel:
            return None
        text = self.completed_tasks_list.get(sel[0])
        return text[2:] if text.startswith('✓ ') else text
    def mark_selected_active_completed(self):
        name = self._selected_active_task_name()
        if not name:
            return
        for t in self.app.data.tasks:
            if t.get('name') == name:
                t['completed'] = True
                break
        self.app.data.save_all()
        self._refresh_task_lists()
    def mark_selected_completed_incomplete(self):
        name = self._selected_completed_task_name()
        if not name:
            return
        for t in self.app.data.tasks:
            if t.get('name') == name:
                t['completed'] = False
                break
        self.app.data.save_all()
        self._refresh_task_lists()
    def delete_selected_active_task(self):
        name = self._selected_active_task_name()
        if not name:
            return
        if messagebox.askyesno("Delete Task", f"Delete task '{name}'?"):
            self.app.data.tasks = [t for t in self.app.data.tasks if t.get('name') != name]
            self.app.data.save_all()
            self._refresh_task_lists()
    def delete_selected_completed_task(self):
        name = self._selected_completed_task_name()
        if not name:
            return
        if messagebox.askyesno("Delete Task", f"Delete task '{name}'?"):
            self.app.data.tasks = [t for t in self.app.data.tasks if t.get('name') != name]
            self.app.data.save_all()
            self._refresh_task_lists()
    def update_stats(self):
        self.task_select["values"] = self._task_names()
        self.type_select["values"] = self._session_type_labels()
        self.update_stats_labels()
        self.update_recent_sessions()
        self.update_smart_reminders()
    def update_stats_labels(self):
        today = datetime.now().strftime("%Y-%m-%d")
        total_today = round(sum(s["duration"] for s in self.app.data.sessions if s["date"] == today))
        streak = calculate_streak(self.app.data.sessions)
        self.label_today.config(text=f"Today: {total_today} min")
        self.label_streak.config(text=f"Streak: {streak} day{'s' if streak != 1 else ''}")
    def update_recent_sessions(self):
        self.recent_listbox.delete(0, tk.END)
        for session in reversed(self.app.data.sessions[-15:]):
            text = (
                f"{session['date']} | {session.get('session_type', '')} | {session['name']} | "
                f"{round(session.get('duration', 0))} min | Breaks: {session.get('breaks', 0)} | "
                f"Interruptions: {session.get('interruptions', 0)}"
            )
            self.recent_listbox.insert(tk.END, text)
    def refresh(self):
        self.update_stats()
class TasksPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build_widgets()
    def _build_widgets(self):
        ttk.Label(self, text="Tasks", font=(FONT_FAMILY, FONT_SIZES['xxlarge'], 'bold')).pack(pady=10, anchor=tk.W)
        # Split layout: left = all tasks table, right = completed tasks list
        main = ttk.Frame(self)
        main.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 10))
        left = ttk.Frame(main)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6))
        right = ttk.Frame(main, style="Card.TFrame")
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(6, 0))
        # All tasks table with new columns
        columns = ("Task", "Time Taken", "Status")
        self.tree = ttk.Treeview(left, columns=columns, show="headings", selectmode="browse")
        for col, text, width in [("Task", "Task", 220), ("Time Taken", "Time Taken", 120), ("Status", "Status", 110)]:
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor=tk.W)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind('<Double-Button-1>', lambda e: self.toggle_selected_status())
        # Action buttons (no Add/Edit)
        btn_frame = ttk.Frame(left)
        btn_frame.pack(fill=tk.X, pady=8)
        ttk.Button(btn_frame, text="Mark Completed", command=self.mark_selected_completed, style="Secondary.TButton").pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Mark Incomplete", command=self.mark_selected_incomplete).pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_frame, text="Delete Task", command=self.delete_selected_task).pack(side=tk.LEFT, padx=6)
        # Completed tasks panel
        panel_inner = ttk.Frame(right)
        panel_inner.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        ttk.Label(panel_inner, text="Completed Tasks", font=(FONT_FAMILY, FONT_SIZES['large'], 'bold')).pack(anchor=tk.W)
        self.completed_list = tk.Listbox(panel_inner, height=12, bg=COLORS['surface'], fg=COLORS['text_secondary'],
                                         selectbackground=COLORS['secondary'], selectforeground='white', borderwidth=0, highlightthickness=0)
        self.completed_list.pack(fill=tk.BOTH, expand=True, pady=(6, 6))
        ttk.Button(panel_inner, text="Mark Incomplete", command=self.mark_completed_list_incomplete).pack(anchor=tk.W)
        self.refresh()
    def _task_time_minutes(self, task_name):
        try:
            return int(sum(s.get('duration', 0) for s in self.app.data.sessions if s.get('name') == task_name))
        except Exception:
            return 0
    def _status_text(self, t):
        return "Completed" if t.get('completed', False) else "Incomplete"
    def refresh(self):
        # refresh main table
        for item in self.tree.get_children():
            self.tree.delete(item)
        for task in self.app.data.tasks:
            mins = self._task_time_minutes(task.get('name',''))
            time_text = f"{mins} min" if mins < 60 else f"{mins//60}h {mins%60}m"
            self.tree.insert("", tk.END, values=(task.get('name',''), time_text, self._status_text(task)))
        # refresh completed panel
        self.completed_list.delete(0, tk.END)
        for t in self.app.data.tasks:
            if t.get('completed', False):
                mins = self._task_time_minutes(t.get('name',''))
                time_text = f"{mins}m" if mins < 60 else f"{mins//60}h {mins%60}m"
                self.completed_list.insert(tk.END, f"✓ {t.get('name','')} ({time_text})")
    def _selected_task_name_from_tree(self):
        sel = self.tree.focus()
        if not sel:
            return None
        vals = self.tree.item(sel, 'values')
        return vals[0] if vals else None
    def toggle_selected_status(self):
        name = self._selected_task_name_from_tree()
        if not name:
            return
        for t in self.app.data.tasks:
            if t.get('name') == name:
                t['completed'] = not t.get('completed', False)
                break
        self.app.data.save_all()
        self.refresh()
    def mark_selected_completed(self):
        name = self._selected_task_name_from_tree()
        if not name:
            return
        for t in self.app.data.tasks:
            if t.get('name') == name:
                t['completed'] = True
                break
        self.app.data.save_all(); self.refresh()
    def mark_selected_incomplete(self):
        name = self._selected_task_name_from_tree()
        if not name:
            return
        for t in self.app.data.tasks:
            if t.get('name') == name:
                t['completed'] = False
                break
        self.app.data.save_all(); self.refresh()
    def mark_completed_list_incomplete(self):
        sel = self.completed_list.curselection()
        if not sel:
            return
        label = self.completed_list.get(sel[0])
        # label format: "✓ name (Xm)"
        name = label[2:].strip()
        if ' (' in name:
            name = name.split(' (',1)[0]
        for t in self.app.data.tasks:
            if t.get('name') == name:
                t['completed'] = False
                break
        self.app.data.save_all(); self.refresh()
    def delete_selected_task(self):
        name = self._selected_task_name_from_tree()
        if not name:
            return
        if messagebox.askyesno("Delete Task", f"Delete task '{name}'?"):
            self.app.data.tasks = [t for t in self.app.data.tasks if t.get('name') != name]
            self.app.data.save_all(); self.refresh()
class TaskDialog(ThemedDialog):
    def __init__(self, parent, app, task, refresh_cb):
        super().__init__(parent)
        self.app, self.task, self.refresh_cb = app, task, refresh_cb
        self.title("Add/Edit Task")
        self.geometry("350x200")
        self.resizable(False, False)
        self.name_var = tk.StringVar(value=task["name"] if task else "")
        self.project_var = tk.StringVar(value=task.get("project", "") if task else "")
        ttk.Label(self, text="Task Name:", font=("Segoe UI", 11, "bold")).pack(anchor=tk.W, padx=12, pady=6)
        ttk.Entry(self, textvariable=self.name_var).pack(fill=tk.X, padx=12)
        ttk.Label(self, text="Project (optional):", font=("Segoe UI", 11)).pack(anchor=tk.W, padx=12, pady=6)
        ttk.Entry(self, textvariable=self.project_var).pack(fill=tk.X, padx=12)
        self.color = task.get("color", DEFAULT_TASK_COLOR) if task else DEFAULT_TASK_COLOR
        ttk.Button(self, text="Pick Color", command=self.pick_color).pack(pady=10)
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=8)
        ttk.Button(btn_frame, text="Save", command=self.save_task).pack(side=tk.LEFT, padx=8)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.LEFT, padx=8)
    def pick_color(self):
        c = colorchooser.askcolor(color=self.color)
        if c[1]:
            self.color = c[1]
    def save_task(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Validation Error", "Task name is required.")
            return
        project = self.project_var.get().strip()
        if self.task:
            self.task["name"] = name
            self.task["project"] = project
            self.task["color"] = self.color
        else:
            if any(t["name"] == name for t in self.app.data.tasks):
                messagebox.showerror("Duplicate Task", "Task with this name already exists.")
                return
            self.app.data.tasks.append({"name": name, "project": project, "color": self.color})
        self.app.data.save_all()
        self.refresh_cb()
        self.destroy()
class ReportsPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        ttk.Label(self, text="Reports & Analytics", font=("Segoe UI", 16, "bold")).pack(pady=10)
        self.fig = Figure(figsize=(7, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=15)
    def refresh(self):
        self.ax.clear()
        type_time = defaultdict(float)
        for s in self.app.data.sessions[-30:]:
            type_time[s.get("session_type", "Unknown")] += s.get("duration", 0)
        labels = list(type_time.keys())
        sizes = [type_time[l] for l in labels]
        if not labels:
            labels = ['No Data']
            sizes = [1]
        self.ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
        self.ax.set_title("Time Distribution by Session Type (Last 30 Sessions)")
        self.canvas.draw()
class SettingsPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build_widgets()
    def _build_widgets(self):
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        ttk.Label(header_frame, text="⚙️ Settings & Customization", style="Heading.TLabel").pack()
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        self.themes_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.themes_frame, text="🎨 Themes")
        self._build_themes_tab()
        self.session_types_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.session_types_frame, text="⏱️ Session Types")
        self._build_session_types_tab()
    def _build_themes_tab(self):
        theme_card = ttk.Frame(self.themes_frame, style="Card.TFrame")
        theme_card.pack(fill=tk.X, padx=20, pady=(20, 10))
        theme_header = ttk.Frame(theme_card)
        theme_header.pack(fill=tk.X, padx=20, pady=(15, 10))
        ttk.Label(theme_header, text="🌈 Theme Selection", 
                 font=(FONT_FAMILY, FONT_SIZES['large'], 'bold')).pack(anchor=tk.W)
        theme_content = ttk.Frame(theme_card)
        theme_content.pack(fill=tk.X, padx=20, pady=(0, 15))
        current_frame = ttk.Frame(theme_content)
        current_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(current_frame, text="Current Theme:", width=15).pack(side=tk.LEFT)
        self.current_theme_var = tk.StringVar()
        current_theme_label = ttk.Label(current_frame, textvariable=self.current_theme_var, 
                                      font=(FONT_FAMILY, FONT_SIZES['medium'], 'bold'),
                                      foreground=COLORS['primary'])
        current_theme_label.pack(side=tk.LEFT, padx=(10, 0))
        selection_frame = ttk.Frame(theme_content)
        selection_frame.pack(fill=tk.X, pady=5)
        ttk.Label(selection_frame, text="Select Theme:", width=15).pack(side=tk.LEFT, anchor=tk.W)
        self.theme_var = tk.StringVar()
        self.theme_combo = ttk.Combobox(selection_frame, textvariable=self.theme_var, 
                                       state="readonly", width=30)
        self.theme_combo.pack(side=tk.LEFT, padx=(10, 0))
        theme_buttons = ttk.Frame(theme_content)
        theme_buttons.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(theme_buttons, text="🌙 Dark Mode", 
                  command=lambda: self.apply_theme("dark"), style="Secondary.TButton").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(theme_buttons, text="☀️ Light Mode", 
                  command=lambda: self.apply_theme("light"), style="Secondary.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(theme_buttons, text="🎨 Apply Selected", 
                  command=self.apply_selected_theme, style="Modern.TButton").pack(side=tk.LEFT, padx=5)
        custom_card = ttk.Frame(self.themes_frame, style="Card.TFrame")
        custom_card.pack(fill=tk.X, padx=20, pady=10)
        custom_header = ttk.Frame(custom_card)
        custom_header.pack(fill=tk.X, padx=20, pady=(15, 10))
        ttk.Label(custom_header, text="🎭 Custom Themes", 
                 font=(FONT_FAMILY, FONT_SIZES['large'], 'bold')).pack(anchor=tk.W)
        custom_buttons = ttk.Frame(custom_card)
        custom_buttons.pack(fill=tk.X, padx=20, pady=(0, 15))
        ttk.Button(custom_buttons, text="➕ Create Custom Theme", 
                  command=self.create_custom_theme, style="Modern.TButton").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(custom_buttons, text="📁 Import Theme", 
                  command=self.import_theme, style="Secondary.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(custom_buttons, text="💾 Export Theme", 
                  command=self.export_theme, style="Secondary.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(custom_buttons, text="🗑️ Delete Custom Theme", 
                  command=self.delete_custom_theme).pack(side=tk.LEFT, padx=5)
        preview_card = ttk.Frame(self.themes_frame, style="Card.TFrame")
        preview_card.pack(fill=tk.BOTH, expand=True, padx=20, pady=(10, 20))
        preview_header = ttk.Frame(preview_card)
        preview_header.pack(fill=tk.X, padx=20, pady=(15, 10))
        ttk.Label(preview_header, text="👀 Color Preview", 
                 font=(FONT_FAMILY, FONT_SIZES['large'], 'bold')).pack(anchor=tk.W)
        self.preview_frame = ttk.Frame(preview_card)
        self.preview_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))
    def _build_session_types_tab(self):
        header = ttk.Frame(self.session_types_frame)
        header.pack(fill=tk.X, padx=20, pady=(20, 10))
        ttk.Label(header, text="⏱️ Session Types Management", 
                 font=(FONT_FAMILY, FONT_SIZES['large'], 'bold')).pack(anchor=tk.W)
        tree_frame = ttk.Frame(self.session_types_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))
        self.tree = ttk.Treeview(tree_frame, columns=("Color", "Hours", "Minutes"), 
                                show="headings", selectmode="browse")
        self.tree.heading("Color", text="Color")
        self.tree.heading("Hours", text="Hours") 
        self.tree.heading("Minutes", text="Minutes")
        self.tree.pack(fill=tk.BOTH, expand=True)
        btn_frame = ttk.Frame(self.session_types_frame)
        btn_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        ttk.Button(btn_frame, text="➕ Add Session Type", 
                  command=self.add_type, style="Modern.TButton").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="🗑️ Delete Selected", 
                  command=self.del_type).pack(side=tk.LEFT)
    def _update_theme_preview(self):
        """Update the color preview based on current theme"""
        try:
            for widget in self.preview_frame.winfo_children():
                widget.destroy()
            colors = COLORS
            color_items = [
                ('Primary', 'primary'),
                ('Secondary', 'secondary'), 
                ('Background', 'background'),
                ('Surface', 'surface'),
                ('Text Primary', 'text_primary'),
                ('Text Secondary', 'text_secondary'),
                ('Success', 'success'),
                ('Warning', 'warning'),
                ('Error', 'error'),
                ('Timer', 'timer')
            ]
            for i, (name, color_key) in enumerate(color_items):
                row = i // 5
                col = i % 5
                color_frame = ttk.Frame(self.preview_frame)
                color_frame.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
                color_canvas = tk.Canvas(color_frame, width=40, height=40, 
                                       bg=colors.get(color_key, '#000000'), 
                                       relief='solid', borderwidth=1)
                color_canvas.pack()
                ttk.Label(color_frame, text=name, 
                         font=(FONT_FAMILY, FONT_SIZES['small'])).pack()
                ttk.Label(color_frame, text=colors.get(color_key, '#000000'), 
                         font=(FONT_FAMILY, FONT_SIZES['small']),
                         foreground=COLORS['text_secondary']).pack()
            for i in range(5):
                self.preview_frame.columnconfigure(i, weight=1)
        except Exception as e:
            ttk.Label(self.preview_frame, text=f"Preview error: {str(e)}").pack(pady=20)
    def apply_theme(self, theme_name):
        """Apply a specific theme by name"""
        self.app.theme_manager.set_theme(theme_name)
        self.refresh()
        messagebox.showinfo("Theme Applied", f"Theme '{theme_name}' has been applied!")
    def apply_selected_theme(self):
        """Apply the currently selected theme"""
        selected = self.theme_var.get()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a theme first.")
            return
        available_themes = self.app.theme_manager.get_available_themes()
        theme_id = None
        for tid, name in available_themes:
            if name == selected:
                theme_id = tid
                break
        if theme_id:
            self.app.theme_manager.set_theme(theme_id)
            self.refresh()
            messagebox.showinfo("Theme Applied", f"Theme '{selected}' has been applied!")
        else:
            messagebox.showerror("Error", "Selected theme not found.")
    def create_custom_theme(self):
        """Open custom theme editor"""
        ThemeEditorDialog(self, self.app, self.refresh)
    def import_theme(self):
        """Import a theme from file"""
        filepath = filedialog.askopenfilename(
            title="Import Theme File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filepath:
            success, message = self.app.theme_manager.import_theme(filepath)
            if success:
                self.refresh()
                messagebox.showinfo("Import Successful", message)
            else:
                messagebox.showerror("Import Failed", message)
    def export_theme(self):
        """Export current theme to file"""
        current_theme = self.app.theme_manager.current_theme_name
        filepath = filedialog.asksaveasfilename(
            title="Export Theme",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=f"{current_theme}_theme.json"
        )
        if filepath:
            success = self.app.theme_manager.export_theme(current_theme, filepath)
            if success:
                messagebox.showinfo("Export Successful", f"Theme exported to {filepath}")
            else:
                messagebox.showerror("Export Failed", "Failed to export theme.")
    def delete_custom_theme(self):
        """Delete a custom theme"""
        available_themes = self.app.theme_manager.get_available_themes()
        custom_themes = [(tid, name) for tid, name in available_themes 
                        if tid not in self.app.theme_manager.themes]
        if not custom_themes:
            messagebox.showinfo("No Custom Themes", "No custom themes available to delete.")
            return
        theme_names = [f"{tid} - {name}" for tid, name in custom_themes]
        selected = simpledialog.askstring(
            "Delete Custom Theme",
            f"Enter theme ID to delete:\n\nAvailable: {', '.join([tid for tid, _ in custom_themes])}"
        )
        if selected and selected in [tid for tid, _ in custom_themes]:
            if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete theme '{selected}'?"):
                self.app.theme_manager.delete_custom_theme(selected)
                self.refresh()
                messagebox.showinfo("Theme Deleted", f"Custom theme '{selected}' has been deleted.")
    def refresh(self):
        """Refresh all settings data"""
        self._refresh_themes()
        self._refresh_session_types()
        self._update_theme_preview()
    def _refresh_themes(self):
        """Refresh theme-related UI elements"""
        current_theme = self.app.theme_manager.get_current_theme()
        self.current_theme_var.set(current_theme['name'])
        available_themes = self.app.theme_manager.get_available_themes()
        theme_options = [f"{name}" for theme_id, name in available_themes]
        self.theme_combo['values'] = theme_options
    def _refresh_session_types(self):
        """Refresh session types tree"""
        for i in self.tree.get_children():
            self.tree.delete(i)
        for st in self.app.data.session_types:
            self.tree.insert("", tk.END,
                             values=(st.get("color", "#000000"), 
                                   st.get("hours", 0), 
                                   st.get("minutes", 25)),
                             text=f"{st.get('icon', '')} {st.get('name', '')}")
    def add_type(self):
        """Add new session type"""
        SessionTypeDialog(self, self.app, None, self.refresh).grab_set()
    def del_type(self):
        """Delete selected session type"""
        sel = self.tree.focus()
        if not sel:
            messagebox.showwarning("Select", "Please select a session type to delete.")
            return
        idx = self.tree.index(sel)
        if 0 <= idx < len(self.app.data.session_types):
            st = self.app.data.session_types[idx]
            label = f"{st.get('icon','')} {st.get('name','')}"
            if messagebox.askyesno("Delete", f"Delete session type {label}?"):
                del self.app.data.session_types[idx]
                self.app.data.save_all()
                self.refresh()
class ThemeEditorDialog(ThemedDialog):
    def __init__(self, parent, app, refresh_callback):
        super().__init__(parent)
        self.app = app
        self.refresh_callback = refresh_callback
        self.title("Custom Theme Editor")
        self.geometry("600x500")
        self.resizable(False, False)
        self.grab_set()
        current_theme = self.app.theme_manager.get_current_theme()
        self.colors = current_theme["colors"].copy()
        self._build_widgets()
    def _build_widgets(self):
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, padx=20, pady=10)
        ttk.Label(header_frame, text="🎨 Custom Theme Editor", 
                 font=(FONT_FAMILY, FONT_SIZES['large'], 'bold')).pack()
        name_frame = ttk.Frame(self)
        name_frame.pack(fill=tk.X, padx=20, pady=5)
        ttk.Label(name_frame, text="Theme Name:").pack(anchor=tk.W)
        self.theme_name_var = tk.StringVar(value="My Custom Theme")
        self.theme_name_entry = ttk.Entry(name_frame, textvariable=self.theme_name_var, width=50)
        self.theme_name_entry.pack(fill=tk.X, pady=(5, 0))
        colors_frame = ttk.Frame(self)
        colors_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        canvas = tk.Canvas(colors_frame, height=280)  # Fixed height
        scrollbar = ttk.Scrollbar(colors_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self._create_color_pickers()
        button_frame = ttk.Frame(self)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=15)
        button_container = ttk.Frame(button_frame)
        button_container.pack()
        ttk.Button(button_container, text="Preview Theme", command=self._preview_theme,
                  style="Secondary.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(button_container, text="Save Theme", command=self._save_theme,
                  style="Modern.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(button_container, text="Cancel", command=self.destroy).pack(side=tk.LEFT, padx=5)
    def _create_color_pickers(self):
        """Create color picker widgets for each color in the theme"""
        self.color_vars = {}
        self.color_buttons = {}
        color_definitions = [
            ('primary', 'Primary Color', 'Main accent color for buttons and highlights'),
            ('primary_dark', 'Primary Dark', 'Darker shade of primary for hover states'),
            ('secondary', 'Secondary Color', 'Secondary accent color'),
            ('secondary_dark', 'Secondary Dark', 'Darker shade of secondary'),
            ('accent', 'Accent Color', 'Additional accent color'),
            ('accent_dark', 'Accent Dark', 'Darker shade of accent'),
            ('background', 'Background', 'Main background color'),
            ('surface', 'Surface', 'Card and surface background color'),
            ('surface_alt', 'Surface Alt', 'Alternative surface color'),
            ('text_primary', 'Text Primary', 'Main text color'),
            ('text_secondary', 'Text Secondary', 'Secondary text color'),
            ('border', 'Border', 'Border and divider color'),
            ('success', 'Success', 'Success/positive feedback color'),
            ('warning', 'Warning', 'Warning/caution color'),
            ('error', 'Error', 'Error/negative feedback color'),
            ('timer', 'Timer', 'Timer display color')
        ]
        for i, (color_key, color_name, description) in enumerate(color_definitions):
            color_frame = ttk.Frame(self.scrollable_frame)
            color_frame.pack(fill=tk.X, pady=5)
            info_frame = ttk.Frame(color_frame)
            info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
            ttk.Label(info_frame, text=color_name,
                     font=(FONT_FAMILY, FONT_SIZES['medium'], 'bold')).pack(anchor=tk.W)
            ttk.Label(info_frame, text=description,
                     font=(FONT_FAMILY, FONT_SIZES['small']),
                     foreground=COLORS['text_secondary']).pack(anchor=tk.W)
            value_frame = ttk.Frame(color_frame)
            value_frame.pack(side=tk.RIGHT, padx=(10, 0))
            self.color_vars[color_key] = tk.StringVar(value=self.colors[color_key])
            color_button = tk.Button(value_frame, 
                                   width=8, height=2,
                                   bg=self.colors[color_key],
                                   command=lambda key=color_key: self._pick_color(key))
            color_button.pack(side=tk.LEFT, padx=(0, 5))
            self.color_buttons[color_key] = color_button
            ttk.Label(value_frame, textvariable=self.color_vars[color_key],
                     font=(FONT_FAMILY, FONT_SIZES['small'])).pack(side=tk.LEFT)
    def _pick_color(self, color_key):
        """Open color picker for a specific color"""
        current_color = self.colors[color_key]
        color_result = colorchooser.askcolor(color=current_color)
        if color_result[1]:  # If user didn't cancel
            new_color = color_result[1]
            self.colors[color_key] = new_color
            self.color_vars[color_key].set(new_color)
            self.color_buttons[color_key].configure(bg=new_color)
    def _preview_theme(self):
        """Apply the theme temporarily for preview"""
        original_theme = self.app.theme_manager.current_theme_name
        temp_theme_id = "__preview__"
        self.app.theme_manager.save_custom_theme(
            temp_theme_id,
            "Preview Theme",
            self.colors
        )
        self.app.theme_manager.set_theme(temp_theme_id)
        result = messagebox.askyesno(
            "Theme Preview", 
            "This is a preview of your custom theme.\n\n" +
            "Click 'Yes' to keep this preview active while editing,\n" +
            "or 'No' to return to the original theme."
        )
        if not result:
            self.app.theme_manager.set_theme(original_theme)
            if temp_theme_id in self.app.theme_manager.custom_themes:
                del self.app.theme_manager.custom_themes[temp_theme_id]
    def _save_theme(self):
        """Save the custom theme"""
        theme_name = self.theme_name_var.get().strip()
        if not theme_name:
            messagebox.showerror("Error", "Please enter a theme name.")
            return
        theme_id = theme_name.lower().replace(' ', '_').replace('-', '_')
        theme_id = ''.join(c for c in theme_id if c.isalnum() or c == '_')
        all_themes = {**self.app.theme_manager.themes, **self.app.theme_manager.custom_themes}
        if theme_id in all_themes:
            if not messagebox.askyesno("Theme Exists", 
                                      f"A theme with ID '{theme_id}' already exists.\n\n" +
                                      "Do you want to overwrite it?"):
                return
        self.app.theme_manager.save_custom_theme(theme_id, theme_name, self.colors)
        self.app.theme_manager.set_theme(theme_id)
        self.refresh_callback()
        messagebox.showinfo("Success", f"Theme '{theme_name}' saved successfully!")
        self.destroy()
class SessionTypeDialog(ThemedDialog):
    def __init__(self, parent, app, stype, refresh_cb):
        super().__init__(parent)
        self.app = app
        self.stype = stype
        self.refresh_cb = refresh_cb
        self.title("Add/Edit Session Type")
        self.geometry("400x400")
        self.resizable(False, False)
        self.icon_var = tk.StringVar(value="💡" if not stype else stype.get("icon", ""))
        self.name_var = tk.StringVar(value="" if not stype else stype.get("name", ""))
        self.hours_var = tk.IntVar(value=stype.get("hours", 0) if stype else 0)
        self.minutes_var = tk.IntVar(value=stype.get("minutes", 25) if stype else 25)
        ttk.Label(self, text="Icon (Emoji):", font=("Segoe UI", 11)).pack(pady=5)
        ttk.Entry(self, textvariable=self.icon_var, width=30).pack()
        ttk.Label(self, text="Name:", font=("Segoe UI", 11)).pack(pady=5)
        ttk.Entry(self, textvariable=self.name_var, width=30).pack()
        ttk.Label(self, text="Color:", font=("Segoe UI", 11)).pack(pady=5)
        self.color = stype.get("color", DEFAULT_TASK_COLOR) if stype else DEFAULT_TASK_COLOR
        ttk.Button(self, text="Pick Color", command=self.pick_color).pack()
        ttk.Label(self, text="Hours:", font=("Segoe UI", 11)).pack(pady=5)
        ttk.Entry(self, textvariable=self.hours_var, width=10).pack()
        ttk.Label(self, text="Minutes:", font=("Segoe UI", 11)).pack(pady=5)
        ttk.Entry(self, textvariable=self.minutes_var, width=10).pack()
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Save", command=self.save_type).pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.LEFT, padx=6)
    def pick_color(self):
        selected = colorchooser.askcolor(color=self.color)[1]
        if selected:
            self.color = selected
    def save_type(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Input Error", "You must enter a name for session type.")
            return
        icon = self.icon_var.get().strip() or "💡"
        hours = self.hours_var.get()
        minutes = self.minutes_var.get()
        color = self.color
        if self.stype:
            self.stype.update({"icon": icon, "name": name, "color": color, "hours": hours, "minutes": minutes})
        else:
            if any(s.get("name") == name for s in self.app.data.session_types):
                messagebox.showerror("Duplicate", "Session type with that name exists.")
                return
            self.app.data.session_types.append({"icon": icon, "name": name, "color": color, "hours": hours, "minutes": minutes})
        self.app.data.save_all()
        self.refresh_cb()
        self.destroy()
class CalendarPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build_widgets()
    def _build_widgets(self):
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        ttk.Label(header_frame, text="📅 Calendar View", style="Heading.TLabel").pack()
        controls_card = ttk.Frame(self, style="Card.TFrame")
        controls_card.pack(fill=tk.X, pady=(0, 20), padx=20)
        controls_frame = ttk.Frame(controls_card)
        controls_frame.pack(padx=20, pady=15)
        nav_frame = ttk.Frame(controls_frame)
        nav_frame.pack(fill=tk.X, pady=(0, 10))
        self.current_date = datetime.now()
        ttk.Button(nav_frame, text="◀", command=self.prev_month, style="Secondary.TButton").pack(side=tk.LEFT)
        self.month_var = tk.StringVar(value=self.current_date.strftime("%B %Y"))
        self.month_label = ttk.Label(nav_frame, textvariable=self.month_var, 
                                   font=(FONT_FAMILY, FONT_SIZES['large'], 'bold'))
        self.month_label.pack(side=tk.LEFT, expand=True)
        ttk.Button(nav_frame, text="▶", command=self.next_month, style="Secondary.TButton").pack(side=tk.RIGHT)
        calendar_card = ttk.Frame(self, style="Card.TFrame")
        calendar_card.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        self.calendar_frame = ttk.Frame(calendar_card)
        self.calendar_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        for i, day in enumerate(days):
            ttk.Label(self.calendar_frame, text=day, 
                     font=(FONT_FAMILY, FONT_SIZES['medium'], 'bold')).grid(
                row=0, column=i, padx=2, pady=2, sticky="ew")
        self.day_buttons = {}
        self.refresh()
    def prev_month(self):
        if self.current_date.month == 1:
            self.current_date = self.current_date.replace(year=self.current_date.year-1, month=12)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month-1)
        self.refresh()
    def next_month(self):
        if self.current_date.month == 12:
            self.current_date = self.current_date.replace(year=self.current_date.year+1, month=1)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month+1)
        self.refresh()
    def refresh(self):
        self.month_var.set(self.current_date.strftime("%B %Y"))
        for widget in self.day_buttons.values():
            widget.destroy()
        self.day_buttons.clear()
        month_calendar = cal.monthcalendar(self.current_date.year, self.current_date.month)
        month_sessions = self._get_month_sessions()
        for week_num, week in enumerate(month_calendar, 1):
            for day_num, day in enumerate(week):
                if day == 0:
                    continue
                date_str = f"{self.current_date.year}-{self.current_date.month:02d}-{day:02d}"
                session_count = month_sessions.get(date_str, 0)
                session_time = sum(s["duration"] for s in self.app.data.sessions if s["date"] == date_str)
                btn_text = f"{day}"
                if session_count > 0:
                    btn_text += f"\n{session_count}s, {int(session_time)}m"
                day_btn = tk.Button(self.calendar_frame, text=btn_text,
                                  width=8, height=3,
                                  bg=COLORS['surface'],
                                  fg=COLORS['text_primary'] if session_count == 0 else COLORS['primary'],
                                  font=(FONT_FAMILY, FONT_SIZES['small']),
                                  relief='solid',
                                  borderwidth=1,
                                  command=lambda d=day: self.show_day_details(d))
                day_btn.grid(row=week_num, column=day_num, padx=1, pady=1, sticky="nsew")
                self.day_buttons[f"{week_num}_{day_num}"] = day_btn
        for i in range(7):
            self.calendar_frame.columnconfigure(i, weight=1)
        for i in range(1, len(month_calendar)+1):
            self.calendar_frame.rowconfigure(i, weight=1)
    def _get_month_sessions(self):
        """Get session count by date for current month"""
        month_start = f"{self.current_date.year}-{self.current_date.month:02d}-01"
        month_end = f"{self.current_date.year}-{self.current_date.month:02d}-31"
        sessions_by_date = defaultdict(int)
        for session in self.app.data.sessions:
            if month_start <= session["date"] <= month_end:
                sessions_by_date[session["date"]] += 1
        return sessions_by_date
    def show_day_details(self, day):
        date_str = f"{self.current_date.year}-{self.current_date.month:02d}-{day:02d}"
        day_sessions = [s for s in self.app.data.sessions if s["date"] == date_str]
        if not day_sessions:
            messagebox.showinfo("No Sessions", f"No sessions recorded for {date_str}")
            return
        details = f"Sessions for {date_str}:\n\n"
        for session in day_sessions:
            details += f"• {session['name']} ({session.get('session_type', '')})\n"
            details += f"  {session['start']} - {session['end']} ({session['duration']:.1f} min)\n\n"
        messagebox.showinfo("Session Details", details)
class AIInsightsPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.predictor = AIPredictor(app.data, getattr(app, 'ai_assistant', None))
        self._build_widgets()
    def _build_widgets(self):
        header = ttk.Frame(self)
        header.pack(fill=tk.X, pady=(0, 20))
        ttk.Label(header, text="🤖 AI Insights", style="Heading.TLabel").pack()
        # Summary cards
        cards = ttk.Frame(self)
        cards.pack(fill=tk.X, padx=20)
        self.card_total = ttk.Label(cards, text="Total Focus (30d): 0h", font=(FONT_FAMILY, FONT_SIZES['medium'], 'bold'))
        self.card_total.pack(side=tk.LEFT, padx=10)
        self.card_pred = ttk.Label(cards, text="Predicted Focus Today: 0", font=(FONT_FAMILY, FONT_SIZES['medium'], 'bold'))
        self.card_pred.pack(side=tk.LEFT, padx=10)
        self.card_tasks = ttk.Label(cards, text="Completed Tasks: 0", font=(FONT_FAMILY, FONT_SIZES['medium'], 'bold'))
        self.card_tasks.pack(side=tk.LEFT, padx=10)
        # Charts
        charts = ttk.Frame(self)
        charts.pack(fill=tk.BOTH, expand=True, padx=20, pady=(10, 0))
        left = ttk.Frame(charts, style="Card.TFrame"); left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,10))
        right = ttk.Frame(charts, style="Card.TFrame"); right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10,0))
        ttk.Label(left, text="Productivity by Hour (last 30d)", font=(FONT_FAMILY, FONT_SIZES['medium'], 'bold')).pack(pady=10)
        self.bar_fig = Figure(figsize=(5,4), dpi=80); self.bar_ax = self.bar_fig.add_subplot(111)
        self.bar_canvas = FigureCanvasTkAgg(self.bar_fig, master=left)
        self.bar_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        ttk.Label(right, text="Daily Trend (last 14d)", font=(FONT_FAMILY, FONT_SIZES['medium'], 'bold')).pack(pady=10)
        self.line_fig2 = Figure(figsize=(5,4), dpi=80); self.line_ax2 = self.line_fig2.add_subplot(111)
        self.line_canvas2 = FigureCanvasTkAgg(self.line_fig2, master=right)
        self.line_canvas2.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        # Recommendations & Motivation
        bottom = ttk.Frame(self, style="Card.TFrame"); bottom.pack(fill=tk.X, padx=20, pady=15)
        inner = ttk.Frame(bottom); inner.pack(fill=tk.X, padx=20, pady=15)
        ttk.Label(inner, text="Smart Recommendations", font=(FONT_FAMILY, FONT_SIZES['medium'], 'bold')).pack(anchor=tk.W)
        self.rec_label = ttk.Label(inner, text="", foreground=COLORS['text_secondary'])
        self.rec_label.pack(anchor=tk.W, pady=(4,8))
        ttk.Label(inner, text="Motivation", font=(FONT_FAMILY, FONT_SIZES['medium'], 'bold')).pack(anchor=tk.W)
        self.motiv_label = ttk.Label(inner, text="", foreground=COLORS['text_secondary'])
        self.motiv_label.pack(anchor=tk.W, pady=(4,0))
    def refresh(self):
        mins30 = self.predictor.total_focus_minutes(30)
        hours = mins30//60; rem = mins30%60
        self.card_total.config(text=f"Total Focus (30d): {hours}h {rem}m")
        pred = self.predictor.predict_focus_today()
        self.card_pred.config(text=f"Predicted Focus Today: {pred}")
        self.card_tasks.config(text=f"Completed Tasks: {self.predictor.completed_tasks_count()}")
        # Bar by hour
        by_hour = self.predictor.productivity_by_hour(30)
        self.bar_ax.clear()
        xs = list(range(24)); ys = [by_hour.get(h,0)/60 for h in xs]
        self.bar_ax.bar(xs, ys)
        self.bar_ax.set_xlabel('Hour'); self.bar_ax.set_ylabel('Hours')
        self.bar_canvas.draw()
        # Line daily trend
        dates, hours_list = self.predictor.daily_trend(14)
        self.line_ax2.clear(); self.line_ax2.plot(range(len(dates)), hours_list, marker='o')
        self.line_ax2.set_xticks(range(0,len(dates), max(1,len(dates)//7)))
        self.line_ax2.set_ylabel('Hours'); self.line_ax2.grid(True, alpha=0.3)
        self.line_canvas2.draw()
        # Recs & motivation
        dur, brk = self.predictor.recommend_session_and_break()
        self.rec_label.config(text=f"Try {dur}-minute focus with a {brk}-minute break. Adjust based on energy.")
        self.motiv_label.config(text=self.predictor.motivation())

class AnalyticsPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build_widgets()
    def _build_widgets(self):
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        ttk.Label(header_frame, text="📈 Advanced Analytics", style="Heading.TLabel").pack()
        controls_card = ttk.Frame(self, style="Card.TFrame")
        controls_card.pack(fill=tk.X, pady=(0, 15), padx=20)
        controls_frame = ttk.Frame(controls_card)
        controls_frame.pack(padx=20, pady=15)
        ttk.Label(controls_frame, text="Time Period:", 
                 font=(FONT_FAMILY, FONT_SIZES['medium'], 'bold')).pack(side=tk.LEFT, padx=(0, 10))
        self.period_var = tk.StringVar(value="Last 30 Days")
        period_combo = ttk.Combobox(controls_frame, textvariable=self.period_var,
                                  values=["Last 7 Days", "Last 30 Days", "Last 90 Days", "This Year"],
                                  state="readonly", width=15)
        period_combo.pack(side=tk.LEFT, padx=(0, 10))
        period_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh())
        ttk.Button(controls_frame, text="🔄 Refresh", command=self.refresh, 
                  style="Secondary.TButton").pack(side=tk.LEFT, padx=10)
        charts_frame = ttk.Frame(self)
        charts_frame.pack(fill=tk.BOTH, expand=True, padx=20)
        left_card = ttk.Frame(charts_frame, style="Card.TFrame")
        left_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        ttk.Label(left_card, text="Session Type Distribution", 
                 font=(FONT_FAMILY, FONT_SIZES['medium'], 'bold')).pack(pady=10)
        self.pie_fig = Figure(figsize=(5, 4), dpi=80)
        self.pie_ax = self.pie_fig.add_subplot(111)
        self.pie_canvas = FigureCanvasTkAgg(self.pie_fig, master=left_card)
        self.pie_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        right_card = ttk.Frame(charts_frame, style="Card.TFrame")
        right_card.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        ttk.Label(right_card, text="Daily Productivity Trend", 
                 font=(FONT_FAMILY, FONT_SIZES['medium'], 'bold')).pack(pady=10)
        self.line_fig = Figure(figsize=(5, 4), dpi=80)
        self.line_ax = self.line_fig.add_subplot(111)
        self.line_canvas = FigureCanvasTkAgg(self.line_fig, master=right_card)
        self.line_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        stats_card = ttk.Frame(self, style="Card.TFrame")
        stats_card.pack(fill=tk.X, pady=(15, 0), padx=20)
        ttk.Label(stats_card, text="📊 Statistics Summary", 
                 font=(FONT_FAMILY, FONT_SIZES['medium'], 'bold')).pack(pady=10)
        self.stats_frame = ttk.Frame(stats_card)
        self.stats_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
        self.total_sessions_label = ttk.Label(self.stats_frame, text="Total Sessions: 0")
        self.total_sessions_label.pack(side=tk.LEFT, padx=10)
        self.total_time_label = ttk.Label(self.stats_frame, text="Total Time: 0h 0m")
        self.total_time_label.pack(side=tk.LEFT, padx=10)
        self.avg_session_label = ttk.Label(self.stats_frame, text="Avg Session: 0m")
        self.avg_session_label.pack(side=tk.LEFT, padx=10)
        self.most_productive_label = ttk.Label(self.stats_frame, text="Most Productive Day: N/A")
        self.most_productive_label.pack(side=tk.LEFT, padx=10)
    def refresh(self):
        period = self.period_var.get()
        sessions = self._get_sessions_for_period(period)
        if not sessions:
            self._show_empty_charts()
            self._update_stats([])
            return
        self._update_pie_chart(sessions)
        self._update_line_chart(sessions)
        self._update_stats(sessions)
    def _get_sessions_for_period(self, period):
        """Get sessions for the selected time period"""
        today = datetime.now().date()
        if period == "Last 7 Days":
            start_date = today - timedelta(days=7)
        elif period == "Last 30 Days":
            start_date = today - timedelta(days=30)
        elif period == "Last 90 Days":
            start_date = today - timedelta(days=90)
        elif period == "This Year":
            start_date = date(today.year, 1, 1)
        else:
            start_date = today - timedelta(days=30)
        start_date_str = start_date.strftime("%Y-%m-%d")
        return [s for s in self.app.data.sessions if s["date"] >= start_date_str]
    def _update_pie_chart(self, sessions):
        self.pie_ax.clear()
        type_time = defaultdict(float)
        for s in sessions:
            session_type = s.get("session_type", "Unknown")
            type_time[session_type] += s.get("duration", 0)
        if type_time:
            labels = list(type_time.keys())
            sizes = list(type_time.values())
            cmap = cm.get_cmap("Set3", len(labels))
            colors = [cmap(i) for i in range(len(labels))]
            self.pie_ax.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
            self.pie_ax.set_title(f"Time Distribution ({self.period_var.get()})")
        self.pie_canvas.draw()
    def _update_line_chart(self, sessions):
        self.line_ax.clear()
        daily_time = defaultdict(float)
        for s in sessions:
            daily_time[s["date"]] += s.get("duration", 0) / 60  # Convert to hours
        if daily_time:
            dates = sorted(daily_time.keys())
            times = [daily_time[d] for d in dates]
            date_objects = np.array([datetime.strptime(d, "%Y-%m-%d") for d in dates])
            self.line_ax.plot(date_objects, times, marker='o', linewidth=2, markersize=4)
            self.line_ax.set_title(f"Daily Productivity ({self.period_var.get()})")
            self.line_ax.set_ylabel("Hours")
            self.line_ax.tick_params(axis='x', rotation=45)
            self.line_ax.grid(True, alpha=0.3)
            self.line_fig.autofmt_xdate()
        self.line_canvas.draw()
    def _show_empty_charts(self):
        self.pie_ax.clear()
        self.pie_ax.text(0.5, 0.5, 'No data available', horizontalalignment='center',
                        verticalalignment='center', transform=self.pie_ax.transAxes,
                        fontsize=14, color='gray')
        self.pie_canvas.draw()
        self.line_ax.clear()
        self.line_ax.text(0.5, 0.5, 'No data available', horizontalalignment='center',
                         verticalalignment='center', transform=self.line_ax.transAxes,
                         fontsize=14, color='gray')
        self.line_canvas.draw()
    def _update_stats(self, sessions):
        if not sessions:
            self.total_sessions_label.config(text="Total Sessions: 0")
            self.total_time_label.config(text="Total Time: 0h 0m")
            self.avg_session_label.config(text="Avg Session: 0m")
            self.most_productive_label.config(text="Most Productive Day: N/A")
            return
        total_sessions = len(sessions)
        total_minutes = sum(s.get("duration", 0) for s in sessions)
        total_hours = int(total_minutes // 60)
        remaining_minutes = int(total_minutes % 60)
        avg_session = int(total_minutes / total_sessions) if total_sessions > 0 else 0
        daily_time = defaultdict(float)
        for s in sessions:
            daily_time[s["date"]] += s.get("duration", 0)
        most_productive_day = "N/A"
        if daily_time:
            best_date = max(daily_time.keys(), key=lambda d: daily_time[d])
            most_productive_day = f"{best_date} ({int(daily_time[best_date])}m)"
        self.total_sessions_label.config(text=f"Total Sessions: {total_sessions}")
        self.total_time_label.config(text=f"Total Time: {total_hours}h {remaining_minutes}m")
        self.avg_session_label.config(text=f"Avg Session: {avg_session}m")
        self.most_productive_label.config(text=f"Most Productive Day: {most_productive_day}")
class AchievementsPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build_widgets()
    def _build_widgets(self):
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        ttk.Label(header_frame, text="🎖️ Achievements & Rewards", style="Heading.TLabel").pack()
        profile_card = ttk.Frame(self, style="Card.TFrame")
        profile_card.pack(fill=tk.X, pady=(0, 15), padx=20)
        profile_frame = ttk.Frame(profile_card)
        profile_frame.pack(padx=20, pady=15, fill=tk.X)
        level_frame = ttk.Frame(profile_frame)
        level_frame.pack(fill=tk.X, pady=(0, 10))
        self.username_var = tk.StringVar()
        ttk.Label(level_frame, textvariable=self.username_var,
                 font=(FONT_FAMILY, FONT_SIZES['large'], 'bold')).pack(anchor=tk.W)
        self.level_var = tk.StringVar()
        ttk.Label(level_frame, textvariable=self.level_var,
                 font=(FONT_FAMILY, FONT_SIZES['medium'])).pack(anchor=tk.W)
        progress_frame = ttk.Frame(profile_frame)
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        self.xp_progress_var = tk.DoubleVar()
        self.xp_progress = ttk.Progressbar(progress_frame, variable=self.xp_progress_var, length=300)
        self.xp_progress.pack(fill=tk.X, side=tk.LEFT, expand=True, padx=(0, 10))
        self.xp_label_var = tk.StringVar()
        ttk.Label(progress_frame, textvariable=self.xp_label_var,
                 font=(FONT_FAMILY, FONT_SIZES['small'])).pack(side=tk.RIGHT)
        badges_card = ttk.Frame(self, style="Card.TFrame")
        badges_card.pack(fill=tk.X, pady=(0, 15), padx=20)
        ttk.Label(badges_card, text="🏅 Your Badges",
                 font=(FONT_FAMILY, FONT_SIZES['medium'], 'bold')).pack(pady=10, anchor=tk.W, padx=20)
        self.badges_frame = ttk.Frame(badges_card)
        self.badges_frame.pack(fill=tk.X, pady=(0, 15), padx=20)
        achievements_card = ttk.Frame(self, style="Card.TFrame")
        achievements_card.pack(fill=tk.BOTH, expand=True, pady=(0, 15), padx=20)
        ttk.Label(achievements_card, text="🏆 Achievements",
                 font=(FONT_FAMILY, FONT_SIZES['medium'], 'bold')).pack(pady=10, anchor=tk.W, padx=20)
        self.achievements_notebook = ttk.Notebook(achievements_card)
        self.achievements_notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))
        self.achievement_frames = {}
        for category in ["All", "Sessions", "Time", "Streak", "Quality", "Goals"]:
            frame = ttk.Frame(self.achievements_notebook)
            self.achievements_notebook.add(frame, text=category)
            self.achievement_frames[category.lower()] = frame
    def _display_user_profile(self):
        """Display user profile information"""
        profile = self.app.data.user_profile
        self.username_var.set(profile.get("username", "Productivity Hero"))
        self.level_var.set(f"Level {profile.get('level', 1)}")
        total_xp = profile.get("total_xp", 0)
        current_level = profile.get("level", 1)
        next_level_xp = current_level * 100
        prev_level_xp = (current_level - 1) * 100
        xp_range = next_level_xp - prev_level_xp
        if xp_range > 0:
            level_progress = (total_xp - prev_level_xp) / xp_range * 100
        else:
            level_progress = 0
        self.xp_progress_var.set(level_progress)
        self.xp_label_var.set(f"XP: {total_xp} / {next_level_xp} ({int(level_progress)}%)")
    def _display_badges(self):
        """Display earned badges"""
        for widget in self.badges_frame.winfo_children():
            widget.destroy()
        badges = self.app.data.user_profile.get("badges_earned", [])
        if not badges:
            ttk.Label(self.badges_frame, text="No badges earned yet. Complete achievements to earn badges!",
                     font=(FONT_FAMILY, FONT_SIZES['normal']),
                     foreground=COLORS['text_secondary']).pack(pady=20)
            return
        for i, badge in enumerate(badges):
            badge_frame = ttk.Frame(self.badges_frame)
            badge_frame.grid(row=i//3, column=i%3, padx=10, pady=10)
            ttk.Label(badge_frame, text=badge,
                     font=(FONT_FAMILY, FONT_SIZES['large'])).pack(pady=5)
    def _display_achievements(self):
        """Display achievements in categorized tabs"""
        for frame in self.achievement_frames.values():
            for widget in frame.winfo_children():
                widget.destroy()
        all_achievements = self.app.data.achievements
        achievements_by_category = {}
        for achievement in all_achievements:
            category = achievement.get("category", "other").lower()
            if category not in achievements_by_category:
                achievements_by_category[category] = []
            achievements_by_category[category].append(achievement)
        self._populate_achievement_list(self.achievement_frames["all"], all_achievements)
        for category, frame_key in {
            "sessions": "sessions",
            "time": "time",
            "streak": "streak",
            "quality": "quality",
            "goals": "goals"
        }.items():
            if category in achievements_by_category and frame_key in self.achievement_frames:
                self._populate_achievement_list(
                    self.achievement_frames[frame_key],
                    achievements_by_category[category]
                )
    def _populate_achievement_list(self, parent_frame, achievements):
        """Populate a frame with achievement cards"""
        if not achievements:
            ttk.Label(parent_frame, text="No achievements in this category",
                     font=(FONT_FAMILY, FONT_SIZES['normal']),
                     foreground=COLORS['text_secondary']).pack(pady=50)
            return
        canvas = tk.Canvas(parent_frame, borderwidth=0, highlightthickness=0,
                         background=COLORS['background'])
        scrollbar = ttk.Scrollbar(parent_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        sorted_achievements = sorted(
            achievements,
            key=lambda a: (not a.get("unlocked", False), a.get("name", ""))
        )
        for achievement in sorted_achievements:
            self._create_achievement_card(scrollable_frame, achievement)
    def _create_achievement_card(self, parent, achievement):
        """Create a card displaying achievement details"""
        is_unlocked = achievement.get("unlocked", False)
        card = ttk.Frame(parent, style="Card.TFrame")
        card.pack(fill=tk.X, pady=5, padx=5)
        header_frame = ttk.Frame(card)
        header_frame.pack(fill=tk.X, padx=10, pady=5)
        icon_label = ttk.Label(header_frame, text=achievement.get("icon", "🏆"),
                             font=(FONT_FAMILY, FONT_SIZES['large']))
        icon_label.pack(side=tk.LEFT, padx=(0, 10))
        name_label = ttk.Label(header_frame, text=achievement.get("name", "Achievement"),
                              font=(FONT_FAMILY, FONT_SIZES['medium'], 'bold'))
        name_label.pack(side=tk.LEFT)
        if is_unlocked:
            unlock_date = achievement.get("unlock_date", "")
            unlock_text = f"✅ Unlocked" + (f" on {unlock_date}" if unlock_date else "")
            ttk.Label(header_frame, text=unlock_text,
                     foreground=COLORS['success'],
                     font=(FONT_FAMILY, FONT_SIZES['small'])).pack(side=tk.RIGHT)
        desc_frame = ttk.Frame(card)
        desc_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(desc_frame, text=achievement.get("description", ""),
                 wraplength=400,
                 foreground=COLORS['text_secondary']).pack(anchor=tk.W)
        reward_frame = ttk.Frame(card)
        reward_frame.pack(fill=tk.X, padx=10, pady=5)
        xp_reward = achievement.get("xp_reward", 0)
        badge = achievement.get("badge", "")
        if xp_reward > 0:
            ttk.Label(reward_frame, text=f"🌟 {xp_reward} XP",
                     font=(FONT_FAMILY, FONT_SIZES['small'])).pack(side=tk.LEFT, padx=(0, 10))
        if badge:
            ttk.Label(reward_frame, text=f"🏅 {badge}",
                     font=(FONT_FAMILY, FONT_SIZES['small'])).pack(side=tk.LEFT)
        if not is_unlocked:
            progress_frame = ttk.Frame(card)
            progress_frame.pack(fill=tk.X, padx=10, pady=(5, 10))
            requirement = achievement.get("requirement", 100)
            current_value = 0
            category = achievement.get("category", "").lower()
            if category == "sessions":
                current_value = self.app.data.user_profile["stats"]["total_sessions"]
            elif category == "time":
                current_value = self.app.data.user_profile["stats"]["total_minutes"]
            elif category == "streak":
                current_value = calculate_streak(self.app.data.sessions)
            elif category == "quality":
                current_value = self.app.data.user_profile["stats"]["perfect_sessions"]
            elif category == "goals":
                current_value = len([g for g in self.app.data.goals if g.get("completed", False)])
            progress_pct = min(100, (current_value / requirement) * 100) if requirement > 0 else 0
            progress_var = tk.DoubleVar(value=progress_pct)
            progress_bar = ttk.Progressbar(progress_frame, variable=progress_var, length=300)
            progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
            progress_text = f"{current_value}/{requirement} ({int(progress_pct)}%)"
            ttk.Label(progress_frame, text=progress_text,
                     font=(FONT_FAMILY, FONT_SIZES['small'])).pack(side=tk.RIGHT)
    def refresh(self):
        """Refresh all achievement data"""
        newly_unlocked = self.app.data.check_and_unlock_achievements()
        for achievement_info in newly_unlocked:
            achievement = achievement_info["achievement"]
            level_up = achievement_info["level_up"]
            xp_gained = achievement_info["xp_gained"]
            message = f"🎉 Achievement Unlocked: {achievement['name']}\n\n"
            message += f"{achievement['description']}\n\n"
            message += f"Reward: {xp_gained} XP"
            if level_up:
                message += f"\n🌟 LEVEL UP! You are now Level {self.app.data.user_profile['level']}"
            if achievement["badge"]:
                message += f"\n🏅 New Badge: {achievement['badge']}"
            messagebox.showinfo("Achievement Unlocked!", message)
        self._display_user_profile()
        self._display_badges()
        self._display_achievements()
        self.app.data.save_all()
class GoalsPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build_widgets()
        if not hasattr(self.app.data, 'goals'):
            self.app.data.goals = []
            self._create_default_goals()
    def _create_default_goals(self):
        """Create some default goals for new users"""
        defaults = [("daily_25min", "Daily Focus", "Complete at least 25 minutes of focused work daily", "daily", 25, "minutes"), ("weekly_500min", "Weekly Target", "Accumulate 500 minutes of productive work this week", "weekly", 500, "minutes"), ("streak_7days", "7-Day Streak", "Work at least 15 minutes for 7 consecutive days", "streak", 7, "days")]
        self.app.data.goals.extend([{"id": id, "name": name, "description": desc, "type": type, "target": target, "current": 0, "unit": unit, "created_date": datetime.now().strftime("%Y-%m-%d"), "completed": False} for id, name, desc, type, target, unit in defaults])
        self.app.data.save_all()
    def _build_widgets(self):
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        ttk.Label(header_frame, text="🏆 Goals & Achievements", style="Heading.TLabel").pack()
        controls_card = ttk.Frame(self, style="Card.TFrame")
        controls_card.pack(fill=tk.X, pady=(0, 15), padx=20)
        controls_frame = ttk.Frame(controls_card)
        controls_frame.pack(padx=20, pady=15)
        ttk.Button(controls_frame, text="➕ Add Goal", command=self.add_goal, 
                  style="Modern.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="🔄 Refresh Progress", command=self.refresh, 
                  style="Secondary.TButton").pack(side=tk.LEFT, padx=5)
        self.goals_frame = ttk.Frame(self)
        self.goals_frame.pack(fill=tk.BOTH, expand=True, padx=20)
        achievements_card = ttk.Frame(self, style="Card.TFrame")
        achievements_card.pack(fill=tk.X, pady=(15, 0), padx=20)
        ttk.Label(achievements_card, text="🎉 Recent Achievements", 
                 font=(FONT_FAMILY, FONT_SIZES['medium'], 'bold')).pack(pady=10)
        self.achievements_listbox = tk.Listbox(achievements_card, height=4,
                                             font=(FONT_FAMILY, FONT_SIZES['normal']),
                                             bg=COLORS['surface'],
                                             fg=COLORS['text_primary'],
                                             selectbackground=COLORS['primary'],
                                             selectforeground='white',
                                             borderwidth=0)
        self.achievements_listbox.pack(fill=tk.X, padx=20, pady=(0, 15))
    def refresh(self):
        if not hasattr(self.app.data, 'goals'):
            self.app.data.goals = []
            self._create_default_goals()
        self._update_goal_progress()
        self._display_goals()
        self._display_achievements()
    def _update_goal_progress(self):
        """Update progress for all goals based on current session data"""
        today = datetime.now().strftime("%Y-%m-%d")
        week_start = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime("%Y-%m-%d")
        for goal in self.app.data.goals:
            if goal["completed"]:
                continue
            if goal["type"] == "daily":
                daily_minutes = sum(s["duration"] for s in self.app.data.sessions if s["date"] == today)
                goal["current"] = int(daily_minutes)
            elif goal["type"] == "weekly":
                weekly_minutes = sum(s["duration"] for s in self.app.data.sessions 
                                   if s["date"] >= week_start)
                goal["current"] = int(weekly_minutes)
            elif goal["type"] == "streak":
                streak = calculate_streak(self.app.data.sessions)
                goal["current"] = streak
            if goal["current"] >= goal["target"] and not goal["completed"]:
                goal["completed"] = True
                goal["completed_date"] = today
                messagebox.showinfo("🎉 Goal Achieved!", 
                                   f"Congratulations! You've completed: {goal['name']}")
        self.app.data.save_all()
    def _display_goals(self):
        for widget in self.goals_frame.winfo_children():
            widget.destroy()
        if not self.app.data.goals:
            ttk.Label(self.goals_frame, text="No goals set yet. Click 'Add Goal' to get started!",
                     font=(FONT_FAMILY, FONT_SIZES['medium']), 
                     foreground=COLORS['text_secondary']).pack(pady=50)
            return
        for i, goal in enumerate(self.app.data.goals):
            self._create_goal_widget(goal, i)
    def _create_goal_widget(self, goal, index):
        goal_card = ttk.Frame(self.goals_frame, style="Card.TFrame")
        goal_card.pack(fill=tk.X, pady=(0, 10))
        header_frame = ttk.Frame(goal_card)
        header_frame.pack(fill=tk.X, padx=15, pady=10)
        status_icon = "✅" if goal["completed"] else "🎯"
        ttk.Label(header_frame, text=f"{status_icon} {goal['name']}", 
                 font=(FONT_FAMILY, FONT_SIZES['medium'], 'bold')).pack(side=tk.LEFT)
        if not goal["completed"]:
            ttk.Button(header_frame, text="❌", width=3,
                      command=lambda idx=index: self.delete_goal(idx)).pack(side=tk.RIGHT)
        ttk.Label(goal_card, text=goal["description"], 
                 font=(FONT_FAMILY, FONT_SIZES['normal']),
                 foreground=COLORS['text_secondary']).pack(anchor=tk.W, padx=15)
        progress_frame = ttk.Frame(goal_card)
        progress_frame.pack(fill=tk.X, padx=15, pady=10)
        progress = min(goal["current"] / goal["target"] * 100, 100) if goal["target"] > 0 else 0
        progress_var = tk.DoubleVar(value=progress)
        progress_bar = ttk.Progressbar(progress_frame, variable=progress_var, length=300)
        progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        progress_text = f"{goal['current']}/{goal['target']} {goal['unit']} ({progress:.1f}%)"
        ttk.Label(progress_frame, text=progress_text, 
                 font=(FONT_FAMILY, FONT_SIZES['small'])).pack(side=tk.RIGHT)
        if goal["completed"] and "completed_date" in goal:
            ttk.Label(goal_card, text=f"✨ Completed on {goal['completed_date']}", 
                     font=(FONT_FAMILY, FONT_SIZES['small']),
                     foreground=COLORS['success']).pack(anchor=tk.W, padx=15, pady=(0, 10))
        else:
            ttk.Frame(goal_card, height=10).pack()  # Spacing
    def _display_achievements(self):
        self.achievements_listbox.delete(0, tk.END)
        completed_goals = [g for g in self.app.data.goals if g["completed"]]
        if not completed_goals:
            self.achievements_listbox.insert(tk.END, "No achievements yet - keep working towards your goals!")
            return
        completed_goals.sort(key=lambda g: g.get("completed_date", ""), reverse=True)
        for goal in completed_goals[-10:]:  # Show last 10 achievements
            achievement_text = f"✅ {goal['name']} - Completed on {goal.get('completed_date', 'N/A')}"
            self.achievements_listbox.insert(tk.END, achievement_text)
    def add_goal(self):
        """Open dialog to add a new goal"""
        GoalDialog(self, self.app, self.refresh)
    def delete_goal(self, index):
        if messagebox.askyesno("Delete Goal", "Are you sure you want to delete this goal?"):
            del self.app.data.goals[index]
            self.app.data.save_all()
            self.refresh()
class GoalDialog(ThemedDialog):
    def __init__(self, parent, app, refresh_callback):
        super().__init__(parent)
        self.app = app
        self.refresh_callback = refresh_callback
        self.title("Add New Goal")
        self.geometry("420x380")
        self.resizable(False, False)
        self.grab_set()
        self._build_widgets()
    def _build_widgets(self):
        ttk.Label(self, text="🎯 Create New Goal", font=(FONT_FAMILY, FONT_SIZES['large'], 'bold')).pack(pady=15)
        self.name_var = tk.StringVar(value="")
        self.desc_var = tk.StringVar(value="")
        ttk.Label(self, text="Goal Name:").pack(anchor=tk.W, padx=20, pady=(10, 5))
        ttk.Entry(self, textvariable=self.name_var, width=50).pack(padx=20, fill=tk.X)
        ttk.Label(self, text="Description:").pack(anchor=tk.W, padx=20, pady=(10, 5))
        ttk.Entry(self, textvariable=self.desc_var, width=50).pack(padx=20, fill=tk.X)
        ttk.Label(self, text="Goal Type:").pack(anchor=tk.W, padx=20, pady=(10, 5))
        self.type_var = tk.StringVar(value="daily")
        type_frame = ttk.Frame(self)
        type_frame.pack(padx=20, fill=tk.X)
        ttk.Radiobutton(type_frame, text="Daily", variable=self.type_var, value="daily").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(type_frame, text="Weekly", variable=self.type_var, value="weekly").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(type_frame, text="Streak", variable=self.type_var, value="streak").pack(side=tk.LEFT)
        # Target Time selector (minutes)
        ttk.Label(self, text="Target Time (minutes):").pack(anchor=tk.W, padx=20, pady=(12, 5))
        self.target_var = tk.IntVar(value=30)
        time_row = ttk.Frame(self)
        time_row.pack(fill=tk.X, padx=20)
        tk.Spinbox(time_row, from_=5, to=600, increment=5, textvariable=self.target_var, width=8).pack(side=tk.LEFT)
        # Quick presets
        for v in (30, 60, 90):
            ttk.Button(time_row, text=f"{v}", command=lambda m=v: self.target_var.set(m)).pack(side=tk.LEFT, padx=4)
        ttk.Label(self, text="(Set how many minutes you want to focus)", foreground=COLORS['text_secondary']).pack(anchor=tk.W, padx=20, pady=(4, 0))
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=20)
        submit_btn = ttk.Button(button_frame, text="Submit", command=self.save_goal, style="Modern.TButton")
        submit_btn.pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.destroy).pack(side=tk.LEFT, padx=5)
        # Enter to submit
        self.bind('<Return>', lambda e: self.save_goal())
    def save_goal(self):
        name = self.name_var.get().strip()
        description = self.desc_var.get().strip()
        goal_type = self.type_var.get()
        try:
            target_minutes = int(self.target_var.get())
        except Exception:
            messagebox.showerror("Error", "Please enter a valid number of minutes.")
            return
        if not name:
            messagebox.showerror("Error", "Please enter a goal name.")
            return
        if target_minutes <= 0:
            messagebox.showerror("Error", "Target time must be greater than 0.")
            return
        new_goal = {
            "id": f"{goal_type}_{len(self.app.data.goals)}_{int(time.time())}",
            "name": name,
            "description": description or f"Achieve {target_minutes} minutes ({goal_type})",
            "type": goal_type,
            "target": target_minutes,
            "current": 0,
            "unit": "minutes",
            "created_date": datetime.now().strftime("%Y-%m-%d"),
            "completed": False
        }
        self.app.data.goals.append(new_goal)
        self.app.data.save_all()
        messagebox.showinfo("Success", f"Goal '{name}' created successfully!")
        self.refresh_callback()
        self.destroy()
class AboutPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        ttk.Label(self, text="SessionSlice", font=("Segoe UI", 22, "bold")).pack(pady=20)
        ttk.Label(self, text="A powerful and modern personal productivity tracker.\n"
                            "Made with Python and Tkinter.\n\n"
                            "Features:\n"
                            "- Task and session management\n"
                            "- Time tracking with breaks/interruptions\n"
                            "- Calendar view with session history\n"
                            "- Advanced analytics and charts\n"
                            "- Goal setting and achievement tracking\n"
                            "- Detailed reports with charts\n\n"
                            "Enjoy using SessionSlice!", font=("Segoe UI", 11), justify=tk.CENTER).pack(pady=12)
class AIPredictor:
    """Lightweight AI-style predictor and recommender based on usage data.
    Uses heuristics; if OpenAI is enabled, can augment messages."""
    def __init__(self, data, ai_assistant=None):
        self.data = data
        self.ai = ai_assistant
    def _sessions_last_days(self, days=30):
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        return [s for s in self.data.sessions if s.get('date','') >= cutoff]
    def total_focus_minutes(self, days=30):
        return int(sum(s.get('duration',0) for s in self._sessions_last_days(days)))
    def productivity_by_hour(self, days=30):
        by_hour = defaultdict(float)
        for s in self._sessions_last_days(days):
            start = s.get('start') or '00:00'
            try:
                h = int(start.split(':')[0])
            except Exception:
                h = 0
            by_hour[h] += s.get('duration',0)
        return by_hour
    def daily_trend(self, days=14):
        by_day = defaultdict(float)
        for s in self._sessions_last_days(days):
            by_day[s.get('date','')] += s.get('duration',0)
        dates = [(datetime.now()-timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days-1,-1,-1)]
        return dates, [by_day.get(d,0)/60 for d in dates]  # hours
    def completed_tasks_count(self):
        return len([t for t in self.data.tasks if t.get('completed')])
    def predict_focus_today(self):
        today = datetime.now().strftime('%Y-%m-%d')
        mins_today = sum(s.get('duration',0) for s in self.data.sessions if s.get('date')==today)
        avg_last7 = (self.total_focus_minutes(7)/7) if self._sessions_last_days(7) else 0
        tasks_done = len([t for t in self.data.tasks if t.get('completed')])
        score = 50
        score += min(30, mins_today/3)  # up to +30
        score += min(15, avg_last7/10)  # up to +15
        score += min(5, tasks_done)
        return int(max(0,min(100,score)))
    def recommend_session_and_break(self):
        last = self._sessions_last_days(14)
        if last:
            avg = sum(s.get('duration',0) for s in last)/len(last)
        else:
            avg = 25
        if avg < 20:
            duration = 20; brk = 5
        elif avg < 35:
            duration = 25; brk = 5
        elif avg < 60:
            duration = 45; brk = 10
        else:
            duration = 60; brk = 10
        return duration, brk
    def motivation(self):
        base = [
            "Believe in small wins — they compound into big results.",
            "Your focus today builds your tomorrow.",
            "One deep breath, one clear intention, one session. Let's go!",
            "Done is better than perfect — start now.",
            "You’re closer than you think. Keep going." 
        ]
        msg = random.choice(base)
        if self.ai and getattr(self.ai,'enabled',False):
            try:
                prompt = f"User stats: total_minutes_7={self.total_focus_minutes(7)}, completed_tasks={self.completed_tasks_count()}\n"
                prompt += "Write a 1-sentence motivational line, friendly, 15 words max."
                reply = self.ai.generate([], prompt)
                if reply:
                    msg = reply.strip()
            except Exception:
                pass
        return msg

class ChatPage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.chatbot = app.chatbot
        self.tts_enabled = tk.BooleanVar(value=TTS_AVAILABLE)
        self._tts_engine = None
        self._listening = False
        self._audio_stream = None
        self._audio_frames = []
        self._audio_samplerate = 16000
        self._build_widgets()
        self._add_bot_message(self.chatbot.get_greeting())
    def _build_widgets(self):
        ttk.Label(self, text="💬 Productivity Buddy", style="Heading.TLabel").pack(pady=(0, 10))
        chat_card = ttk.Frame(self, style="Card.TFrame")
        chat_card.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        inner = ttk.Frame(chat_card)
        inner.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.chat_display = scrolledtext.ScrolledText(
            inner, wrap=tk.WORD,
            font=(FONT_FAMILY, FONT_SIZES['normal']),
            bg=COLORS['surface'], fg=COLORS['text_primary'],
            relief='flat', state='disabled', height=18
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        quick = ttk.Frame(inner)
        quick.pack(fill=tk.X, pady=(8, 0))
        for text, preset in [("📊 Stats","today"),("💡 Tip","tip"),("💪 Motivate","motivate")]:
            ttk.Button(quick, text=text, command=lambda p=preset: self._send_message(p), style="Secondary.TButton").pack(side=tk.LEFT, padx=3)
        input_bar = ttk.Frame(inner)
        input_bar.pack(fill=tk.X, pady=(8, 0))
        self.message_var = tk.StringVar()
        entry = ttk.Entry(input_bar, textvariable=self.message_var)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        entry.bind('<Return>', lambda e: self._send_message())
        ttk.Button(input_bar, text="Send", command=self._send_message, style="Modern.TButton").pack(side=tk.RIGHT, padx=(8,0))
        voice = ttk.Frame(inner)
        voice.pack(fill=tk.X, pady=(8, 0))
        self.speak_btn = ttk.Button(voice, text="🎤 Speak", command=self._toggle_listen, style="Secondary.TButton")
        self.speak_btn.pack(side=tk.LEFT)
        tk.Checkbutton(voice, text="🔊 Speak replies", variable=self.tts_enabled, bg=COLORS['surface']).pack(side=tk.RIGHT)
    def _add_bot_message(self, message):
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, "🤖 Bot: ", 'bot')
        self.chat_display.insert(tk.END, f"{message}\n\n")
        self.chat_display.tag_config('bot', foreground=COLORS['primary'], font=(FONT_FAMILY, FONT_SIZES['normal'], 'bold'))
        self.chat_display.see(tk.END)
        self.chat_display.config(state='disabled')
        if self.tts_enabled.get() and TTS_AVAILABLE:
            threading.Thread(target=self._speak, args=(message,), daemon=True).start()
    def _add_user_message(self, message):
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, "You: ", 'user')
        self.chat_display.insert(tk.END, f"{message}\n\n")
        self.chat_display.tag_config('user', foreground=COLORS['secondary'], font=(FONT_FAMILY, FONT_SIZES['normal'], 'bold'))
        self.chat_display.see(tk.END)
        self.chat_display.config(state='disabled')
    def _send_message(self, preset_message=None):
        user_message = preset_message if preset_message else self.message_var.get().strip()
        if not user_message:
            return
        self.message_var.set("")
        self._add_user_message(user_message)
        if getattr(self.chatbot, 'ai', None) and getattr(self.chatbot.ai, 'enabled', False):
            self._add_bot_message("🧠 Thinking...")
            def worker():
                try:
                    reply = self.chatbot.get_ai_response(user_message)
                except Exception:
                    reply = self.chatbot.get_response(user_message)
                self.after(0, lambda: self._add_bot_message(reply))
            threading.Thread(target=worker, daemon=True).start()
        else:
            reply = self.chatbot.get_response(user_message)
            self.after(300, lambda: self._add_bot_message(reply))
    def _ensure_tts(self):
        if not TTS_AVAILABLE:
            return None
        if self._tts_engine is None:
            try:
                self._tts_engine = pyttsx3.init()
                rate = self._tts_engine.getProperty('rate')
                self._tts_engine.setProperty('rate', int(rate * 0.95))
            except Exception:
                self._tts_engine = None
        return self._tts_engine
    def _speak(self, text):
        eng = self._ensure_tts()
        if not eng:
            return
        try:
            eng.say(text); eng.runAndWait()
        except Exception:
            pass
    def _toggle_listen(self):
        if getattr(self, '_listening', False):
            self._stop_listening()
        else:
            self._start_listening()
    def _start_listening(self):
        if not AUDIO_AVAILABLE:
            self._add_bot_message("Microphone not available on this system.")
            return
        self._listening = True
        self._audio_frames = []
        self.speak_btn.config(text="⏹ Stop")
        self._add_bot_message("Listening...")
        def callback(indata, frames, time_info, status):
            self._audio_frames.append(indata.copy())
        try:
            self._audio_stream = sd.InputStream(samplerate=self._audio_samplerate, channels=1, callback=callback)
            self._audio_stream.start()
        except Exception as e:
            self._listening = False
            self.speak_btn.config(text="🎤 Speak")
            self._add_bot_message(f"Audio error: {e}")
    def _stop_listening(self):
        if not getattr(self, '_listening', False):
            return
        self._listening = False
        try:
            if self._audio_stream:
                self._audio_stream.stop(); self._audio_stream.close()
        finally:
            self._audio_stream = None
        self.speak_btn.config(text="🎤 Speak")
        if not self._audio_frames:
            return
        try:
            import numpy as _np
            data = _np.concatenate(self._audio_frames, axis=0)
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.wav'); tmp_path = tmp.name; tmp.close()
            sf.write(tmp_path, data, self._audio_samplerate)
        except Exception as e:
            self._add_bot_message(f"Recording error: {e}"); return
        def worker(path=tmp_path):
            try:
                text = self._transcribe_file(path)
                if text:
                    self.after(0, lambda t=text: self._send_message(t))
                else:
                    self.after(0, lambda: self._add_bot_message("Sorry, I couldn't hear anything."))
            finally:
                try: os.remove(path)
                except Exception: pass
        threading.Thread(target=worker, daemon=True).start()
    def _transcribe_file(self, filepath):
        try:
            if getattr(self.chatbot, 'ai', None) and getattr(self.chatbot.ai, 'enabled', False):
                client = self.chatbot.ai.client
                try:
                    resp = client.audio.transcriptions.create(model=os.getenv('OPENAI_STT_MODEL','gpt-4o-transcribe'), file=open(filepath,'rb'))
                except Exception:
                    resp = client.audio.transcriptions.create(model='whisper-1', file=open(filepath,'rb'))
                text = getattr(resp, 'text', None) or (resp.get('text') if isinstance(resp, dict) else None)
                return (text or '').strip()
        except Exception:
            pass
        if SR_AVAILABLE:
            try:
                import speech_recognition as _sr
                r = _sr.Recognizer()
                with _sr.AudioFile(filepath) as s:
                    audio = r.record(s)
                return r.recognize_google(audio)
            except Exception:
                return ""
        return ""
# Optional AI assistant integration (OpenAI)
try:
    from openai import OpenAI
    _OPENAI_SDK_AVAILABLE = True
except Exception:
    _OPENAI_SDK_AVAILABLE = False

class AIAssistant:
    def __init__(self):
        self.enabled = False
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.system_prompt = (
            "You are SessionSlice's friendly productivity assistant. "
            "Be concise, warm, and practical. Offer advice, tips, and encouragement tailored to productivity."
        )
        if _OPENAI_SDK_AVAILABLE and os.getenv("OPENAI_API_KEY"):
            try:
                self.client = OpenAI()
                self.enabled = True
            except Exception:
                self.client = None
                self.enabled = False
        else:
            self.client = None

    def generate(self, history, user_message):
        if not self.enabled or not self.client:
            raise RuntimeError("AI assistant not enabled")
        messages = [{"role": "system", "content": self.system_prompt}]
        trimmed = history[-20:] if history else []
        for m in trimmed:
            if isinstance(m, dict) and "role" in m and "content" in m:
                messages.append(m)
        messages.append({"role": "user", "content": user_message})
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=300,
        )
        return resp.choices[0].message.content.strip()

class ProductivityChatbot:
    """Friendly productivity chatbot companion"""
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

    def get_greeting(self):
        return random.choice(self.greetings)

    def get_encouragement(self):
        return random.choice(self.encouragements)

    def get_break_reminder(self):
        return random.choice(self.break_reminders)

    def get_tip(self):
        return random.choice(self.tips)

    def get_response(self, user_message):
        """Generate response based on user message"""
        message = user_message.lower().strip()
        
        # Greetings
        if any(word in message for word in ['hi', 'hello', 'hey', 'sup']):
            return self.get_greeting()
        
        # Session stats
        elif any(word in message for word in ['today', 'stats', 'progress', 'how am i']):
            return self.get_today_summary()
        
        # Motivation
        elif any(word in message for word in ['motivate', 'encourage', 'inspire']):
            return self.get_encouragement()
        
        # Break reminder
        elif any(word in message for word in ['break', 'rest', 'tired']):
            return self.get_break_reminder()
        
        # Tips
        elif any(word in message for word in ['tip', 'help', 'advice', 'how']):
            return self.get_tip()
        
        # Start session
        elif any(word in message for word in ['start', 'begin', 'focus']):
            return "Let's do this! Head to the dashboard and hit that Start button! 🚀 You got this!"
        
        # Distraction help
        elif any(word in message for word in ['distract', 'focus', 'concentrate']):
            return "I feel you! Try this: close unnecessary tabs, put phone away, and take 3 deep breaths. Then dive in! 🎯"
        
        # Default friendly responses
        else:
            responses = [
                "I'm here for you! Want a productivity tip or should we check your stats? 😊",
                "Not sure what you mean, but I'm vibing with the energy! Want to start a focus session? 💪",
                "Tell me more! Or ask me about tips, stats, or motivation! 🌟",
                "I'm your productivity buddy! Ask me anything about staying focused! 🎯"
            ]
            return random.choice(responses)

    def get_ai_response(self, user_message):
        if self.ai and getattr(self.ai, 'enabled', False):
            try:
                reply = self.ai.generate(self.history, user_message)
                self.history.append({"role": "user", "content": user_message})
                self.history.append({"role": "assistant", "content": reply})
                if len(self.history) > 40:
                    self.history = self.history[-40:]
                return reply
            except Exception:
                return self.get_response(user_message)
        else:
            return self.get_response(user_message)

    def get_today_summary(self):
        """Get summary of today's sessions"""
        today = datetime.now().strftime("%Y-%m-%d")
        today_sessions = [s for s in self.app.data.sessions if s["date"] == today]
        
        if not today_sessions:
            return "No sessions yet today! But hey, it's never too late to start. Let's get one in! 💪"
        
        total_time = sum(s["duration"] for s in today_sessions)
        session_count = len(today_sessions)
        breaks = sum(s.get("breaks", 0) for s in today_sessions)
        
        response = f"Here's your day so far! 📊\n\n"
        response += f"✅ Sessions completed: {session_count}\n"
        response += f"⏱️ Total focus time: {int(total_time)} minutes\n"
        response += f"☕ Breaks taken: {breaks}\n\n"
        
        if total_time > 60:
            response += "Wow, you're crushing it today! 🔥"
        elif total_time > 25:
            response += "Nice work! Keep the momentum going! 💪"
        else:
            response += "Good start! Let's add another session! 🚀"
        
        return response

    def get_session_start_message(self):
        messages = [
            "Let's go! Time to get in the zone! 🎯",
            "You got this! Focus mode activated! 💪",
            "Alright! Let's make this session count! 🔥",
            "Here we go! Show this task who's boss! 🚀"
        ]
        return random.choice(messages)

    def get_session_complete_message(self):
        messages = [
            "Boom! Another one in the books! Great job! 🎉",
            "Nailed it! That's how it's done! 🌟",
            "Session complete! You're on fire! 🔥",
            "Yes! That's what I'm talking about! 💪",
            "Awesome work! Ready for another round? 🚀"
        ]
        return random.choice(messages)

class ChatWindow(tk.Toplevel):
    """Chat window for the productivity bot"""
    def __init__(self, parent, chatbot):
        super().__init__(parent)
        self.chatbot = chatbot
        self.title("Productivity Buddy 💬")
        self.geometry("350x500")
        self.resizable(False, False)
        
        # Position at bottom-right
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = screen_width - 370
        y = 80  # Top-right placement
        self.geometry(f"350x500+{x}+{y}")
        
        self.configure(bg=COLORS['background'])
        self.pinned = tk.BooleanVar(value=True)
        try:
            self.attributes('-topmost', True)
        except Exception:
            pass
        self.tts_enabled = tk.BooleanVar(value=TTS_AVAILABLE)
        self._tts_engine = None
        self._listening = False
        self._audio_stream = None
        self._audio_frames = []
        self._audio_samplerate = 16000
        self._build_widgets()
        self._add_bot_message(self.chatbot.get_greeting())

    def _build_widgets(self):
        # Header
        header = tk.Frame(self, bg=COLORS['primary'], height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        label = tk.Label(
            header,
            text="💬 Your Productivity Buddy",
            font=(FONT_FAMILY, FONT_SIZES['medium'], 'bold'),
            bg=COLORS['primary'],
            fg='white'
        )
        label.pack(side=tk.LEFT, padx=10, pady=12)
        pin_btn = tk.Checkbutton(
            header,
            text='📌',
            variable=self.pinned,
            command=self._toggle_pin,
            bg=COLORS['primary'],
            fg='white',
            selectcolor=COLORS['primary'],
            bd=0,
            highlightthickness=0
        )
        pin_btn.pack(side=tk.RIGHT, padx=8, pady=8)
        
        # Chat display area
        chat_frame = tk.Frame(self, bg=COLORS['surface'])
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            font=(FONT_FAMILY, FONT_SIZES['normal']),
            bg=COLORS['surface'],
            fg=COLORS['text_primary'],
            relief='flat',
            state='disabled'
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        
        # Quick action buttons
        quick_actions = tk.Frame(self, bg=COLORS['background'])
        quick_actions.pack(fill=tk.X, padx=10, pady=(0, 5))
        
        buttons = [
            ("📊 Stats", lambda: self._send_message("today")),
            ("💡 Tip", lambda: self._send_message("tip")),
            ("💪 Motivate", lambda: self._send_message("motivate"))
        ]
        
        for text, command in buttons:
            btn = tk.Button(
                quick_actions,
                text=text,
                command=command,
                bg=COLORS['surface_alt'],
                fg=COLORS['text_primary'],
                font=(FONT_FAMILY, FONT_SIZES['small']),
                relief='flat',
                cursor='hand2',
                padx=8,
                pady=4
            )
            btn.pack(side=tk.LEFT, padx=2)
        
        # Input area
        input_frame = tk.Frame(self, bg=COLORS['background'])
        input_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.message_entry = tk.Entry(
            input_frame,
            font=(FONT_FAMILY, FONT_SIZES['normal']),
            bg=COLORS['surface'],
            fg=COLORS['text_primary'],
            relief='solid',
            bd=1
        )
        self.message_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        self.message_entry.bind('<Return>', lambda e: self._send_message())
        
        send_btn = tk.Button(
            input_frame,
            text="➤",
            command=self._send_message,
            bg=COLORS['primary'],
            fg='white',
            font=(FONT_FAMILY, FONT_SIZES['medium'], 'bold'),
            relief='flat',
            cursor='hand2',
            width=3
        )
        send_btn.pack(side=tk.RIGHT)

        # Voice controls
        voice_frame = tk.Frame(self, bg=COLORS['background'])
        voice_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        self.speak_btn = tk.Button(
            voice_frame,
            text="🎤 Speak",
            command=self._toggle_listen,
            bg=COLORS['secondary'],
            fg='white',
            font=(FONT_FAMILY, FONT_SIZES['small'], 'bold'),
            relief='flat',
            cursor='hand2',
            padx=8,
            pady=4
        )
        self.speak_btn.pack(side=tk.LEFT)
        self.tts_chk = tk.Checkbutton(
            voice_frame,
            text="🔊 Speak replies",
            variable=self.tts_enabled,
            bg=COLORS['background']
        )
        self.tts_chk.pack(side=tk.RIGHT)

    def _add_bot_message(self, message):
        """Add bot message to chat"""
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, "🤖 Bot: ", 'bot')
        self.chat_display.insert(tk.END, f"{message}\n\n")
        self.chat_display.tag_config('bot', foreground=COLORS['primary'], font=(FONT_FAMILY, FONT_SIZES['normal'], 'bold'))
        self.chat_display.see(tk.END)
        self.chat_display.config(state='disabled')
        if self.tts_enabled.get() and TTS_AVAILABLE:
            threading.Thread(target=self._speak, args=(message,), daemon=True).start()

    def _add_user_message(self, message):
        """Add user message to chat"""
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, "You: ", 'user')
        self.chat_display.insert(tk.END, f"{message}\n\n")
        self.chat_display.tag_config('user', foreground=COLORS['secondary'], font=(FONT_FAMILY, FONT_SIZES['normal'], 'bold'))
        self.chat_display.see(tk.END)
        self.chat_display.config(state='disabled')

    def _toggle_pin(self):
        """Toggle always-on-top pin for the chat window"""
        try:
            self.attributes('-topmost', bool(self.pinned.get()))
        except Exception:
            pass

    def _ensure_tts(self):
        if not TTS_AVAILABLE:
            return None
        if self._tts_engine is None:
            try:
                self._tts_engine = pyttsx3.init()
                # Slightly faster speech
                rate = self._tts_engine.getProperty('rate')
                self._tts_engine.setProperty('rate', int(rate * 0.95))
            except Exception:
                self._tts_engine = None
        return self._tts_engine

    def _speak(self, text):
        engine = self._ensure_tts()
        if not engine:
            return
        try:
            engine.say(text)
            engine.runAndWait()
        except Exception:
            pass

    def _toggle_listen(self):
        if self._listening:
            self._stop_listening()
        else:
            self._start_listening()

    def _start_listening(self):
        if not AUDIO_AVAILABLE:
            self._add_bot_message("Microphone not available on this system.")
            return
        self._listening = True
        self._audio_frames = []
        self.speak_btn.config(text="⏹ Stop")
        self._add_bot_message("Listening...")
        def callback(indata, frames, time_info, status):
            if status:
                pass
            self._audio_frames.append(indata.copy())
        try:
            self._audio_stream = sd.InputStream(samplerate=self._audio_samplerate, channels=1, callback=callback)
            self._audio_stream.start()
        except Exception as e:
            self._listening = False
            self.speak_btn.config(text="🎤 Speak")
            self._add_bot_message(f"Audio error: {e}")

    def _stop_listening(self):
        if not self._listening:
            return
        self._listening = False
        try:
            if self._audio_stream:
                self._audio_stream.stop()
                self._audio_stream.close()
        finally:
            self._audio_stream = None
        self.speak_btn.config(text="🎤 Speak")
        if not self._audio_frames:
            return
        # Save to temp WAV and transcribe
        try:
            import numpy as _np
            data = _np.concatenate(self._audio_frames, axis=0)
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            tmp_path = tmp.name
            tmp.close()
            sf.write(tmp_path, data, self._audio_samplerate)
        except Exception as e:
            self._add_bot_message(f"Recording error: {e}")
            return
        def worker(path=tmp_path):
            try:
                text = self._transcribe_file(path)
                if text:
                    self.after(0, lambda t=text: self._send_message(t))
                else:
                    self.after(0, lambda: self._add_bot_message("Sorry, I couldn't hear anything."))
            finally:
                try:
                    os.remove(path)
                except Exception:
                    pass
        threading.Thread(target=worker, daemon=True).start()

    def _transcribe_file(self, filepath):
        # Prefer OpenAI transcription if available
        try:
            if getattr(self.chatbot, 'ai', None) and getattr(self.chatbot.ai, 'enabled', False):
                client = self.chatbot.ai.client
                try:
                    resp = client.audio.transcriptions.create(model=os.getenv('OPENAI_STT_MODEL','gpt-4o-transcribe'), file=open(filepath,'rb'))
                except Exception:
                    resp = client.audio.transcriptions.create(model='whisper-1', file=open(filepath,'rb'))
                text = getattr(resp, 'text', None) or (resp.get('text') if isinstance(resp, dict) else None)
                return (text or '').strip()
        except Exception:
            pass
        # Fallback to SpeechRecognition (Google Web Speech)
        if SR_AVAILABLE:
            try:
                recognizer = sr.Recognizer()
                with sr.AudioFile(filepath) as source:
                    audio = recognizer.record(source)
                return recognizer.recognize_google(audio)
            except Exception:
                return ""
        return ""

    def _send_message(self, preset_message=None):
        """Send message and get bot response"""
        if preset_message:
            user_message = preset_message
        else:
            user_message = self.message_entry.get().strip()
            self.message_entry.delete(0, tk.END)
        
        if not user_message:
            return
        
        self._add_user_message(user_message)
        
        # Get bot response (AI if available)
        if getattr(self.chatbot, 'ai', None) and getattr(self.chatbot.ai, 'enabled', False):
            self._add_bot_message("🧠 Thinking...")
            def worker():
                try:
                    reply = self.chatbot.get_ai_response(user_message)
                except Exception:
                    reply = self.chatbot.get_response(user_message)
                self.after(0, lambda: self._add_bot_message(reply))
            threading.Thread(target=worker, daemon=True).start()
        else:
            bot_response = self.chatbot.get_response(user_message)
            self.after(500, lambda: self._add_bot_message(bot_response))

def calculate_streak(sessions):
    if not sessions:
        return 0
    dates = {s["date"] for s in sessions}
    streak = 0
    day = datetime.now().date()
    while day.strftime("%Y-%m-%d") in dates:
        streak += 1
        day -= timedelta(days=1)
    return streak
if __name__ == "__main__":
    try:
        print("🚀 Starting SessionSlice Productivity Tracker...")
        app = SessionSliceApp()
        print("✅ Application loaded successfully!")
        app.mainloop()
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")