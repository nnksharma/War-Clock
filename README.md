# दी-War Clock | Geopolitical Resolution Engine 

> "The supreme art of war is to subdue the enemy without fighting." — Sun Tzu

The **दी-War Clock** (a wordplay on the Hindi *दीवार घड़ी* or 'Wall Clock') is an automated, real-time mathematical model designed to track and visualize regional stability in the Middle East. 

##  The Concept
This project treats geopolitical stability as a dynamic system. It utilizes a **State-Space Equation** with parabolic damping to calculate the "time" until resolution or collapse. 

- **12:00 PM (Noon):** Absolute systemic resolution and peace.
- **12:00 AM (Midnight):** Total systemic collapse / Regional escalation.
- **Current Epoch:** Started at 07:00 AM (Optimistic baseline).

##  How it Works
The engine runs every 6 hours via **GitHub Actions** and performs the following:

1. **Economic Sensing:** Fetches live Brent Crude Oil prices as a proxy for market-perceived regional tension.
2. **AI News Analysis:** Scrapes 6-hour windows of global news (BBC, Al Jazeera, etc.) and uses **Google Gemini 2.5 Flash** to classify kinetic events vs. diplomatic interventions.
3. **Mathematical Modeling:** Processes these inputs through a damped flux equation:
   $$D(T) = \frac{4T(720 - T)}{720^2}$$
   This ensures that the clock becomes more "resistant" to change as it approaches either extreme.

##  Tech Stack
- **Backend:** Python 3.10
- **Logic:** State-Space Modeling & Parabolic Damping
- **AI:** Google Gemini API (LLM-based event classification)
- **Automation:** GitHub Actions
- **Frontend:** HTML5/CSS3 (Tactical HUD)

---
**Imagined by @Nayan (PhD Scholar, Sikkim University) with the help of Gemini.**
