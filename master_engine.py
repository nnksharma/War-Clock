import feedparser
import requests
import json
import time
import os 
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
from google import genai
from google.genai import types

# --- CONFIGURATION & CONSTANTS ---
ALPHA_VANTAGE_KEY = os.environ.get('ALPHA_VANTAGE_KEY')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

ALPHA_KINETIC = 0.5       
BETA_INFRA = 10.0         
GAMMA_EXPANSION = 45.0    
LAMBDA_INTERVENTION = 15.0 
LAMBDA_ECONOMY = 16.0      
MAX_OIL_PRICE = 150.0     

# --- UTILITY FUNCTIONS ---
def calculate_damping(T):
    return (4 * T * (720 - T)) / (720 ** 2)

def format_time(minutes):
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    if hours == 0: hours = 12
    return f"{hours}:{mins:02d}"

# --- SENSORS (Phase 2) ---
def get_live_oil_price(last_known_price):
    print("🌐 Connecting to Global Energy Feed (OilPrice.com)...")
    url = "https://oilprice.com/oil-price-charts/"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # We look for the 'Brent Crude' label in the table
            # Using 'string' instead of 'text' to keep it modern
            brent_label = soup.find(string="Brent Crude")
            
            if brent_label:
                # Find the next <td> which contains the price
                price_text = brent_label.find_next('td').text.strip()
                live_price = float(price_text.replace(",", ""))
                print(f"✅ Scraper Success! Brent Crude: ${live_price:.2f}")
                return live_price
                
        print(f"⚠️ Site reached but returned Status {response.status_code}")
    except Exception as e:
        print(f"⚠️ Scraping Error: {e}")
        
    print(f"🔄 Using Fallback Price: ${last_known_price}")
    return last_known_price

def harvest_latest_news():
    RSS_URLS = [
        "http://feeds.bbci.co.uk/news/world/middle_east/rss.xml", 
        "https://www.aljazeera.com/xml/rss/all.xml",
        "https://www.yahoo.com/news/rss/world",
        "http://rss.cnn.com/rss/edition_world.rss",
        "https://www.theguardian.com/world/middleeast/rss"
    ]
    
    # Corrected time window logic for 'from datetime import datetime, timezone, timedelta'
    cutoff_window = datetime.now(timezone.utc) - timedelta(hours=3)
    fresh_headlines = []
    
    memory_file = 'seen_news.json'
    seen_ids = set()
    if os.path.exists(memory_file):
        try:
            with open(memory_file, 'r') as f:
                seen_ids = set(json.load(f))
        except:
            seen_ids = set()

    current_run_ids = []

    for url in RSS_URLS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                guid = entry.get('id') or entry.get('link')
                
                try:
                    # Convert article time using time.mktime
                    article_time = datetime.fromtimestamp(time.mktime(entry.published_parsed), timezone.utc)
                    
                    if article_time > cutoff_window and guid not in seen_ids:
                        fresh_headlines.append(entry.title)
                        current_run_ids.append(guid)
                except:
                    continue
        except Exception as e:
            print(f"⚠️ Feed Error ({url}): {e}")
            continue
    
    updated_memory = list(seen_ids.union(current_run_ids))
    with open(memory_file, 'w') as f:
        json.dump(updated_memory[-200:], f) 
            
    print(f"📡 Memory Check: {len(fresh_headlines)} NEW headlines captured.")
    return list(set(fresh_headlines))
      
# --- THE LLM BRAIN (Phase 3) ---
def get_ai_analysis(headlines):
    if not headlines:
        return {"kinetic_events": 0, "infrastructure_sites": 0, "new_state_actors": 0, "international_treaties": 0}
        
    if not GEMINI_API_KEY:
        print("⚠️ No Gemini API Key found in environment. Returning zeros.")
        return {"kinetic_events": 0, "infrastructure_sites": 0, "new_state_actors": 0, "international_treaties": 0}
        
    client = genai.Client(api_key=GEMINI_API_KEY)
    system_instruction = """
    You are a strictly objective geopolitical data-extraction algorithm. Read the provided list of news headlines from the last 6 hours.
    EXPECTED OUTPUT FORMAT (Strict JSON only):
    {
      "kinetic_events": 0,
      "infrastructure_sites": 0,
      "new_state_actors": 0,
      "international_treaties": 0
    }
        Current Baseline: {clock_state['formatted_time']}
        Current Oil: ${clock_state['latest_oil_price']}

        TASK: Analyze the following NEW news headlines from the last 3 hours. 
        Only calculate the 'Delta' (the change). 
        If a kinetic strike happened 5 hours ago, it has already been counted—IGNORE IT. 
        ONLY count strikes or events that appear in this specific list.
    """
    prompt_text = "Headlines:\n" + "\n".join([f"- {h}" for h in headlines])
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_text,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                temperature=0.0
            )
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"⚠️ Gemini API Error: {e}")
        return {"kinetic_events": 0, "infrastructure_sites": 0, "new_state_actors": 0, "international_treaties": 0}

# --- THE MAIN PIPELINE ---
def run_pipeline():
    print("🚀 INITIALIZING RESOLUTION CLOCK PIPELINE...")
    
    # 1. Load Previous State 
    try:
        with open("clock_state.json", "r") as f:
            state = json.load(f)
            current_time_minutes = state["current_minutes"]
            last_oil_price = state.get("latest_oil_price", 82.50) 
    except FileNotFoundError:
        # NEW: The optimistic 7:00 AM start time!
        current_time_minutes = 420.0 
        last_oil_price = 82.50

    print(f"🕒 Starting Position: {format_time(current_time_minutes)} ({current_time_minutes:.2f} mins)")

    # 2. Gather Data
    E_t = get_live_oil_price(last_oil_price)
    headlines = harvest_latest_news()
    print(f"📡 Harvested {len(headlines)} headlines and Brent Crude at ${E_t}")

    # 3. AI Analysis
    ai_data = get_ai_analysis(headlines)
    print(f"🧠 AI Classification: {ai_data}")

    # 4. Math Engine
    phi_E = (ai_data["kinetic_events"] * ALPHA_KINETIC) + \
            (ai_data["infrastructure_sites"] * BETA_INFRA) + \
            (ai_data["new_state_actors"] * GAMMA_EXPANSION)
            
    relief_ratio = (MAX_OIL_PRICE - E_t) / MAX_OIL_PRICE
    phi_D = (ai_data["international_treaties"] * LAMBDA_INTERVENTION) + \
            (relief_ratio * LAMBDA_ECONOMY)

    damping = calculate_damping(current_time_minutes)
    net_flux = phi_D - phi_E
    delta_T = damping * net_flux
    new_time_minutes = max(0, min(720, current_time_minutes + delta_T))

    print(f"🧮 Net Shift: {delta_T:+.2f} mins")
    print(f"🏁 NEW POSITION: {format_time(new_time_minutes)}")

    # 5. Save to JSON
    output_state = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "current_minutes": round(new_time_minutes, 2),
        "formatted_time": format_time(new_time_minutes),
        "last_shift": round(delta_T, 2),
        "latest_oil_price": E_t,
        "ai_readout": ai_data
    }
    
    with open("clock_state.json", "w") as f:
        json.dump(output_state, f, indent=4)
        
    print("💾 Saved to clock_state.json successfully.")

if __name__ == "__main__":
    run_pipeline()
