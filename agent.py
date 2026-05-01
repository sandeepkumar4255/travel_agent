import requests, os, math, re
from dotenv import load_dotenv
from groq import Groq

# ======================
# 🔐 SETUP
# ======================
load_dotenv()

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)


# ======================
# 🌦 WEATHER
# ======================
def get_weather(city):
    if not WEATHER_API_KEY:
        return "N/A", "Missing API Key"

    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
        res = requests.get(url, timeout=5)

        if res.status_code != 200:
            return "N/A", f"Error {res.status_code}"

        data = res.json()
        return data["main"]["temp"], data["weather"][0]["description"]

    except:
        return "N/A", "API Error"


# ======================
# 📍 COORDS
# ======================
def get_coords(city):
    if not GEOAPIFY_API_KEY:
        return None, None

    try:
        url = f"https://api.geoapify.com/v1/geocode/search?text={city}&apiKey={GEOAPIFY_API_KEY}"
        res = requests.get(url, timeout=5)

        if res.status_code != 200:
            return None, None

        data = res.json()

        if not data.get("features"):
            return None, None

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

    if lat1 is None or lat2 is None:
        return "Not available"

    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
    return round(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a)), 2)


# ======================
# 🚆 TRANSPORT
# ======================
def get_transport(d):
    if isinstance(d, str):
        return "Unknown"

    if d < 100:
        return "Car/Bike"
    elif d < 1000:
        return "Train"
    else:
        return "Flight"


# ======================
# 🏨 HOTELS
# ======================
def get_hotels(city):
    try:
        lat, lon = get_coords(city)

        if lat is None:
            return ["No hotels found"]

        url = f"https://api.geoapify.com/v2/places?categories=accommodation.hotel&filter=circle:{lon},{lat},15000&limit=5&apiKey={GEOAPIFY_API_KEY}"
        res = requests.get(url, timeout=5)

        if res.status_code != 200:
            return ["No hotels found"]

        data = res.json()

        hotels = [
            p["properties"].get("name")
            for p in data.get("features", [])
            if p["properties"].get("name")
        ]

        return hotels if hotels else ["No hotels found"]

    except:
        return ["No hotels found"]


# ======================
# 📚 LOAD KB
# ======================
def load_kb():
    try:
        return open("travel.txt", encoding="utf-8").read().lower().split("\n")
    except:
        return []


# ======================
# 🔍 CONTEXT
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

        if isinstance(weather, str) and "rain" in weather and "[weather][rain]" in line:
            context.append(line)

        if "[safety]" in line:
            context.append(line)

    return "\n".join(context[:5]) if context else "General travel safety tips"


# ======================
# 📚 RAG ADVICE
# ======================
def rag_advice(temp, weather, dist, transport, kb):
    advice = []

    for line in kb:
        if isinstance(temp, (int, float)):
            if temp > 35 and "[weather][heat]" in line:
                advice.append(line)
            elif temp < 20 and "[weather][cold]" in line:
                advice.append(line)
            elif 20 <= temp <= 35 and "[weather][mild]" in line:
                advice.append(line)

        if isinstance(weather, str) and "rain" in weather and "[weather][rain]" in line:
            advice.append(line)

        if "[safety]" in line and (
            (isinstance(temp, (int, float)) and (temp > 35 or temp < 18)) or
            (isinstance(weather, str) and "rain" in weather) or
            (isinstance(dist, (int, float)) and dist > 1000)
        ):
            advice.append(line)

    advice = [a.split("]")[-1].strip() for a in advice]

    if "Flight" in transport:
        advice.append("Flight is best for long distance travel")
    elif "Train" in transport:
        advice.append("Train is comfortable for this journey")

    return list(dict.fromkeys(advice))[:4]


# ======================
# 🤖 LLM
# ======================
def generate_advice(src, dest, temp, weather, dist, transport, hotels, context, kb_advice):

    prompt = f"""
You are an AI Travel Assistant.

STRICT RULE:
- Use ONLY the given CONTEXT.
- Do NOT invent information.

Travel Details:
- Source: {src}
- Destination: {dest}
- Weather: {temp}°C, {weather}
- Distance: {dist} km
- Transport: {transport}
- Hotels: {hotels}

CONTEXT:
{context}

TASK:
Give 3 short travel tips.
"""

    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}]
        )

        ai_text = response.choices[0].message.content

        extra = "\n".join([f"- {a}" for a in kb_advice])

        return f"{ai_text}\n\n📌 Extra Smart Tips:\n{extra}"

    except:
        return "\n".join([f"- {a}" for a in kb_advice])


# ======================
# 🚀 MAIN FUNCTION
# ======================
def travel(source, destination):

    temp, weather = get_weather(destination)
    distance = get_distance(source, destination)
    transport = get_transport(distance)
    hotels = get_hotels(destination)

    kb = load_kb()
    context = retrieve_context(temp, weather, kb)
    advice = rag_advice(temp, weather, distance, transport, kb)

    final_advice = generate_advice(
        source, destination, temp, weather,
        distance, transport, hotels, context, advice
    )

    return f"""
🌍 Travel Summary

From: {source}
To: {destination}

📏 Distance: {distance} km
🚆 Transport: {transport}

🌤 Weather:
- {destination}: {temp}°C, {weather}

🏨 Hotels:
- {", ".join(hotels)}

💡 Tips:
{final_advice}
"""


# ======================
# 🌐 CHAT
# ======================
def get_response(query):
    match = re.search(r"from (.+?) to (.+)", query.lower())

    if not match:
        return "Use format: travel from X to Y"

    src, dest = match.groups()
    return travel(src, dest)