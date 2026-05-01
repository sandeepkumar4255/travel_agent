import requests, os, math, re
from dotenv import load_dotenv
from groq import Groq

# ======================
# 🔐 SETUP
# ======================
load_dotenv()

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY")
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ======================
# 🌦 WEATHER
# ======================
def get_weather(city):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
        data = requests.get(url, timeout=5).json()
        return data["main"]["temp"], data["weather"][0]["description"]
    except:
        return "N/A", "Unavailable"

# ======================
# 📍 COORDS
# ======================
def get_coords(city):
    try:
        url = f"https://api.geoapify.com/v1/geocode/search?text={city}&apiKey={GEOAPIFY_API_KEY}"
        data = requests.get(url, timeout=5).json()
        p = data["features"][0]["properties"]
        return p["lat"], p["lon"]
    except:
        return None, None

# ======================
# 📏 DISTANCE
# ======================
def get_distance(src, dest):
    lat1, lon1 = get_coords(src)
    lat2, lon2 = get_coords(dest)

    if not lat1 or not lat2:
        return 0

    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
    return round(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a)), 2)

# ======================
# 🚆 TRANSPORT
# ======================
def get_transport(d):
    if d < 100:
        return "Car/Bike"
    elif d < 1000:
        return "Train"
    else:
        return "Flight (Best)"

# ======================
# 🏨 HOTELS
# ======================
def get_hotels(city):
    try:
        lat, lon = get_coords(city)
        url = f"https://api.geoapify.com/v2/places?categories=accommodation.hotel&filter=circle:{lon},{lat},15000&limit=5&apiKey={GEOAPIFY_API_KEY}"
        data = requests.get(url, timeout=5).json()

        return [
            p["properties"].get("name")
            for p in data.get("features", [])
            if p["properties"].get("name")
        ][:5]

    except:
        return ["No hotels"]

# ======================
# 📚 LOAD KB
# ======================
def load_kb():
    try:
        return open("travel.txt", encoding="utf-8").read().lower().split("\n")
    except:
        return []

# ======================
# 🔍 RETRIEVE CONTEXT
# ======================
def retrieve_context(temp, weather, kb):
    context = []

    for line in kb:
        if isinstance(temp, (int, float)):
            if temp > 35 and "[weather][heat]" in line:
                context.append(line)
            elif temp < 20 and "[weather][cold]" in line:
                context.append(line)
            elif 20 <= temp <= 35 and "[weather][mild]" in line:
                context.append(line)

        if "rain" in weather and "[weather][rain]" in line:
            context.append(line)

        if "[safety]" in line:
            context.append(line)

    return "\n".join(context[:5])

# ======================
# 📚 RAG ADVICE (ALWAYS WORKS)
# ======================
def rag_advice(temp, weather, dist, transport, kb):
    advice = []

    for line in kb:

        # 🌡 Weather
        if isinstance(temp, (int, float)):
            if temp > 35 and "[weather][heat]" in line:
                advice.append(line)
            elif temp < 20 and "[weather][cold]" in line:
                advice.append(line)
            elif 20 <= temp <= 35 and "[weather][mild]" in line:
                advice.append(line)

        # 🌧 Rain
        if "rain" in weather and "[weather][rain]" in line:
            advice.append(line)

        # ⚠ Safety (UPDATED CONDITION)
        if "[safety]" in line and (
            temp > 35 or 
            temp < 18 or 
            "rain" in weather or 
            dist > 1000   # 🔥 FIX HERE
        ):
            advice.append(line)

    # 🧹 Clean
    advice = [a.split("]")[-1].strip() for a in advice]

    # 🚆 Transport
    if "Flight" in transport:
        advice.append("Flight is best for long distance travel")
    elif "Train" in transport:
        advice.append("Train is comfortable for this journey")

    return list(dict.fromkeys(advice))[:4]
# ======================
# 🤖 LLM + RAG COMBINE
# ======================
def generate_advice(src, dest, temp, weather, dist, transport, hotels, context, kb_advice):

    prompt = f"""
You are an AI Travel Assistant.

Travel Details:
- Source: {src}
- Destination: {dest}
- Weather: {temp}°C, {weather}
- Distance: {dist} km
- Transport: {transport}
- Hotels: {hotels}

Context:
{context}

Give 3 short travel tips.
"""

    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}]
        )

        ai_text = response.choices[0].message.content

        return ai_text + "\n\n📌 Additional Tips:\n" + "\n".join([f"- {a}" for a in kb_advice])

    except:
        # fallback → KB always works
        return "\n".join([f"- {a}" for a in kb_advice])

# ======================
# 🚀 MAIN FUNCTION
# ======================
def travel(src, dest):
    s_temp, s_w = get_weather(src)
    d_temp, d_w = get_weather(dest)

    dist = get_distance(src, dest)
    transport = get_transport(dist)
    hotels = get_hotels(dest)

    kb = load_kb()

    context = retrieve_context(d_temp, d_w, kb)
    kb_advice = rag_advice(d_temp, d_w, dist, transport, kb)

    advice = generate_advice(
        src, dest, d_temp, d_w, dist, transport, hotels, context, kb_advice
    )

    return f"""
🌍 Travel Summary
{src} → {dest}

🌡 Source: {s_temp}°C ({s_w})
🌡 Destination: {d_temp}°C ({d_w})

📏 Distance: {dist} km
🚆 Transport: {transport}

🏨 Hotels:
- """ + "\n- ".join(hotels) + f"""

📚 Advice:
{advice}
"""

# ======================
# 🌐 CHAT API
# ======================
def get_response(query):
    match = re.search(r"from (.+?) to (.+)", query.lower())

    if not match:
        return "Use format: travel from X to Y"

    src, dest = match.groups()
    return travel(src, dest)

# ======================
# RUN
# ======================
if __name__ == "__main__":
    src = input("Enter source: ")
    dest = input("Enter destination: ")
    print(travel(src, dest))