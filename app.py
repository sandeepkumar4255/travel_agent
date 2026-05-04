import streamlit as st
import requests

API_URL = "https://travel-agent-kr8f.onrender.com/chat"
# ======================
# 🎨 PAGE SETTINGS
# ======================
st.set_page_config(
    page_title="AI Travel Assistant",
    page_icon="🌍",
    layout="centered"
)

# ======================
# 🎨 SIMPLE UI
# ======================
st.title("🌍 AI Travel Assistant")
st.caption("Plan your journey with AI + Live APIs")

# ======================
# 🧑 INPUT
# ======================
col1, col2 = st.columns(2)

with col1:
    source = st.text_input("From City")

with col2:
    destination = st.text_input("To City")

# ======================
# 🚀 BUTTON
# ======================
if st.button("Plan Trip ✈️"):

    if not source or not destination:
        st.warning("Please enter both cities")
    else:
        with st.spinner("Fetching travel data..."):

            try:
                response = requests.post(
                    API_URL,
                    json={
                        "source": source,
                        "destination": destination
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    result = data.get("response", "")

                    st.success("Travel Plan Ready ✅")

                    # ======================
                    # 📊 OUTPUT
                    # ======================
                    st.markdown("### 📊 Travel Summary")

                    st.markdown(
                        f"""
                        <div style="
                            background:#1e293b;
                            padding:20px;
                            border-radius:10px;
                            color:white;
                        ">
                        <pre>{result}</pre>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                else:
                    st.error("Backend error")

            except Exception as e:
                st.error("Cannot connect to backend ❌")
