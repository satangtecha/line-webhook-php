import streamlit as st
import psutil
from datetime import datetime, timedelta
import time
import json
import os
import requests
import pandas as pd
import sqlite3
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import numpy as np
import statsmodels.tsa.arima.model as sm_arima
import webbrowser # Import webbrowser module
import threading # Import threading for opening browser without blocking


# Set Streamlit page config
st.set_page_config(page_title="PreBreak Monitor", layout="wide", initial_sidebar_state="expanded")

# --- Session State Initialization (Moved to top for robustness) ---
# Ensure dark_mode is initialized early in session state before other components access it.
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = True # Default to dark mode if not set

# Initialize other session states after dark_mode
if 'alert_log' not in st.session_state:
    st.session_state.alert_log = [] # Stores: [{"timestamp": "...", "message": "...", "type": "info/warning/danger"}]
if 'alert_sent_cpu_threshold' not in st.session_state:
    st.session_state.alert_sent_cpu_threshold = False
if 'alert_sent_ram_threshold' not in st.session_state:
    st.session_state.alert_sent_ram_threshold = False
if 'alert_sent_disk_threshold' not in st.session_state:
    st.session_state.alert_sent_disk_threshold = False
if 'alert_sent_battery_threshold' not in st.session_state: 
    st.session_state.alert_sent_battery_threshold = False
if 'alert_sent_cpu_trend' not in st.session_state:
    st.session_state.alert_sent_cpu_trend = False
if 'alert_sent_ram_trend' not in st.session_state:
    st.session_state.alert_sent_ram_trend = False
if 'alert_sent_disk_trend' not in st.session_state: 
    st.session_state.alert_sent_disk_trend = False 
if 'alert_sent_cpu_prediction' not in st.session_state:
    st.session_state.alert_sent_cpu_prediction = False
if 'alert_sent_ram_prediction' not in st.session_state:
    st.session_state.alert_sent_ram_prediction = False
if 'alert_sent_disk_prediction' not in st.session_state:
    st.session_state.alert_sent_disk_prediction = False
# Initialize last ML retrain time
if 'last_ml_retrain_time' not in st.session_state:
    st.session_state.last_ml_retrain_time = datetime.min # Set to min time to force immediate retraining on start


