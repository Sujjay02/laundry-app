# 🧺 Laundry Optimizer Pro

**Laundry Optimizer Pro** is a smart desktop assistant that helps you save money and reduce your carbon footprint by determining the best time to do laundry. It monitors real-time electricity rates, weather conditions, and solar windows to suggest the optimal wash time.


## 🚀 Features

*   **💰 Smart Cost Calculation:** Fetches real-time utility rates (via OpenEI) to calculate the exact cost of a load.
*   **🌤️ Weather Integration:** Checks local weather to suggest "Line Drying" on warm, sunny days.
*   **🌱 Carbon Footprint Tracking:** Estimates the CO₂ impact of every wash.
*   **📉 Price Trend Graph:** Visualizes electricity rates over the last 24 hours to spot trends.
*   **🔔 Smart Notifications:** Runs in the system tray and alerts you when electricity rates drop.
*   **☀️ Solar Mode:** Special logic for users with solar panels to maximize usage during peak sun hours.
*   **📊 History & Savings:** Logs your washes and tracks total money saved over time.

## 🛠️ Installation

### Prerequisites
*   Python 3.8 or higher
*   `pip` (Python package manager)

### 1. Clone the Repository
```bash
git clone https://github.com/Sujjay02/laundry-optimizer.git
cd laundry-optimizer
```

### 2. Install Dependencies
This project relies on several Python libraries for the GUI, graphing, and API requests.

```bash
pip install requests matplotlib pystray Pillow plyer
```

*Note: Tkinter is usually included with Python, but on Linux, you may need to install it separately (e.g., `sudo apt-get install python3-tk`).*

## 🏃 Usage

### Running the Script
Simply run the main Python file:

```bash
python laundry_app.py
```

### How to Use
1.  **Search Location:** Enter your city (e.g., "Austin, TX") to fetch local utility rates and weather.
2.  **Check Status:** The dashboard will tell you to **"WASH NOW"** or **"WAIT"** based on current rates.
3.  **Log Wash:** Click "Log Wash" when you start a load to track your savings in the History tab.
4.  **Background Mode:** Close the window to minimize it to the System Tray. It will keep monitoring prices in the background.

## 📦 Building an Executable (.exe)

You can package this application into a standalone `.exe` file for Windows using PyInstaller.

1.  Install PyInstaller:
    ```bash
    pip install pyinstaller
    ```

2.  Build the executable:
    ```bash
    pyinstaller --noconsole --onefile --name="LaundryOptimizer" laundry_app.py
    ```

3.  The executable will be located in the `dist/` folder.

## ⚙️ Configuration

*   **API Keys:** The app uses a demo key for OpenEI. For heavy usage, replace `OPENEI_API_KEY` in the code with your own free key from OpenEI.
*   **Appliance Settings:** Go to **Settings** within the app to customize the wattage of your specific washer and dryer for accurate cost estimation.

## 💻 Technologies Used

*   **Python 3**
*   **Tkinter** (GUI Framework)
*   **Matplotlib** (Data Visualization)
*   **OpenEI API** (Utility Rate Data)
*   **Open-Meteo API** (Weather Data)
*   **Pystray** (System Tray Integration)

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
