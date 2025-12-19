import tkinter as tk
from tkinter import ttk
import datetime
import requests
import threading

# --- DATA CONFIGURATION ---
# Database of locations with Coordinates for API Lookup
# Note: "National Avg" replaced with a specific location (Kansas) for API demo
LOCATION_DATA = {
    "Morrisville, NC": {
        "lat": 35.82, "lon": -78.82,
        "water_price": 0.018,   # High (Cary Water) ~$18/1000gal
    },
    "Charlotte, NC": {
        "lat": 35.22, "lon": -80.84,
        "water_price": 0.012,   # Lower (Charlotte Water) ~$12/1000gal
    },
    "Lebanon, KS (US Center)": {
        "lat": 39.80, "lon": -98.55,
        "water_price": 0.010,
    }
}

# OpenEI API Key (Use 'DEMO_KEY' for testing, but it has rate limits)
OPENEI_API_KEY = "DEMO_KEY"

class LaundryOptimizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Laundry Optimizer Pro")
        self.root.geometry("1920x1080")
        self.root.resizable(False, False)
        
        # --- THEME CONFIGURATION ---
        self.colors = {
            "bg": "#f4f6f9",          # Light Blue-Gray Background
            "card": "#ffffff",        # White Cards
            "text_main": "#2c3e50",   # Dark Blue-Gray Text
            "text_light": "#7f8c8d",  # Lighter Gray Text
            "accent": "#3498db",      # Blue Accent
            "border": "#e0e0e0",      # Subtle Borders
            "success": "#27ae60",     # Green
            "warning": "#f39c12",     # Orange
            "danger": "#c0392b"       # Red
        }
        self.root.configure(bg=self.colors["bg"])
        
        # Cache for API responses
        self.api_cache = {}
        self.history_rates = [0.15] * 24
        
        # Default Selection
        self.current_loc = "Morrisville, NC"
        
        # Appliance Constants
        self.WASHER_KWH = 0.5
        self.ELEC_DRYER_KWH = 3.0
        self.GAS_DRYER_KWH = 0.3 
        self.WATER_GALS = 20

        # UI STYLING
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Configure Styles
        self.style.configure("TFrame", background=self.colors["bg"])
        self.style.configure("Card.TFrame", background=self.colors["card"])
        self.style.configure("TLabel", background=self.colors["bg"], foreground=self.colors["text_main"])
        self.style.configure("Card.TLabel", background=self.colors["card"], foreground=self.colors["text_main"])
        self.style.configure("Sub.TLabel", background=self.colors["card"], foreground=self.colors["text_light"], font=("Segoe UI", 9))
        self.style.configure("Value.TLabel", background=self.colors["card"], foreground=self.colors["text_main"], font=("Segoe UI", 18, "bold"))
        self.style.configure("Title.TLabel", background=self.colors["bg"], foreground=self.colors["text_main"], font=("Segoe UI", 16, "bold"))
        self.style.configure("TButton", font=("Segoe UI", 10))
        
        # --- GUI ELEMENTS ---
        
        # Main Container
        self.main_frame = ttk.Frame(root, padding="20")
        self.main_frame.pack(fill="both", expand=True)
        
        # 1. Header & Search
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill="x", pady=(0, 15))
        
        ttk.Label(header_frame, text="Laundry Optimizer", style="Title.TLabel").pack(side="left")
        
        # Search Bar (Custom styled entry)
        search_cont = tk.Frame(self.main_frame, bg="white", highlightbackground=self.colors["border"], highlightthickness=1)
        search_cont.pack(fill="x", pady=(0, 20), ipady=5)
        
        self.loc_var = tk.StringVar(value=self.current_loc)
        self.loc_entry = tk.Entry(search_cont, textvariable=self.loc_var, font=("Segoe UI", 11), bd=0, bg="white", fg=self.colors["text_main"])
        self.loc_entry.pack(side="left", fill="x", expand=True, padx=10)
        self.loc_entry.bind("<Return>", lambda event: self.search_location())
        
        search_btn = tk.Button(search_cont, text="🔍", command=self.search_location, bd=0, bg="white", cursor="hand2")
        search_btn.pack(side="right", padx=10)

        # 2. Status Card (Hero Section)
        self.status_frame = tk.Frame(self.main_frame, bg=self.colors["card"], highlightbackground=self.colors["border"], highlightthickness=1)
        self.status_frame.pack(fill="x", pady=(0, 15), ipady=10)
        
        # Inner layout for Status
        status_inner = tk.Frame(self.status_frame, bg=self.colors["card"])
        status_inner.pack(fill="both", expand=True, padx=20)
        
        # Graphic
        self.gfx_canvas = tk.Canvas(status_inner, width=70, height=90, bg=self.colors["card"], highlightthickness=0)
        self.gfx_canvas.pack(side="left")
        self.gfx_canvas.create_rectangle(5, 5, 65, 85, outline=self.colors["text_main"], width=2, fill="white") # Body
        self.gfx_canvas.create_line(5, 20, 65, 20, fill=self.colors["text_main"], width=1) # Panel
        self.door_light = self.gfx_canvas.create_oval(15, 30, 55, 70, fill="gray", outline=self.colors["text_main"], width=1) # Door

        # Text Info
        status_text_area = tk.Frame(status_inner, bg=self.colors["card"])
        status_text_area.pack(side="left", fill="both", expand=True, padx=(15, 0))
        
        ttk.Label(status_text_area, text="CURRENT STATUS", style="Sub.TLabel").pack(anchor="w", pady=(5,0))
        self.status_label = ttk.Label(status_text_area, text="LOADING...", font=("Segoe UI", 22, "bold"), style="Card.TLabel")
        self.status_label.pack(anchor="w")
        self.lbl_advice = ttk.Label(status_text_area, text="--", style="Sub.TLabel", wraplength=250)
        self.lbl_advice.pack(anchor="w", pady=(2,0))

        # 3. Metrics Grid (Cost & Rate)
        metrics_frame = ttk.Frame(self.main_frame)
        metrics_frame.pack(fill="x", pady=(0, 15))
        
        # Helper for cards
        def create_card(parent, title):
            f = tk.Frame(parent, bg=self.colors["card"], highlightbackground=self.colors["border"], highlightthickness=1)
            f.pack(side="left", fill="both", expand=True, padx=5)
            ttk.Label(f, text=title, style="Sub.TLabel").pack(anchor="w", padx=10, pady=(10,0))
            l = ttk.Label(f, text="--", style="Value.TLabel")
            l.pack(anchor="w", padx=10, pady=(0,10))
            return l
            
        self.lbl_cost = create_card(metrics_frame, "EST. COST")
        self.lbl_rate_info = create_card(metrics_frame, "RATE / kWh")

        # 4. Graph Card
        graph_card = tk.Frame(self.main_frame, bg=self.colors["card"], highlightbackground=self.colors["border"], highlightthickness=1)
        graph_card.pack(fill="both", expand=True, pady=(0, 15))
        
        graph_header = tk.Frame(graph_card, bg=self.colors["card"])
        graph_header.pack(fill="x", padx=15, pady=10)
        ttk.Label(graph_header, text="24-Hour Price Trend", style="Card.TLabel", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.lbl_time = ttk.Label(graph_header, text="", style="Sub.TLabel")
        self.lbl_time.pack(side="right")

        self.graph_canvas = tk.Canvas(graph_card, bg=self.colors["card"], height=120, highlightthickness=0)
        self.graph_canvas.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.graph_canvas.bind("<Configure>", lambda e: self.draw_graph(self.history_rates))

        # 5. Footer Controls
        footer_frame = ttk.Frame(self.main_frame)
        footer_frame.pack(fill="x")
        
        self.lbl_provider = ttk.Label(footer_frame, text="", style="Sub.TLabel", background=self.colors["bg"])
        self.lbl_provider.pack(anchor="w", pady=(0, 5))
        
        self.dryer_var = tk.StringVar(value="Electric")
        self.dryer_check = ttk.Checkbutton(footer_frame, text="Gas Dryer", 
                                           variable=self.dryer_var, onvalue="Gas", offvalue="Electric",
                                           command=self.update_data)
        self.dryer_check.pack(side="left")
        
        self.solar_mode_var = tk.BooleanVar(value=False)
        self.solar_check = ttk.Checkbutton(footer_frame, text="Solar Mode ☀️", 
                                           variable=self.solar_mode_var,
                                           command=self.update_data)
        self.solar_check.pack(side="left", padx=10)

        self.btn_refresh = ttk.Button(footer_frame, text="Refresh", command=self.refresh_data)
        self.btn_refresh.pack(side="right")

        self.btn_settings = ttk.Button(footer_frame, text="⚙ Settings", command=self.open_settings)
        self.btn_settings.pack(side="right", padx=5)

        # Start
        self.update_data()

    def refresh_data(self):
        # Clear cache for current location to force re-fetch
        if self.current_loc in self.api_cache:
            del self.api_cache[self.current_loc]
        
        self.status_label.config(text="REFRESHING...", foreground=self.colors["text_light"])
        self.gfx_canvas.itemconfig(self.door_light, fill="gray")
        self.update_data()

    def open_settings(self):
        win = tk.Toplevel(self.root)
        win.title("Settings")
        win.geometry("300x250")
        win.configure(bg=self.colors["card"])
        
        ttk.Label(win, text="Appliance Power (kWh)", style="Title.TLabel", font=("Segoe UI", 12, "bold")).pack(pady=10)
        
        def add_field(label, var_name):
            f = tk.Frame(win, bg=self.colors["card"])
            f.pack(fill="x", padx=20, pady=5)
            ttk.Label(f, text=label, style="Sub.TLabel").pack(side="left")
            entry = ttk.Entry(f, width=10)
            entry.insert(0, str(getattr(self, var_name)))
            entry.pack(side="right")
            return entry
            
        e_washer = add_field("Washer:", "WASHER_KWH")
        e_dryer_e = add_field("Elec. Dryer:", "ELEC_DRYER_KWH")
        e_dryer_g = add_field("Gas Dryer:", "GAS_DRYER_KWH")
        
        def save():
            try:
                self.WASHER_KWH = float(e_washer.get())
                self.ELEC_DRYER_KWH = float(e_dryer_e.get())
                self.GAS_DRYER_KWH = float(e_dryer_g.get())
                self.update_data()
                win.destroy()
            except ValueError: pass
            
        ttk.Button(win, text="Save", command=save).pack(pady=20)

    def search_location(self):
        query = self.loc_var.get()
        if not query: return
        
        self.status_label.config(text="SEARCHING...", foreground=self.colors["text_light"])
        self.gfx_canvas.itemconfig(self.door_light, fill="gray")
        
        # Run geocoding in thread
        threading.Thread(target=self._perform_geocoding, args=(query,), daemon=True).start()

    def _perform_geocoding(self, query):
        try:
            # Nominatim API (OpenStreetMap)
            url = "https://nominatim.openstreetmap.org/search"
            headers = {'User-Agent': 'LaundryOptimizerApp/1.0'}
            params = {'q': query, 'format': 'json', 'limit': 1}
            
            response = requests.get(url, params=params, headers=headers, timeout=5)
            response.raise_for_status()
            results = response.json()
            
            if results:
                loc = results[0]
                # Update global data with new coordinates
                new_key = loc['display_name'].split(',')[0] # Use City name
                LOCATION_DATA[new_key] = {
                    "lat": float(loc['lat']),
                    "lon": float(loc['lon']),
                    "water_price": 0.012 # Default average
                }
                
                self.current_loc = new_key
                self.root.after(0, lambda: self.loc_var.set(new_key))
                self.root.after(0, self.update_data)
            else:
                self.root.after(0, lambda: self.status_label.config(text="NOT FOUND", foreground=self.colors["danger"]))
        except Exception as e:
            print(f"Geo Error: {e}")
            self.root.after(0, lambda: self.status_label.config(text="ERROR", foreground=self.colors["danger"]))

    def update_data(self):
        # Run API call in a separate thread to prevent UI freezing
        threading.Thread(target=self._fetch_and_update_ui, daemon=True).start()

    def _fetch_and_update_ui(self):
        now = datetime.datetime.now()
        data = LOCATION_DATA[self.current_loc]
        
        # 1. Fetch Rate from OpenEI API
        rate = 0.15 # Default fallback
        history_rates = [0.15] * 24 # Default flat history
        advice_msg = "Real-time rate fetched from OpenEI Utility Database"
        provider_name = "Unknown Provider"
        
        try:
            # Check cache first
            if self.current_loc in self.api_cache:
                utility = self.api_cache[self.current_loc]
            else:
                url = "https://api.openei.org/utility_rates"
                params = {
                    "version": "latest",
                    "format": "json",
                    "api_key": OPENEI_API_KEY,
                    "lat": data["lat"],
                    "lon": data["lon"],
                    "sector": "Residential",
                    "detail": "full",
                    "limit": 1
                }
                
                response = requests.get(url, params=params, timeout=5)
                response.raise_for_status()
                api_data = response.json()

                utility = None
                if api_data.get("items"):
                    utility = api_data["items"][0]
                    self.api_cache[self.current_loc] = utility

            if utility:
                provider_name = utility.get("name", "Unknown Utility")
                history_rates = []

                # Calculate rates for the past 24 hours (including now)
                # And look ahead for the best time
                for i in range(24):
                    # Time point: from 23 hours ago up to 0 hours ago (now)
                    t = now - datetime.timedelta(hours=23-i)
                    history_rates.append(self._get_rate_from_schedule(utility, t))
                
                # Current rate is the last one in the history list
                rate = history_rates[-1]

                # Look ahead 12 hours for a better rate
                future_rates = []
                for i in range(1, 13):
                    t = now + datetime.timedelta(hours=i)
                    future_rates.append((t, self._get_rate_from_schedule(utility, t)))
                
                # Find minimum rate in future
                best_time, best_rate = min(future_rates, key=lambda x: x[1])
                
                if best_rate < rate:
                    diff = rate - best_rate
                    advice_msg = f"💡 Tip: Wait until {best_time.strftime('%I %p')} to save ${(diff * (self.WASHER_KWH + self.ELEC_DRYER_KWH)):.2f} per load!"
                else:
                    advice_msg = "✅ Best time to wash is right now."

        except Exception as e:
            print(f"API Error: {e}")
            provider_name = "API Error (Using Default)"

        # 2. Determine Status based on Rate
        # Simple logic: < $0.12 is cheap, > $0.20 is expensive
        if rate < 0.12:
            status = "WASH NOW"
            color = self.colors["success"]
        elif rate > 0.20:
            status = "WAIT"
            color = self.colors["danger"]
        else:
            status = "OK TO WASH"
            color = self.colors["warning"]

        # Solar Mode Override
        if self.solar_mode_var.get():
            # Peak Solar Window: 11 AM - 3 PM
            if 11 <= now.hour < 15:
                status = "SOLAR PWR"
                color = self.colors["success"]
                advice_msg = "☀️ Solar Mode: Running on peak sun."
            else:
                status = "WAIT"
                color = self.colors["warning"]
                advice_msg = "☀️ Solar Mode: Wait for noon (11 AM - 3 PM) for max power."

        # Calculate Cost
        dryer_kwh = self.GAS_DRYER_KWH if self.dryer_var.get() == "Gas" else self.ELEC_DRYER_KWH
        cost = (self.WASHER_KWH + dryer_kwh) * rate + (self.WATER_GALS * data["water_price"])

        # Update UI
        # Must use after() or similar to update UI from thread, but for simple Tkinter 
        # direct calls often work if not heavy. To be safe, we schedule it.
        self.root.after(0, lambda: self._update_ui_elements(provider_name, now, rate, cost, status, color, history_rates, advice_msg))

    def _get_rate_from_schedule(self, utility, t):
        month_idx = t.month - 1
        hour_idx = t.hour
        is_weekend = t.weekday() >= 5
        schedule_name = "energyweekendschedule" if is_weekend else "energyweekdayschedule"
        
        if schedule_name in utility:
            period_idx = utility[schedule_name][month_idx][hour_idx]
            rate_struct = utility["energyratestructure"][period_idx][0]
            return float(rate_struct.get("rate", 0.15))
        return 0.15

    def _update_ui_elements(self, provider, now, rate, cost, status, color, history, advice):
        self.history_rates = history
        self.lbl_provider.config(text=provider)
        self.lbl_time.config(text=now.strftime("%I:%M %p"))
        self.lbl_rate_info.config(text=f"${rate:.3f}/kWh")
        self.lbl_cost.config(text=f"${cost:.2f}")
        self.status_label.config(text=status, foreground=color)
        self.gfx_canvas.itemconfig(self.door_light, fill=color)
        self.lbl_advice.config(text=advice)
        self.draw_graph(history)

    def draw_graph(self, rates):
        self.graph_canvas.delete("all")
        
        w = self.graph_canvas.winfo_width()
        h = self.graph_canvas.winfo_height()
        # Fallback if canvas isn't rendered yet
        if w < 50: w = 400
        if h < 50: h = 120
        
        margin = 10
        graph_w = w - 2 * margin
        graph_h = h - 2 * margin
        
        min_r = min(rates)
        max_r = max(rates)
        
        # Avoid division by zero if flat rate
        if max_r == min_r:
            max_r += 0.01
            min_r -= 0.01
            
        x_step = graph_w / (len(rates) - 1)
        
        # Draw Grid Lines (Low, Mid, High)
        self.graph_canvas.create_line(margin, margin, w-margin, margin, fill=self.colors["bg"], dash=(2,2))
        self.graph_canvas.create_line(margin, h-margin, w-margin, h-margin, fill=self.colors["bg"], dash=(2,2))
        
        # Draw Plot
        points = []
        for i, r in enumerate(rates):
            x = margin + (i * x_step)
            # Invert Y (canvas 0 is top)
            y = h - margin - ((r - min_r) / (max_r - min_r) * graph_h)
            points.extend([x, y])
            
        self.graph_canvas.create_line(*points, fill=self.colors["accent"], width=3, smooth=True)
        
        # Draw End Point Dot
        self.graph_canvas.create_oval(points[-2]-4, points[-1]-4, points[-2]+4, points[-1]+4, fill=self.colors["accent"], outline="white", width=2)


if __name__ == "__main__":
    root = tk.Tk()
    app = LaundryOptimizerApp(root)
    root.mainloop()