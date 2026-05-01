import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000/chat"

st.set_page_config(page_title="AI Travel Assistant", page_icon="🌍")

# ======================
# 🎨 SIMPLE UNIQUE STYLE
# ======================
st.markdown("""
<style>
body {
    background-color: #0f172a;
}
.title {
    font-size: 38px;
    text-align: center;
    color: #00f5d4;
    font-weight: bold;
}
.subtitle {
    text-align: center;
    color: #94a3b8;
    margin-bottom: 30px;
}
.result-box {
    background: #1e293b;
    padding: 20px;
    border-radius: 12px;
    margin-top: 20px;
}
</style>
""", unsafe_allow_html=True)

# ======================
# 🧾 HEADER
# ======================
st.markdown('<div class="title">🌍 AI Travel Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Plan your journey smartly</div>', unsafe_allow_html=True)

# ======================
# 🧑 INPUT
# ======================
source = st.text_input("From City")
destination = st.text_input("To City")

# ======================
# 🚀 BUTTON
# ======================
if st.button("Plan Trip ✈️"):
    if source and destination:
        query = f"travel from {source} to {destination}"

        with st.spinner("Analyzing travel data..."):
            try:
                res = requests.post(API_URL, json={"message": query})
                data = res.json()

                result = data.get("response", "")

                st.success("Travel Plan Ready")

                # ======================
                # 📊 UNIQUE DISPLAY
                # ======================
                st.markdown("### 📊 Travel Details")

                st.markdown(f"""
                <div class="result-box">
                <pre>{result}</pre>
                </div>
                """, unsafe_allow_html=True)

            except:
                st.error("Backend not running")
    else:
        st.warning("Enter both cities")

# ======================
# 💡 QUICK BUTTONS
# ======================
st.markdown("### ⚡ Quick Try")

col1, col2, col3 = st.columns(3)

if col1.button("Vizag → Delhi"):
    st.experimental_set_query_params(src="vizag", dest="delhi")

if col2.button("Hyderabad → Goa"):
    st.experimental_set_query_params(src="hyderabad", dest="goa")

if col3.button("Bangalore → Chennai"):
    st.experimental_set_query_params(src="bangalore", dest="chennai")

# ======================
# FOOTER
# ======================
st.markdown("---")
st.markdown("<center>Made with ❤️ using Streamlit</center>", unsafe_allow_html=True)