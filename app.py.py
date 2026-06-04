import streamlit as st
import json
import os
import random
import requests
import base64
from PIL import Image

# --- INITIALIZE PAGE CONFIGURATION AND FAVICON ---
st.set_page_config(
    page_title="Character Matrix",
    page_icon="🪐",  
    layout="wide"
)

# --- GITHUB PERMANENT DATABASE CONFIGURATION ---
REPO = "finmcg-ctrl/my-ai-character-hub"
TOKEN = st.secrets.get("GITHUB_TOKEN", "")

CHAR_FILE = "custom_characters.json"
CHAT_HISTORY_FILE = "chat_history.json"
AVATAR_DIR = "uploaded_avatars"
CHAT_MEDIA_DIR = "chat_media"  

for folder in [AVATAR_DIR, CHAT_MEDIA_DIR]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# Display a helper alert if the secret variable isn't configured in Streamlit Cloud
if not TOKEN:
    st.warning("⚠️ Database Warning: `GITHUB_TOKEN` was not found inside your Streamlit Secrets vault. Your chats are currently running on temporary memory.")

# Helper function to read from GitHub DB with explicit error logs
def github_fetch_file(filename, default_data):
    if not TOKEN:
        return default_data
    url = f"https://api.github.com/repos/{REPO}/contents/{filename}"
    headers = {"Authorization": f"token {TOKEN}"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            content = response.json()
            file_content = base64.b64decode(content["content"]).decode("utf-8")
            return json.loads(file_content)
        elif response.status_code == 401 or response.status_code == 403:
            st.error(f"❌ GitHub Authorization Failed (Status {response.status_code}). Check your Personal Access Token scopes.")
        elif response.status_code == 404:
            # File doesn't exist yet, this is normal for a fresh build
            return default_data
    except Exception as e:
        st.error(f"🔌 Database Connection Error: {e}")
    return default_data

# Helper function to save to GitHub DB with explicit error logs
def github_save_file(filename, data):
    if not TOKEN:
        return
    url = f"https://api.github.com/repos/{REPO}/contents/{filename}"
    headers = {"Authorization": f"token {TOKEN}"}
    try:
        response = requests.get(url, headers=headers)
        sha = response.json().get("sha") if response.status_code == 200 else None
        
        encoded_content = base64.b64encode(json.dumps(data, indent=4).encode("utf-8")).decode("utf-8")
        payload = {
            "message": f"Database Sync: Updated {filename}",
            "content": encoded_content
        }
        if sha:
            payload["sha"] = sha
            
        res = requests.put(url, headers=headers, json=payload)
        if res.status_code not in [200, 201]:
            st.error(f"❌ Could not write back to GitHub database. Status Code: {res.status_code}. Response: {res.text}")
    except Exception as e:
        st.error(f"💾 Failed to commit data packet: {e}")

# --- LOAD REGISTERED CHARACTER PROFILES ---
DEFAULT_CHARACTERS = {
    "Luna": {
        "title": "Sarcastic Space Explorer",
        "greeting": "Comm-line active. Hey there, traveler!",
        "bio": "Luna is a cynical spaceship pilot. She uses dry wit, loves space coffee, hates bad engine thrusters, and frequently references cosmic anomalies.",
        "avatar": None
    },
    "Merlin": {
        "title": "Ancient Grumpy Wizard",
        "greeting": "*Puffs pipe* Who dares disturb my arcane studies?! Speak quickly, mortal.",
        "bio": "Merlin is a cranky old wizard from a dark fantasy realm. He complains about his aching knees, guards his glowing potions fiercely, and speaks with Old English flair.",
        "avatar": None
    }
}

if "characters_db" not in st.session_state:
    st.session_state.characters_db = github_fetch_file(CHAR_FILE, DEFAULT_CHARACTERS)

CHARACTERS = st.session_state.characters_db

if "theme" not in st.session_state:
    st.session_state.theme = "Dark"

if "messages" not in st.session_state:
    st.session_state.messages = github_fetch_file(CHAT_HISTORY_FILE, {})

if "last_processed_image" not in st.session_state:
    st.session_state.last_processed_image = None

if "current_char" not in st.session_state:
    st.session_state.current_char = list(CHARACTERS.keys())[0]

# --- DYNAMIC STRUCTURAL CSS INJECTOR ---
if st.session_state.theme == "Dark":
    st.markdown("""
        <style>
        .stApp { background-color: #0f0f14; color: #cdd6f4; }
        div[data-testid="stSidebar"] { background-color: #161622; }
        div.stButton > button:first-child { background-color: #a6e3a1; color: #11111b; font-weight: bold; border-radius: 8px; border: none; }
        div[data-baseweb="tab-list"] { background-color: #161622; border-radius: 8px; padding: 4px; }
        div[data-baseweb="tab"] { color: #cdd6f4; font-weight: 500; }
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
        .stApp { background-color: #f8f9fa; color: #212529; }
        div[data-testid="stSidebar"] { background-color: #e9ecef; }
        div.stButton > button:first-child { background-color: #0d6efd; color: #ffffff; font-weight: bold; border-radius: 8px; border: none; }
        div[data-baseweb="tab-list"] { background-color: #e9ecef; border-radius: 8px; padding: 4px; }
        div[data-baseweb="tab"] { color: #212529; font-weight: 500; }
        </style>
    """, unsafe_allow_html=True)

# --- CHAI-STYLE ADAPTIVE CHAT RESPONSE LOGIC ---
def generate_reply(user_msg, char_name, has_image=False):
    msg = user_msg.lower() if user_msg else ""
    char_data = CHARACTERS[char_name]
    bio = char_data.get("bio", "").lower()
    
    actions = ["*crosses arms*", "*nods slowly*", "*sighs deep*", "*smirks*"]
    
    if has_image:
        if "wizard" in bio:
            return f"{random.choice(actions)} What sort of magical artifact or illusion am I looking at right now? Explain yourself!"
        elif "pilot" in bio or "explorer" in bio:
            return f"{random.choice(actions)} Scanning this transmission attachment. Looks like a coordinate map or unknown data module."
        return f"{random.choice(actions)} Interesting visual transmission. My scanners are analyzing what you just sent me."

    if "coffee" in msg or "drink" in msg:
        if "coffee" in bio or "pilot" in bio:
            return "Did someone say coffee?! I'd trade my entire warp drive engine for a warm cup right now."
    if "magic" in msg or "wizard" in msg:
        if "wizard" in bio:
            return "Magic requires absolute focus! One wrong syllable and you turn into a toad."

    matching_words = [word for word in bio.replace(",", "").replace(".", "").split() if len(word) > 4 and word in msg]
    if matching_words:
        return f"{random.choice(actions)} Talking about {matching_words[0]}? That aligns perfectly with my background as a {char_data['title']}."

    if "grumpy" in bio or "cranky" in bio:
        return f"{random.choice(actions)} Don't push your luck. I'm not in the mood for games today."
    elif "friendly" in bio or "sweet" in bio:
        return f"{random.choice(actions)} That's wonderful to hear! I'm always glad to help out."
    
    return f"{random.choice(actions)} That is an interesting transmission line. Tell me more."

# --- NAVIGATION HUB SIDEBAR ---
with st.sidebar:
    st.title("🪐 Character Hub")
    
    theme_selection = st.selectbox("Interface Display Theme:", ["Dark", "Light"], index=0 if st.session_state.theme == "Dark" else 1)
    if theme_selection != st.session_state.theme:
        st.session_state.theme = theme_selection
        st.rerun()
        
    st.markdown("---")
    
    selected = st.radio("Active Conversations:", list(CHARACTERS.keys()))
    if selected != st.session_state.current_char:
        st.session_state.current_char = selected
        st.rerun()

# --- CENTRAL APPLICATION MATRIX TABS ---
tab_chat, tab_create = st.tabs(["💬 AI Chat Dashboard", "🎨 Advanced Character Studio"])

# ================= TAB 1: IMMERSIVE CHAT INTERFACE =================
with tab_chat:
    active_char = st.session_state.current_char
    char_info = CHARACTERS[active_char]
    
    col_avatar, col_details = st.columns([1, 8])
    with col_avatar:
        avatar_path = char_info.get("avatar")
        if avatar_path and os.path.exists(avatar_path):
            st.image(avatar_path, width=85)
        else:
            st.markdown("<h1 style='text-align: center; margin:0; padding-top:10px;'>👤</h1>", unsafe_allow_html=True)
            
    with col_details:
        st.subheader(f"{active_char}")
        st.caption(f"**Tagline:** {char_info['title']} | **Core Definition Matrix:** {char_info['bio']}")
    
    st.markdown("---")

    if active_char not in st.session_state.messages:
        st.session_state.messages[active_char] = [{"role": "assistant", "content": char_info["greeting"], "image": None}]
        github_save_file(CHAT_HISTORY_FILE, st.session_state.messages)

    # Render previous logs safely
    for msg in st.session_state.messages[active_char]:
        with st.chat_message(msg["role"]):
            if msg.get("image") and os.path.exists(msg["image"]):
                st.image(msg["image"], width=250)
            if msg["content"]:
                st.write(msg["content"])

    # --- IMAGE ATTACHMENT HUB ---
    st.markdown("<p style='font-size:13px; margin-bottom: -15px;'>📎 Attach an image to your message:</p>", unsafe_allow_html=True)
    chat_image_file = st.file_uploader("", type=["png", "jpg", "jpeg"], key="chat_uploader", label_visibility="collapsed")

    # Capture chat input text safely
    user_input = st.chat_input(f"Send a message to {active_char}...")

    is_new_image = chat_image_file is not None and chat_image_file.name != st.session_state.last_processed_image

    if user_input or is_new_image:
        saved_chat_img_path = None
        
        if is_new_image:
            try:
                img = Image.open(chat_image_file)
                img.thumbnail((800, 800)) 
                
                file_extension = os.path.splitext(chat_image_file.name)[1]
                if not file_extension:
                    file_extension = ".jpg"
                    
                file_name = f"msg_{random.randint(10000, 99999)}{file_extension}"
                saved_chat_img_path = os.path.join(CHAT_MEDIA_DIR, file_name)
                img.save(saved_chat_img_path, optimize=True, quality=80)
                
                st.session_state.last_processed_image = chat_image_file.name
            except Exception as e:
                st.error(f"Failed to process chat image: {e}")

        # Append user message entry
        user_message_entry = {
            "role": "user", 
            "content": user_input if user_input else "", 
            "image": saved_chat_img_path
        }
        st.session_state.messages[active_char].append(user_message_entry)
        
        # Process and append character reply
        has_img_flag = True if saved_chat_img_path else False
        reply = generate_reply(user_input, active_char, has_image=has_img_flag)
        st.session_state.messages[active_char].append({"role": "assistant", "content": reply, "image": None})
        
        # Save to database file on GitHub
        github_save_file(CHAT_HISTORY_FILE, st.session_state.messages)
        st.rerun()

# ================= TAB 2: ADVANCED CREATION DASHBOARD =================
with tab_create:
    st.header("✨ Model Creation Engine")
    st.markdown("Configure custom persona guidelines matching dedicated platform field metrics.")
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        new_name = st.text_input("Character Chat Name *", placeholder="e.g., Cybernetic Engineer Lilly")
        new_title = st.text_input("Short Role Sub-Title / Tagline *", placeholder="e.g., Friendly Mech Pilot")
        new_greet = st.text_area("Initial Greeting Response *", placeholder="*Wipes oil from brow* Hey! Need an engine tuning?", height=100)

    with col_right:
        uploaded_avatar = st.file_uploader("Upload Profile Avatar Media (PNG / JPG)", type=["png", "jpg", "jpeg", "jfif"])
        new_bio = st.text_area("Character Background Memory Definition (Long Bio) *", 
                               placeholder="Provide core personality traits, behaviors, likes, and dialogue preferences...",
                               height=175)

    st.markdown("---")
    
    if st.button("🔥 Compile & Register Character Card Profile", use_container_width=True):
        if new_name and new_title and new_greet and new_bio:
            saved_avatar_path = None
            
            if uploaded_avatar is not None:
                try:
                    img = Image.open(uploaded_avatar)
                    img.thumbnail((300, 300))
                    file_extension = os.path.splitext(uploaded_avatar.name)[1]
                    file_name = f"{new_name.lower().replace(' ', '_')}_avatar{file_extension}"
                    saved_avatar_path = os.path.join(AVATAR_DIR, file_name)
                    img.save(saved_avatar_path, optimize=True, quality=85)
                except Exception as e:
                    st.error(f"Media compile tracking error: {e}")

            CHARACTERS[new_name] = {
                "title": new_title,
                "greeting": new_greet,
                "bio": new_bio,
                "avatar": saved_avatar_path
            }
            
            # Save character list directly to GitHub
            github_save_file(CHAR_FILE, CHARACTERS)
            st.session_state.characters_db = CHARACTERS
                
            st.balloons()
            st.success(f"Successfully deployed {new_name} to the runtime profile index!")
            st.session_state.current_char = new_name
            st.rerun()
        else:
            st.error("Validation Halt: Please fill in all parameters requiring asterisks (*).")
