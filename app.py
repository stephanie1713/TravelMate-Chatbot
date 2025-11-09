import streamlit as st
import requests
from groq import Groq
import pandas as pd
import time

# ------------------------------
# Konfigurasi halaman
# ------------------------------
st.set_page_config(page_title="TravelMate AI", page_icon="🌴", layout="wide")

st.markdown("""
<h1 style='text-align: center;'>🌴 TravelMate AI</h1>
<p style='text-align: center;'>Asisten perjalanan & insight liburan kamu! 🎒</p>
""", unsafe_allow_html=True)

# ------------------------------
# Sidebar untuk Input API Key
# ------------------------------
st.sidebar.header("🛠️ Konfigurasi & API Keys")
exa_api_key = st.sidebar.text_input("EXA API Key", type="password")
groq_api_key = st.sidebar.text_input("GROQ API Key", type="password")
weather_api_key = st.sidebar.text_input("OpenWeather API Key", type="password")

st.sidebar.header("⚙️ Parameter Model")
temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.3, step=0.05)
top_p = st.sidebar.slider("Top-p (nucleus sampling)", 0.0, 1.0, 0.9, step=0.05)
max_tokens = st.sidebar.slider("Max Tokens", 64, 1024, 400, step=32)

st.sidebar.markdown("---")
if st.sidebar.button("🧹 Hapus Riwayat Chat"):
    st.session_state.chat_history = []

# ------------------------------
# Initialize session state
# ------------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

DEFAULT_MODEL = "llama-3.3-70b-versatile"

# ------------------------------
# Fungsi bantu
# ------------------------------
def search_places(query, exa_key):
    """Cari tempat dari EXA API"""
    if not exa_key:
        return []
    url = "https://api.exa.ai/search"
    headers = {"Authorization": f"Bearer {exa_key}", "Content-Type": "application/json"}
    payload = {"query": query, "num_results": 3}
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=8)
        r.raise_for_status()
        data = r.json()
        results = [{"title": item.get("title", "-"), "url": item.get("url", "")} for item in data.get("results", [])]
        return results
    except Exception:
        return []

def get_weather(city, weather_key):
    """Ambil data cuaca dari OpenWeather"""
    if not weather_key:
        return "(API cuaca tidak dikonfigurasi)"
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={weather_key}&units=metric&lang=id"
    try:
        r = requests.get(url, timeout=6)
        data = r.json()
        if data.get("cod") != 200:
            return "Cuaca tidak tersedia"
        desc = data["weather"][0]["description"].capitalize()
        temp = data["main"]["temp"]
        return f"{desc}, {temp}°C"
    except:
        return "Gagal mengambil data cuaca"

def call_llm(prompt, groq_key, model, temperature, top_p, max_tokens):
    """Panggil model Groq LLM"""
    try:
        client = Groq(api_key=groq_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are TravelMate AI, a friendly travel assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ Terjadi error saat memanggil model: {e}"

# ------------------------------
# UI utama
# ------------------------------
user_input = st.chat_input("Mau ke mana liburan kamu kali ini? 🌍")

if user_input:
    if not (exa_api_key and groq_api_key and weather_api_key):
        st.warning("⚠️ Masukkan semua API Key di sidebar dulu ya!")
    else:
        with st.spinner("TravelMate lagi nyari inspirasi liburan... ✈️"):
            places = search_places(user_input, exa_api_key)
            weather_info = get_weather(user_input, weather_api_key)

            context = ""
            if places:
                context += "Rekomendasi tempat:\n"
                for p in places:
                    context += f"- {p['title']}: {p['url']}\n"
            context += f"\nCuaca saat ini di {user_input}: {weather_info}\n"

            prompt = f"""
Kamu adalah TravelMate AI, asisten perjalanan yang ramah dan pintar.
Pengguna bertanya: "{user_input}"
Gunakan data ini untuk membantu:
{context}

Buat jawaban dengan gaya santai, ramah, dan relevan.
Sertakan tips wisata, rekomendasi, dan insight menarik.
"""
            reply = call_llm(prompt, groq_api_key, DEFAULT_MODEL, temperature, top_p, max_tokens)

            st.session_state.chat_history.append({"user": user_input, "assistant": reply, "places": places})

# ------------------------------
# Tampilkan percakapan
# ------------------------------
for chat in st.session_state.chat_history:
    with st.chat_message("user"):
        st.markdown(chat["user"])
    with st.chat_message("assistant"):
        st.markdown(chat["assistant"])
        if chat["places"]:
            df = pd.DataFrame(chat["places"])
            st.dataframe(df, use_container_width=True)