# --- Custom CSS for Dark Mode, Font and General Styling ---
# Using st.markdown with unsafe_allow_html=True to inject CSS
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [class*="st-emotion"] {{
        font-family: 'Inter', sans-serif;
    }}

    /* CSS variables for application theme */
    :root {{
        --app-bg-color: #f1f5f9; /* Light: slate-100 */
        --container-bg-color: #f8fafc; /* Light: slate-50 */
        --card-bg-color: #ffffff; /* Light: white */
        --text-color: #1e293b; /* Light: slate-900 */
        --sub-text-color: #64748b; /* Light: slate-500 */

        /* Metric card specific background colors */
        --metric-card-bg-normal: #ffffff; /* Light: white */
        --metric-card-bg-warning: #fef3c7; /* Light: amber-50 */
        --metric-card-bg-danger: #fee2e2; /* Light: red-50 */

        /* Alert log colors */
        --info-bg: #e0f2fe; /* Light: blue-50 */
        --info-text: #1e40af; /* Light: blue-800 */
        --warning-bg: #fffbeb; /* Light: amber-50 */
        --warning-text: #b45309; /* Light: amber-700 */
        --danger-bg: #fee2e2; /* Light: red-50 */
        --danger-text: #b91c1c; /* Light: red-800 */

        /* Streamlit's default info/warning/error border colors */
        --st-info-border-color: #3b82f6; /* blue-500 */
        --st-warning-border-color: #f59e0b; /* amber-500 */
        --st-error-border-color: #ef4444; /* red-500 */
    }}

    /* Dark mode specific variables */
    body.dark-mode {{
        --app-bg-color: #0f172a; /* Dark: slate-900 */
        --container-bg-color: #1e293b; /* Dark: slate-800 (slightly lighter for contrast) */
        --card-bg-color: #2d3748; /* Dark: slate-700 */
        --text-color: #e2e8f0; /* Dark: slate-200 */
        --sub-text-color: #94a3b8; /* Dark: slate-400 */

        --metric-card-bg-normal: #2d3748; /* Dark grey */
        --metric-card-bg-warning: #b45309; /* Dark amber */
        --metric-card-bg-danger: #991b1b; /* Dark red */

        --info-bg: #1e3a8a; 
        --info-text: #bfdbfe;
        --warning-bg: #78350f;
        --warning-text: #fcd34d;
        --danger-bg: #7f1d1d;
        --danger-text: #fca5a5;
    }}

    /* Base app background color, controlled by CSS variable */
    .stApp {{
        background-color: var(--app-bg-color); 
        color: var(--text-color); /* General text color for the app */
    }}
    .stAlert {{
        border-radius: 0.5rem; /* rounded-lg */
    }}
    .stButton>button {{
        border-radius: 0.5rem; /* rounded-lg */
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); /* shadow-md */
        transition: all 0.2s ease-in-out;
        background-color: #3b82f6; /* blue-500 */
        color: white;
        border: none;
        padding: 0.75rem 1.25rem;
        font-weight: 600;
    }}
    .stButton>button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05); /* shadow-lg */
        background-color: #2563eb; /* blue-600 */
    }}
    .stSlider > div > div > div {{
        border-radius: 0.5rem; /* rounded-lg */
    }}
    .stTextInput > div > div > input {{
        border-radius: 0.5rem; /* rounded-lg */
    }}
    .st-dg, .st-ck, .st-cn {{ /* Targets various input/select boxes */
        border-radius: 0.5rem; /* rounded-lg */
    }}
    /* Styles for general Streamlit components (like sidebar inputs, etc.) */
    .st-au, .st-bf, .st-bg, .st-b5, .st-a8, .st-br {{ /* metric, text_area, columns, info, warning, error */
        border-radius: 0.5rem; /* rounded-lg */
        padding: 1rem; /* p-4 */
    }}

    /* Common container/card styles, colors are controlled by CSS variable */
    .theme-container {{
        border-radius: 0.75rem; /* rounded-xl */
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05); /* shadow-lg */
        margin-bottom: 2rem; /* Add margin-bottom for better spacing between sections */
        background-color: var(--container-bg-color);
        color: var(--text-color);
    }}
    .theme-card {{
        border-radius: 0.75rem; /* rounded-xl */
        padding: 1rem; /* p-4 */
        margin-bottom: 1rem; /* mb-4 */
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); /* shadow-md */
        background-color: var(--card-bg-color);
        color: var(--text-color);
    }}

    /* Specific styling for custom metric cards (replaces st.metric visually) */
    .metric-card {{
        border-radius: 0.75rem;
        padding: 1rem;
        margin-bottom: 1rem; /* Consistent spacing */
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transition: background-color 0.3s ease-in-out, box-shadow 0.3s ease-in-out; /* Smooth transitions */
        color: var(--text-color); /* Use general text color for card content */
    }}

    /* Background colors for metric cards based on status */
    .metric-card-normal {{ background-color: var(--metric-card-bg-normal); }}
    .metric-card-warning {{ background-color: var(--metric-card-bg-warning); }}
    .metric-card-danger {{ background-color: var(--metric-card-bg-danger); }}

    /* Text colors within custom metric cards */
    .metric-card .metric-label {{
        font-size: 0.875rem; /* text-sm */
        color: var(--sub-text-color);
        margin-bottom: 0.25rem;
    }}
    .metric-card .metric-value {{
        font-size: 2.25rem; /* text-4xl */
        font-weight: 700; /* font-bold */
        color: var(--text-color); /* Use general text color */
    }}

    /* Styling for st.text_area to look like a card */
    .stTextArea > label {{ /* Target the label of the text area */
        font-size: 1.125rem; /* text-lg */
        font-weight: 600;
        margin-bottom: 0.5rem;
        display: block; /* Make label a block element for spacing */
    }}
    .stTextArea > div > div {{ /* Target the actual text area container */
        background-color: var(--card-bg-color);
        border-radius: 0.75rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        padding: 1rem;
        border: none; /* Remove default border */
    }}
    .stTextArea > div > div > textarea {{ /* Target the textarea itself */
        background-color: transparent; /* Make inner textarea transparent */
        color: var(--text-color);
    }}

    /* Styling for st.info, st.warning, st.error */
    .st-br {{ /* Streamlit's default container for info/warning/error */
        border-left: 6px solid var(--st-info-border-color); /* Streamlit's default color variables */
        border-radius: 0.75rem;
        padding: 1rem;
        margin-bottom: 1rem;
        background-color: var(--card-bg-color); /* Match card background */
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        color: var(--text-color);
    }}
    .st-br.st-cf {{ /* Info */
        --st-info-border-color: #3b82f6; /* blue-500 */
    }}
    .st-br.st-ch {{ /* Warning */
        --st-info-border-color: #f59e0b; /* amber-500 */
    }}
    .st-br.st-c9 {{ /* Error */
        --st-info-border-color: #ef4444; /* red-500 */
    }}

    /* Alert log entry styling */
    .alert-entry {{
        border-radius: 0.5rem;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        transition: background-color 0.2s ease-in-out;
    }}
    .alert-entry-info {{ background-color: var(--info-bg); color: var(--info-text); }}
    .alert-entry-warning {{ background-color: var(--warning-bg); color: var(--warning-text); }}
    .alert-entry-danger {{ background-color: var(--danger-bg); color: var(--danger-text); }}

    </style>
    <script>
    // Script to dynamically apply CSS variables for theme
    // Now accepts a boolean parameter to directly apply theme, or reads from body class if parameter is null
    function applyThemeStyles(forceDarkModeState = null) {{
        let isDarkMode;
        if (forceDarkModeState !== null) {{
            isDarkMode = forceDarkModeState; // Use the explicitly passed state from Python
        }} else {{
            isDarkMode = document.body.classList.contains('dark-mode'); // Fallback to reading from body class (e.g., if triggered by external CSS change)
        }}

        if (isDarkMode) {{
            document.documentElement.style.setProperty('--app-bg-color', '#0f172a'); /* Dark: slate-900 */
            document.documentElement.style.setProperty('--container-bg-color', '#1e293b'); /* Dark: slate-800 */
            document.documentElement.style.setProperty('--card-bg-color', '#2d3748'); /* Dark: slate-700 */
            document.documentElement.style.setProperty('--text-color', '#e2e8f0'); /* Dark: slate-200 */
            document.documentElement.style.setProperty('--sub-text-color', '#94a3b8'); /* Dark: slate-400 */

            document.documentElement.style.setProperty('--metric-card-bg-normal', '#2d3748'); /* Dark grey */
            document.documentElement.style.setProperty('--metric-card-bg-warning', '#b45309'); /* Dark amber */
            document.documentElement.style.setProperty('--metric-card-bg-danger', '#991b1b'); /* Dark red */

            document.documentElement.style.setProperty('--info-bg', '#1e3a8a'); 
            document.documentElement.style.setProperty('--info-text', '#bfdbfe');
            document.documentElement.style.setProperty('--warning-bg', '#78350f');
            document.documentElement.style.setProperty('--warning-text', '#fcd34d');
            document.documentElement.style.setProperty('--danger-bg', '#7f1d1d');
            document.documentElement.style.setProperty('--danger-text', '#fca5a5');

        }} else {{
            document.documentElement.style.setProperty('--app-bg-color', '#f1f5f9'); /* Light: slate-100 */
            document.documentElement.style.setProperty('--container-bg-color', '#f8fafc'); /* Light: slate-50 */
            document.documentElement.style.setProperty('--card-bg-color', '#ffffff');
            document.documentElement.style.setProperty('--text-color', '#1e293b'); /* Light: slate-900 */
            document.documentElement.style.setProperty('--sub-text-color', '#64748b');
            
            document.documentElement.style.setProperty('--metric-card-bg-normal', '#ffffff'); /* White */
            document.documentElement.style.setProperty('--metric-card-bg-warning', '#fef3c7'); /* Light amber */
            document.documentElement.style.setProperty('--metric-card-bg-danger', '#fee2e2'); /* Light red */

            document.documentElement.style.setProperty('--info-bg', '#e0f2fe');
            document.documentElement.style.setProperty('--info-text', '#1e40af');
            document.documentElement.style.setProperty('--warning-bg', '#fffbeb');
            document.documentElement.style.setProperty('--warning-text', '#b45309');
            document.documentElement.style.setProperty('--danger-bg', '#fee2e2');
            document.documentElement.style.setProperty('--danger-text', '#b91c1c');
        }}
    }}

    // Observe changes to the body's class list
    const observer = new MutationObserver((mutationsList) => {{
        for (const mutation of mutationsList) {{
            if (mutation.type === 'attributes' && mutation.attributeName === 'class') {{
                // When observer triggers, re-read from body class
                applyThemeStyles(); 
            }}
        }}
    }});

    // Start observing the body for class changes
    observer.observe(document.body, {{ attributes: true }});

    // CRITICAL PART: Immediately Invoked Function Expression (IIFE)
    // This runs immediately whenever the script is loaded/reloaded by Streamlit
    (function() {{
        // Inject the boolean value from Python's session state directly
        const isDarkModeEnabledFromPython = {str(st.session_state.dark_mode).lower()}; 
        
        if (isDarkModeEnabledFromPython) {{
            document.body.classList.add('dark-mode');
            document.body.classList.remove('light-mode'); // Ensure light-mode is removed
        }} else {{
            document.body.classList.add('light-mode'); // Ensure light-mode is added
            document.body.classList.remove('dark-mode');
        }}
        // Call applyThemeStyles directly with the value from Python for initial/rerun application
        applyThemeStyles(isDarkModeEnabledFromPython); 
    }})();
    </script>
    """, unsafe_allow_html=True)


# --- Database Setup ---
DB_PATH = os.path.join(os.path.dirname(__file__), 'system_monitor.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usage_data (
            timestamp TEXT PRIMARY KEY,
            cpu REAL,
            ram REAL,
            disk REAL,
            battery TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print(f"DEBUG: SQLite database initialized at {DB_PATH}")

# Initialize DB when the script runs
init_db()

# --- Function to load and save config ---
def load_config():
    config_file_path = os.path.join(os.path.dirname(__file__), 'config.json')
    print(f"DEBUG: Looking for config.json at: {config_file_path}")

    default_config = {
        "thresholds": {
            "cpu_limit": 80,
            "ram_limit": 75,
            "disk_limit": 90,
            "battery_low_limit": 20 
        },
        "alert_settings": {
            "line_webhook_url": "https://line-webhook-php.onrender.com",
            "line_target_user_id": "U4d66cb0a61bc7385dd2407080f64bb42" # Updated with provided User ID
        },
        "trend_analysis_settings": {
            "lookback_minutes": 5,
            "min_increase_percent": 10
        },
        "prediction_settings": {
            "prediction_lookback_minutes": 30,
            "prediction_alert_threshold_factor": 1.1,
            "prediction_model": "Linear Regression",
            "prediction_retrain_interval_minutes": 15
        }
    }

    config = {}
    config_updated = False

    try:
        if os.path.exists(config_file_path):
            with open(config_file_path, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
            print(f"DEBUG: ✅ Loaded configuration from {config_file_path}")
            
            config = default_config.copy()
            def update_dict(d, u):
                for k, v in u.items():
                    if isinstance(v, dict):
                        d[k] = update_dict(d.get(k, {}), v)
                    else:
                        d[k] = v
                return d
            
            initial_config_str = json.dumps(loaded_config, sort_keys=True)
            merged_config = update_dict(config, loaded_config)
            final_config_str = json.dumps(merged_config, sort_keys=True)

            if initial_config_str != final_config_str:
                config_updated = True
                config = merged_config
                print(f"DEBUG: Configuration merged with default values. Updates detected.")
            else:
                config = merged_config

        else:
            print(f"DEBUG: ❌ config.json not found. Creating with default values.")
            config = default_config
            config_updated = True

        if config_updated or not os.path.exists(config_file_path):
            with open(config_file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            print(f"DEBUG: Configuration saved/updated to {config_file_path}")

    except json.JSONDecodeError as e:
        print(f"DEBUG: ❌ Error decoding config.json: {e}. Using default values and recreating file.")
        config = default_config
        with open(config_file_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"DEBUG: Recreated config.json with default values.")
    except Exception as e:
        print(f"DEBUG: ❌ An unexpected error occurred loading config.json: {e}. Using default values and recreating file.")
        config = default_config
        with open(config_file_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"DEBUG: Recreated config.json with default values due to unexpected error.")
    
    return config

def save_config(config_data):
    config_file_path = os.path.join(os.path.dirname(__file__), 'config.json')
    try:
        with open(config_file_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        print(f"DEBUG: ✅ Configuration saved to {config_file_path}")
        st.sidebar.success("Settings saved successfully!")
    except Exception as e:
        print(f"DEBUG: ❌ Error saving config.json: {e}")
        st.sidebar.error(f"Error saving settings: {e}")

# --- Function to save usage data to SQLite ---
def save_usage_to_db(timestamp, cpu, ram, disk, battery_percent):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO usage_data (timestamp, cpu, ram, disk, battery)
            VALUES (?, ?, ?, ?, ?)
        ''', (timestamp, cpu, ram, disk, battery_percent))
        conn.commit()
    except sqlite3.IntegrityError:
        print(f"DEBUG: Timestamp {timestamp} already exists in DB. Skipping insert.")
    except Exception as e:
        print(f"DEBUG: Error saving data to DB: {e}")
    finally:
        conn.close()

# --- Function to read usage data from SQLite for Trend Analysis and Prediction ---
def read_usage_data_from_db(lookback_period_minutes):
    conn = sqlite3.connect(DB_PATH)
    query_start_time = datetime.now() - timedelta(minutes=lookback_period_minutes)
    data = []
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT timestamp, cpu, ram, disk, battery FROM usage_data WHERE timestamp >= ? ORDER BY timestamp ASC", (query_start_time.strftime("%Y-%m-%d %H:%M:%S"),))
        rows = cursor.fetchall()
        for row in rows:
            data.append({
                'timestamp': datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S"),
                'cpu': row[1],
                'ram': row[2],
                'disk': row[3],
                'battery': row[4]
            })
    except Exception as e:
        print(f"DEBUG: Error reading data from DB for trend/prediction: {e}")
    finally:
        conn.close()
    return data

# --- Function to read ALL usage data from SQLite for Historical Chart and Analysis ---
def read_all_usage_data_from_db():
    conn = sqlite3.connect(DB_PATH)
    df = pd.DataFrame()
    try:
        df = pd.read_sql_query("SELECT timestamp, cpu, ram, disk, battery FROM usage_data ORDER BY timestamp ASC", conn)
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
    except Exception as e:
        print(f"DEBUG: Error reading all usage data from DB: {e}")
        df = pd.DataFrame()
    finally:
        conn.close()
    return df

# --- Function to analyze trend ---
def analyze_trend(data_points, resource_name, min_increase_percent):
    if len(data_points) < 2:
        return None

    values = [dp[resource_name] for dp in data_points if isinstance(dp[resource_name], (int, float))]
    
    if not values or len(values) < 2:
        return None

    start_value = values[0]
    end_value = values[-1]

    if start_value == 0:
        if end_value > 0 and end_value > min_increase_percent:
            return f"({resource_name.upper()} usage significantly increased from 0% to {end_value:.1f}%)"
        return None
        
    increase_percentage = ((end_value - start_value) / start_value) * 100
    
    if increase_percentage >= min_increase_percent:
        return f"({resource_name.upper()} usage increased by {increase_percentage:.1f}% from {start_value:.1f}% to {end_value:.1f}%)"
    
    return None

# --- Function to train and predict using selected ML model ---
# This function is now cached with Streamlit's @st.cache_data decorator
# It will only re-run if its inputs change, which helps performance
#@st.cache_data(ttl=300) # Cache for 5 minutes by default, can be cleared manually
def train_and_predict(data_points, resource_name, model_type="Linear Regression"):
    # Add a print statement to indicate when retraining happens
    print(f"DEBUG: Retraining ML model for {resource_name} using {model_type}...")
    
    if len(data_points) < 10: 
        return None, "Not enough data (min 10 points recommended)" 

    valid_data_points = []
    for dp in data_points:
        if isinstance(dp[resource_name], (int, float)):
            valid_data_points.append(dp)
    
    if len(valid_data_points) < 10:
        return None, "Not enough valid numeric data (min 10 points recommended)"

    time_series = pd.Series(
        [dp[resource_name] for dp in valid_data_points],
        index=[dp['timestamp'] for dp in valid_data_points]
    )

    prediction = None
    evaluation_metric = "N/A"

    try:
        if model_type == "Linear Regression":
            X = np.array(range(len(time_series))).reshape(-1, 1)
            y = time_series.values
            model = LinearRegression()
            model.fit(X, y)
            prediction = model.predict(np.array([[len(time_series)]]))[0]
            y_pred = model.predict(X)
            mse = mean_squared_error(y, y_pred)
            r2 = r2_score(y, y_pred)
            evaluation_metric = f"MSE: {mse:.2f}, R2: {r2:.2f}"
            
        elif model_type == "Random Forest":
            X = np.array(range(len(time_series))).reshape(-1, 1)
            y = time_series.values
            model = RandomForestRegressor(n_estimators=10, random_state=42)
            model.fit(X, y)
            prediction = model.predict(np.array([[len(time_series)]]))[0]
            y_pred = model.predict(X)
            mse = mean_squared_error(y, y_pred)
            r2 = r2_score(y, y_pred)
            evaluation_metric = f"MSE: {mse:.2f}, R2: {r2:.2f}"
            
        elif model_type == "ARIMA":
            if len(time_series) < 15 or time_series.var() == 0:
                return None, "Not enough data or no variance for ARIMA (min 15 points, non-zero variance recommended)"
            
            # Ensure time series index is suitable for ARIMA (datetime index)
            time_series.index = pd.to_datetime(time_series.index)
            model = sm_arima.ARIMA(time_series, order=(1,1,0)) 
            model_fit = model.fit()
            
            # Forecast the next point after the last timestamp
            last_timestamp = time_series.index[-1]
            future_timestamp = last_timestamp + pd.Timedelta(seconds=config['update_interval']) # Predict for the next update interval
            
            # Predict only one step into the future
            prediction = model_fit.predict(start=future_timestamp, end=future_timestamp)[0]
            evaluation_metric = f"ARIMA AIC: {model_fit.aic:.2f}"
            
        else:
            return None, "Unknown Model Type"

        prediction = max(0.0, prediction)
        prediction = min(100.0, prediction)
        
        return prediction, evaluation_metric
    
    except Exception as e:
        print(f"DEBUG: Error training/predicting with {model_type}: {e}")
        return None, f"Error: {e}"

# Load config when app starts
config = load_config()

# Set Threshold and LINE Settings from config
CPU_LIMIT = config['thresholds']['cpu_limit']
RAM_LIMIT = config['thresholds']['ram_limit']
DISK_LIMIT = config['thresholds']['disk_limit']
BATTERY_LOW_LIMIT = config['thresholds']['battery_low_limit'] 
LINE_WEBHOOK_URL = config['alert_settings']['line_webhook_url']
LINE_TARGET_USER_ID = config['alert_settings']['line_target_user_id']

# Trend Analysis Settings
LOOKBACK_MINUTES = config['trend_analysis_settings']['lookback_minutes']
MIN_INCREASE_PERCENT = config['trend_analysis_settings']['min_increase_percent']

# Prediction Analysis Settings
PREDICTION_LOOKBACK_MINUTES = config['prediction_settings']['prediction_lookback_minutes']
PREDICTION_ALERT_THRESHOLD_FACTOR = config['prediction_settings']['prediction_alert_threshold_factor']
PREDICTION_MODEL = config['prediction_settings']['prediction_model']
PREDICTION_RETRAIN_INTERVAL_MINUTES = config['prediction_settings']['prediction_retrain_interval_minutes']


# --- Helper function for custom metric cards ---
def create_metric_card_html(label: str, value: float | str, limit: float, warning_factor: float = 0.8, is_battery: bool = False):
    """
    Generates HTML string for a custom metric card with dynamic background color based on value.
    
    Args:
        label (str): The label for the metric (e.g., "CPU (%)").
        value (float | str): The current value of the metric. Can be "N/A" for battery.
        limit (float): The threshold limit for the metric.
        warning_factor (float): Factor to determine warning threshold (e.g., 0.8 for 80% of limit).
        is_battery (bool): True if this is the battery metric (low value is bad).
    
    Returns:
        str: HTML string for the metric card.
    """
    color_class = "metric-card-normal"
    
    if not isinstance(value, (int, float)): # Handle "N/A" for battery or other non-numeric values
        color_class = "metric-card-normal" # Default to normal if not a number
    elif is_battery:
        # For battery, warning/danger is when value is *below* a threshold
        if value < limit: # Battery below limit is danger
            color_class = "metric-card-danger"
        elif value < (limit + (100 - limit) * 0.2): # Warning for a 20% band above the low limit
            color_class = "metric-card-warning"
        else: # Normal: battery above warning threshold
            color_class = "metric-card-normal"

    else: # For CPU, RAM, Disk (high value is bad)
        if value > limit: # Above limit is danger
            color_class = "metric-card-danger"
        elif value > limit * warning_factor: # Above limit * factor is warning
            color_class = "metric-card-warning"
        else: # Normal: below warning threshold
            color_class = "metric-card-normal"

    formatted_value = f"{value:.1f}%" if isinstance(value, (int, float)) else str(value)

    return f"""
    <div class="{color_class} metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{formatted_value}</div>
    </div>
    """

# --- Helper function for custom alert log entries ---
def create_alert_log_entry_html(message: str, timestamp: str, alert_type: str = 'info'):
    """
    Generates HTML for an alert log entry with specific styling based on type.
    """
    icon = "ℹ️"
    type_class = "alert-entry-info"

    if alert_type == 'warning':
        icon = "⚠️"
        type_class = "alert-entry-warning"
    elif alert_type == 'danger':
        icon = "🚨"
        type_class = "alert-entry-danger"
    
    return f"""
    <div class="alert-entry {type_class}">
        <div class="text-xl">{icon}</div>
        <div>
            <p class="font-semibold">{message}</p>
            <p class="text-sm opacity-80">{timestamp}</p>
        </div>
    </div>
    """

# --- UI section for settings in Sidebar ---
st.sidebar.header("⚙️ System Monitoring Settings")

# Dark Mode Toggle in Sidebar
# Changed the key for the checkbox to ensure it doesn't conflict during reruns.
dark_mode_checkbox = st.sidebar.checkbox("เปิดโหมดกลางคืน", value=st.session_state.dark_mode, key="dark_mode_toggle_sidebar")
if dark_mode_checkbox != st.session_state.dark_mode:
    st.session_state.dark_mode = dark_mode_checkbox
    st.rerun() # Rerun to apply changes, as st.session_state has changed

# Apply dynamic CSS class based on dark mode state
current_container_class = "theme-container" 
current_card_class = "theme-card" # This class is for general cards/sections, not individual metrics anymore


with st.sidebar.form(key='threshold_form'):
    st.subheader("ตั้งค่าขีดจำกัด (%)")
    new_cpu_limit = st.slider("CPU Limit", 0, 100, CPU_LIMIT, key="cpu_slider")
    new_ram_limit = st.slider("RAM Limit", 0, 100, RAM_LIMIT, key="ram_slider")
    new_disk_limit = st.slider("Disk Limit", 0, 100, DISK_LIMIT, key="disk_slider")
    new_battery_low_limit = st.slider("Battery Low Limit (%)", 0, 100, BATTERY_LOW_LIMIT, key="battery_low_slider") 
    
    st.subheader("LINE Alert Settings")
    new_line_webhook_url = st.text_input("LINE Webhook URL", LINE_WEBHOOK_URL, key="webhook_input")
    new_line_target_user_id = st.text_input("LINE Target User ID", LINE_TARGET_USER_ID, key="userid_input")

    st.subheader("Trend Analysis Settings")
    new_lookback_minutes = st.slider("Lookback Minutes for Trend", 1, 60, LOOKBACK_MINUTES, key="lookback_slider")
    new_min_increase_percent = st.slider("Min Increase % for Trend Alert", 1, 100, MIN_INCREASE_PERCENT, key="min_increase_slider")

    st.subheader("Prediction Settings (ML)")
    new_prediction_lookback_minutes = st.slider("Prediction Lookback Minutes", 1, 60, PREDICTION_LOOKBACK_MINUTES, key="pred_lookback_slider")
    new_prediction_alert_threshold_factor = st.slider("Prediction Alert Factor (x Normal Limit)", 1.0, 2.0, PREDICTION_ALERT_THRESHOLD_FACTOR, step=0.05, key="pred_alert_factor_slider")
    
    new_prediction_model = st.selectbox(
        "เลือกโมเดลการทำนาย", 
        ("Linear Regression", "Random Forest", "ARIMA"), 
        index=["Linear Regression", "Random Forest", "ARIMA"].index(PREDICTION_MODEL),
        key="pred_model_selector"
    )
    new_prediction_retrain_interval_minutes = st.slider("ML Retrain Interval (Minutes)", 1, 60, PREDICTION_RETRAIN_INTERVAL_MINUTES, key="pred_retrain_interval_slider")

    submit_button = st.form_submit_button(label='บันทึกการตั้งค่า')

    if submit_button:
        config['thresholds']['cpu_limit'] = new_cpu_limit
        config['thresholds']['ram_limit'] = new_ram_limit
        config['thresholds']['disk_limit'] = new_disk_limit
        config['thresholds']['battery_low_limit'] = new_battery_low_limit 
        config['alert_settings']['line_webhook_url'] = new_line_webhook_url
        config['alert_settings']['line_target_user_id'] = new_line_target_user_id
        config['trend_analysis_settings']['lookback_minutes'] = new_lookback_minutes
        config['trend_analysis_settings']['min_increase_percent'] = new_min_increase_percent
        config['prediction_settings']['prediction_lookback_minutes'] = new_prediction_lookback_minutes
        config['prediction_settings']['prediction_alert_threshold_factor'] = new_prediction_alert_threshold_factor
        config['prediction_settings']['prediction_model'] = new_prediction_model 
        config['prediction_settings']['prediction_retrain_interval_minutes'] = new_prediction_retrain_interval_minutes
        
        save_config(config)
        
        st.sidebar.info("โปรดรีสตาร์ทการ Monitoring (เอาเครื่องหมายออกแล้วติ๊กใหม่) หรือรันแอปใหม่เพื่อให้การตั้งค่ามีผลสมบูรณ์.")
        
        CPU_LIMIT = new_cpu_limit
        RAM_LIMIT = new_ram_limit
        DISK_LIMIT = new_disk_limit
        BATTERY_LOW_LIMIT = new_battery_low_limit 
        LINE_WEBHOOK_URL = new_line_webhook_url
        LINE_TARGET_USER_ID = new_line_target_user_id
        LOOKBACK_MINUTES = new_lookback_minutes
        MIN_INCREASE_PERCENT = new_min_increase_percent
        PREDICTION_LOOKBACK_MINUTES = new_prediction_lookback_minutes
        PREDICTION_ALERT_THRESHOLD_FACTOR = new_prediction_alert_threshold_factor
        PREDICTION_MODEL = new_prediction_model
        PREDICTION_RETRAIN_INTERVAL_MINUTES = new_prediction_retrain_interval_minutes # Update the global variable

# --- Main display section ---
# Use a spinner while the main loop runs
with st.spinner('กำลังโหลดข้อมูลและประมวลผล...'):
    # Wrap main content in a container with dynamic class for theme
    st.markdown(f'<div class="{current_container_class} p-6">', unsafe_allow_html=True) 

    st.subheader("ภาพรวมการใช้งานปัจจุบัน")
    current_usage_cols = st.columns(4)

    # Placeholders for custom metric cards. The actual content will be updated inside the loop
    cpu_metric_placeholder = current_usage_cols[0].empty()
    ram_metric_placeholder = current_usage_cols[1].empty()
    disk_metric_placeholder = current_usage_cols[2].empty()
    battery_metric_placeholder = current_usage_cols[3].empty()

    st.markdown("</div>", unsafe_allow_html=True) # Close the first container

    # Wrap the next section in a new container
    st.markdown(f'<div class="{current_container_class} p-6">', unsafe_allow_html=True)
    st.subheader("กราฟการใช้งานปัจจุบัน (30 วินาทีล่าสุด)")
    realtime_chart_placeholder = st.empty()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(f'<div class="{current_container_class} p-6">', unsafe_allow_html=True)
    st.subheader("กราฟประวัติการใช้งาน")
    historical_chart_placeholder = st.empty()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(f'<div class="{current_container_class} p-6">', unsafe_allow_html=True)
    st.subheader("การคาดการณ์การใช้งาน (จาก Machine Learning)")
    prediction_cols = st.columns(3)
    prediction_eval_cols = st.columns(3) # This will hold the evaluation captions
    prediction_status_placeholder = st.empty() # Placeholder for ML retraining status
    st.markdown("</div>", unsafe_allow_html=True)


    st.markdown(f'<div class="{current_container_class} p-6">', unsafe_allow_html=True)
    st.subheader("การวิเคราะห์ข้อมูลเชิงลึก (จาก Log File)")
    analysis_metric_cols = st.columns(3)
    analysis_detail_cols = st.columns(3)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(f'<div class="{current_container_class} p-6">', unsafe_allow_html=True)
    st.subheader("ประวัติการแจ้งเตือน")
    alert_history_placeholder = st.empty() # Placeholder for alert history text_area

    # Clear Alert History Button
    clear_button_col, _ = st.columns([0.2, 0.8])
    with clear_button_col:
        if st.button("ล้างประวัติการแจ้งเตือน"):
            st.session_state.alert_log = []
            st.info("ประวัติการแจ้งเตือนถูกล้างแล้ว.")
            # Re-render empty log or placeholder
            alert_history_placeholder.markdown(
                f'<div style="max-height: 250px; overflow-y: auto; padding-right: 15px;">' + 
                '<div class="text-center text-slate-500 py-8">ยังไม่มีการแจ้งเตือน...</div>' +
                '</div>', 
                unsafe_allow_html=True
            )
    st.markdown("</div>", unsafe_allow_html=True) # Close the last container


    monitoring = st.checkbox("เริ่ม Monitoring", value=True)

    # Add a check to only open browser the first time the app runs
    # This prevents the browser from re-opening every time Streamlit reruns

    if not monitoring:
        st.info(f"Monitoring is off. Current limits: CPU={CPU_LIMIT}%, RAM={RAM_LIMIT}%, Disk={DISK_LIMIT}%, Battery Low={BATTERY_LOW_LIMIT}%. ML Retrain Interval: {PREDICTION_RETRAIN_INTERVAL_MINUTES} minutes.") 

    while monitoring:
        current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cpu = psutil.cpu_percent(interval=1) 
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        battery = psutil.sensors_battery()
        battery_percent = battery.percent if battery else "N/A"

        # Save current usage data to SQLite DB
        save_usage_to_db(current_timestamp, cpu, ram, disk, battery_percent)

        # Update custom metric cards with dynamic colors
        cpu_metric_placeholder.markdown(create_metric_card_html("🖥️ CPU (%)", cpu, CPU_LIMIT, warning_factor=0.8), unsafe_allow_html=True)
        ram_metric_placeholder.markdown(create_metric_card_html("🧠 RAM (%)", ram, RAM_LIMIT, warning_factor=0.8), unsafe_allow_html=True)
        disk_metric_placeholder.markdown(create_metric_card_html("💽 Disk (%)", disk, DISK_LIMIT, warning_factor=0.8), unsafe_allow_html=True)
        # Call create_metric_card_html with is_battery=True for correct logic
        battery_metric_placeholder.markdown(create_metric_card_html("🔋 Battery (%)", battery_percent, BATTERY_LOW_LIMIT, warning_factor=2.0, is_battery=True), unsafe_allow_html=True) 


        if 'realtime_cpu_data' not in st.session_state:
            st.session_state.realtime_cpu_data = []
            st.session_state.realtime_ram_data = []
            st.session_state.realtime_disk_data = []
            st.session_state.realtime_labels = []

        st.session_state.realtime_cpu_data.append(cpu)
        st.session_state.realtime_ram_data.append(ram)
        st.session_state.realtime_disk_data.append(disk)
        st.session_state.realtime_labels.append(datetime.now().strftime("%H:%M:%S"))

        MAX_REALTIME_POINTS = 30
        if len(st.session_state.realtime_labels) > MAX_REALTIME_POINTS:
            st.session_state.realtime_labels.pop(0)
            st.session_state.realtime_cpu_data.pop(0)
            st.session_state.realtime_ram_data.pop(0)
            st.session_state.realtime_disk_data.pop(0)
        
        realtime_chart_data = pd.DataFrame({
            'Time': st.session_state.realtime_labels,
            'CPU': st.session_state.realtime_cpu_data,
            'RAM': st.session_state.realtime_ram_data,
            'Disk': st.session_state.realtime_disk_data
        }).set_index('Time')
        realtime_chart_placeholder.line_chart(realtime_chart_data)


        # Read historical data from SQLite DB
        historical_df = read_all_usage_data_from_db()
        if not historical_df.empty:
            historical_df_numeric = historical_df[['cpu', 'ram', 'disk']]
            historical_chart_placeholder.line_chart(historical_df_numeric)

            # Data Analysis Section - Averages
            # For average metrics, use the general create_metric_card_html but with normal background
            analysis_metric_cols[0].markdown(create_metric_card_html("CPU เฉลี่ย", historical_df['cpu'].mean(), CPU_LIMIT, warning_factor=0.8), unsafe_allow_html=True)
            analysis_metric_cols[1].markdown(create_metric_card_html("RAM เฉลี่ย", historical_df['ram'].mean(), RAM_LIMIT, warning_factor=0.8), unsafe_allow_html=True)
            analysis_metric_cols[2].markdown(create_metric_card_html("Disk เฉลี่ย", historical_df['disk'].mean(), DISK_LIMIT, warning_factor=0.8), unsafe_allow_html=True)
            

            # Data Analysis Section - Min/Max/Std Dev
            analysis_detail_cols[0].caption(f"**CPU Min:** {historical_df['cpu'].min():.1f}%")
            analysis_detail_cols[0].caption(f"**CPU Max:** {historical_df['cpu'].max():.1f}%")
            analysis_detail_cols[0].caption(f"**CPU Std Dev:** {historical_df['cpu'].std():.1f}%")

            analysis_detail_cols[1].caption(f"**RAM Min:** {historical_df['ram'].min():.1f}%")
            analysis_detail_cols[1].caption(f"**RAM Max:** {historical_df['ram'].max():.1f}%")
            analysis_detail_cols[1].caption(f"**RAM Std Dev:** {historical_df['ram'].std():.1f}%")

            analysis_detail_cols[2].caption(f"**Disk Min:** {historical_df['disk'].min():.1f}%")
            analysis_detail_cols[2].caption(f"**Disk Max:** {historical_df['disk'].max():.1f}%")
            analysis_detail_cols[2].caption(f"**Disk Std Dev:** {historical_df['disk'].std():.1f}%")

        else: # This 'else' correctly belongs to the 'if not historical_df.empty:'
            historical_chart_placeholder.info("No historical data available yet. Please wait for data collection.")
            analysis_metric_cols[0].info("CPU เฉลี่ย: ไม่มีข้อมูล")
            analysis_metric_cols[1].info("RAM เฉลี่ย: ไม่มีข้อมูล")
            analysis_metric_cols[2].info("Disk เฉลี่ย: ไม่มีข้อมูล")
            analysis_detail_cols[0].caption("CPU Min/Max/Std: N/A")
            analysis_detail_cols[1].caption("RAM Min/Max/Std: N/A")
            analysis_detail_cols[2].caption("Disk Min/Max/Std: N/A")


        # --- Perform Predictions and Display ---
        predicted_cpu, eval_cpu = None, None
        predicted_ram, eval_ram = None, None
        predicted_disk, eval_disk = None, None

        # Logic to only retrain ML models based on interval
        current_time_dt = datetime.now() # Use a different variable name to avoid conflict with current_time string
        if (current_time_dt - st.session_state.last_ml_retrain_time).total_seconds() >= PREDICTION_RETRAIN_INTERVAL_MINUTES * 60:
            prediction_status_placeholder.info("กำลังเทรนโมเดล ML... (อาจใช้เวลาสักครู่)")
            # Get recent data for prediction
            recent_data_for_prediction = read_usage_data_from_db(PREDICTION_LOOKBACK_MINUTES)

            if len(recent_data_for_prediction) >= (15 if PREDICTION_MODEL == "ARIMA" else 10): 
                predicted_cpu, eval_cpu = train_and_predict(recent_data_for_prediction, 'cpu', PREDICTION_MODEL)
                predicted_ram, eval_ram = train_and_predict(recent_data_for_prediction, 'ram', PREDICTION_MODEL)
                predicted_disk, eval_disk = train_and_predict(recent_data_for_prediction, 'disk', PREDICTION_MODEL)
            
            st.session_state.last_ml_retrain_time = current_time_dt # Update last retrain time
            prediction_status_placeholder.empty() # Clear the status message

        # Display last known predictions (even if not just retrained)
        prediction_cols[0].markdown(create_metric_card_html("🖥️ CPU (คาดการณ์)", predicted_cpu, CPU_LIMIT, warning_factor=0.8), unsafe_allow_html=True)
        prediction_eval_cols[0].caption(f"Eval: {eval_cpu}" if predicted_cpu is not None else "Eval: N/A")

        prediction_cols[1].markdown(create_metric_card_html("🧠 RAM (คาดการณ์)", predicted_ram, RAM_LIMIT, warning_factor=0.8), unsafe_allow_html=True)
        prediction_eval_cols[1].caption(f"Eval: {eval_ram}" if predicted_ram is not None else "Eval: N/A")

        prediction_cols[2].markdown(create_metric_card_html("💽 Disk (คาดการณ์)", predicted_disk, DISK_LIMIT, warning_factor=0.8), unsafe_allow_html=True)
        prediction_eval_cols[2].caption(f"Eval: {eval_disk}" if predicted_disk is not None else "Eval: N/A")


        # --- Section for detecting and sending LINE alerts ---
        current_line_alert_messages = [] # For LINE notification payload (list of strings)
        current_ui_alert_entries = [] # For Streamlit UI display (list of dicts)

        # Threshold Alerts
        # CPU
        if cpu > CPU_LIMIT:
            if not st.session_state.alert_sent_cpu_threshold:
                alert_msg = f"🖥️ CPU usage is high: {cpu:.1f}% (Limit: {CPU_LIMIT}%)"
                current_line_alert_messages.append(alert_msg)
                current_ui_alert_entries.append({"message": alert_msg, "type": "danger"})
                st.session_state.alert_sent_cpu_threshold = True
        else:
            st.session_state.alert_sent_cpu_threshold = False

        # RAM
        if ram > RAM_LIMIT:
            if not st.session_state.alert_sent_ram_threshold:
                alert_msg = f"🧠 RAM usage is high: {ram:.1f}% (Limit: {RAM_LIMIT}%)"
                current_line_alert_messages.append(alert_msg)
                current_ui_alert_entries.append({"message": alert_msg, "type": "danger"})
                st.session_state.alert_sent_ram_threshold = True
        else:
            st.session_state.alert_sent_ram_threshold = False

        # Disk
        if disk > DISK_LIMIT:
            if not st.session_state.alert_sent_disk_threshold:
                alert_msg = f"💽 Disk usage is high: {disk:.1f}% (Limit: {DISK_LIMIT}%)"
                current_line_alert_messages.append(alert_msg)
                current_ui_alert_entries.append({"message": alert_msg, "type": "danger"})
                st.session_state.alert_sent_disk_threshold = True
        else:
            st.session_state.alert_sent_disk_threshold = False

        # Battery Alert
        if isinstance(battery_percent, (int, float)) and battery_percent < BATTERY_LOW_LIMIT:
            if not st.session_state.alert_sent_battery_threshold:
                alert_msg = f"🔋 Battery level is low: {battery_percent:.1f}% (Limit: {BATTERY_LOW_LIMIT}%)"
                current_line_alert_messages.append(alert_msg)
                current_ui_alert_entries.append({"message": alert_msg, "type": "danger"}) # Battery low is critical
                st.session_state.alert_sent_battery_threshold = True 
        elif isinstance(battery_percent, (int, float)) and battery_percent >= BATTERY_LOW_LIMIT:
            st.session_state.alert_sent_battery_threshold = False


        # Trend Alerts
        recent_data_for_trend = read_usage_data_from_db(LOOKBACK_MINUTES)
        
        cpu_trend_alert = analyze_trend(recent_data_for_trend, 'cpu', MIN_INCREASE_PERCENT)
        if cpu_trend_alert and not st.session_state.alert_sent_cpu_trend:
            alert_msg = f"📈 CPU usage trend detected {cpu_trend_alert}"
            current_line_alert_messages.append(alert_msg)
            current_ui_alert_entries.append({"message": alert_msg, "type": "warning"})
            st.session_state.alert_sent_cpu_trend = True
        elif not cpu_trend_alert:
            st.session_state.alert_sent_cpu_trend = False

        ram_trend_alert = analyze_trend(recent_data_for_trend, 'ram', MIN_INCREASE_PERCENT)
        if ram_trend_alert and not st.session_state.alert_sent_ram_trend:
            alert_msg = f"📈 RAM usage trend detected {ram_trend_alert}"
            current_line_alert_messages.append(alert_msg)
            current_ui_alert_entries.append({"message": alert_msg, "type": "warning"})
            st.session_state.alert_sent_ram_trend = True 
        elif not ram_trend_alert:
            st.session_state.alert_sent_ram_trend = False

        disk_trend_alert = analyze_trend(recent_data_for_trend, 'disk', MIN_INCREASE_PERCENT)
        if disk_trend_alert and not st.session_state.alert_sent_disk_trend:
            alert_msg = f"📈 Disk usage trend detected {disk_trend_alert}"
            current_line_alert_messages.append(alert_msg)
            current_ui_alert_entries.append({"message": alert_msg, "type": "warning"})
            st.session_state.alert_sent_disk_trend = True
        elif not disk_trend_alert:
            st.session_state.alert_sent_disk_trend = False

        # Prediction Alerts (now run only when ML models are retrained)
        # Note: predicted_cpu, predicted_ram, predicted_disk are set when the ML models are retrained
        # We assume their values persist through Streamlit reruns
        if predicted_cpu is not None: # Check if prediction was made
            prediction_alert_cpu_limit = CPU_LIMIT * PREDICTION_ALERT_THRESHOLD_FACTOR
            if predicted_cpu > prediction_alert_cpu_limit:
                if not st.session_state.alert_sent_cpu_prediction:
                    alert_msg = f"🔮 CPU (ML) คาดการณ์สูง: {predicted_cpu:.1f}% (เกิน {prediction_alert_cpu_limit:.1f}%)"
                    current_line_alert_messages.append(alert_msg)
                    current_ui_alert_entries.append({"message": alert_msg, "type": "warning"})
                    st.session_state.alert_sent_cpu_prediction = True
            else:
                st.session_state.alert_sent_cpu_prediction = False

        if predicted_ram is not None:
            prediction_alert_ram_limit = RAM_LIMIT * PREDICTION_ALERT_THRESHOLD_FACTOR
            if predicted_ram > prediction_alert_ram_limit:
                if not st.session_state.alert_sent_ram_prediction:
                    alert_msg = f"🔮 RAM (ML) คาดการณ์สูง: {predicted_ram:.1f}% (เกิน {prediction_alert_ram_limit:.1f}%)"
                    current_line_alert_messages.append(alert_msg)
                    current_ui_alert_entries.append({"message": alert_msg, "type": "warning"})
                    st.session_state.alert_sent_ram_prediction = True
            else:
                st.session_state.alert_sent_ram_prediction = False

        if predicted_disk is not None:
            prediction_alert_disk_limit = DISK_LIMIT * PREDICTION_ALERT_THRESHOLD_FACTOR
            if predicted_disk > prediction_alert_disk_limit:
                if not st.session_state.alert_sent_disk_prediction:
                    alert_msg = f"🔮 Disk (ML) คาดการณ์สูง: {predicted_disk:.1f}% (เกิน {prediction_alert_disk_limit:.1f}%)"
                    current_line_alert_messages.append(alert_msg)
                    current_ui_alert_entries.append({"message": alert_msg, "type": "warning"})
                    st.session_state.alert_sent_disk_prediction = True
            else:
                st.session_state.alert_sent_disk_prediction = False


        # Send LINE alert (consolidated message)
        if current_line_alert_messages:
            full_line_alert_message = f"🚨 PreBreak Alert ({current_timestamp}):\n" + "\n".join(current_line_alert_messages)

            payload = {
                "message": full_line_alert_message,
                "userId": LINE_TARGET_USER_ID
            }
            headers = {'Content-Type': 'application/json'}

            try:
                response = requests.post(LINE_WEBHOOK_URL, data=json.dumps(payload), headers=headers)
                response.raise_for_status()
                print(f"[{current_timestamp}] Alert sent to LINE: {full_line_alert_message}")
            except requests.exceptions.RequestException as e:
                print(f"[{current_timestamp}] Error sending alert to LINE: {e}")

        # Update UI Alert Log
        if current_ui_alert_entries:
            for entry in current_ui_alert_entries:
                st.session_state.alert_log.insert(0, { # Insert at beginning to show latest first
                    "timestamp": current_timestamp,
                    "message": entry["message"],
                    "type": entry["type"]
                })
            st.session_state.alert_log = st.session_state.alert_log[:10] # Keep only last 10


        alert_log_html_list = []
        if not st.session_state.alert_log:
            alert_log_html_list.append('<div class="text-center text-slate-500 py-8">ยังไม่มีการแจ้งเตือน...</div>')
        else:
            for entry in st.session_state.alert_log: 
                alert_log_html_list.append(create_alert_log_entry_html(
                    entry["message"], 
                    entry["timestamp"], 
                    entry["type"]
                ))

        # Display the alert log in a scrollable area.
        alert_history_placeholder.markdown(
            f'<div style="max-height: 250px; overflow-y: auto; padding-right: 15px;">' + 
            "".join(alert_log_html_list) + 
            '</div>', 
            unsafe_allow_html=True
        )

        time.sleep(config.get('update_interval', 2)) # Use update_interval from config

        if not monitoring:
            st.stop()

# Add a check to only open browser the first time the app runs
# This prevents the browser from re-opening every time Streamlit reruns
# Also added a check if the app is already being served (e.g. via streamlit run)

