import streamlit as st
import json
import os
import random
from PIL import Image

# --- INITIALIZE PAGE CONFIGURATION AND FAVICON ---
st.set_page_config(
    page_title="Character Matrix",
    page_icon="🪐",  
    layout="wide"
)

CHAR_FILE = "custom_characters.json"
AVATAR_DIR = "uploaded_avatars"
CHAT_MEDIA_DIR = "chat_media"  # Folder to temporarily save user-sent chat images

# Ensure necessary directories exist
for folder in [AVATAR_DIR, CHAT_MEDIA_DIR]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# --- INITIALIZE THEME AND SESSION MEMORY MATRIX ---
if "theme" not in st.session_state:
    st.session_state.theme = "Dark"

if "messages" not in st.session_state:
    st.session_state.messages = {}

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

if os.path.exists(CHAR_FILE):
    try:
        with open(CHAR_FILE, "r") as f:
            CHARACTERS = json.load(f)
    except:
        CHARACTERS = DEFAULT_CHARACTERS.copy()
else:
    CHARACTERS = DEFAULT_CHARACTERS.copy()

if "current_char" not in st.session_state:
    st.session_state.current_char = list(CHARACTERS.keys())[0]

# --- CHAI-STYLE ADAPTIVE CHAT RESPONSE LOGIC ---
def generate_reply(user_msg, char_name, has_image=False):
    msg = user_msg.lower() if user_msg else ""
    char_data = CHARACTERS[char_name]
    bio = char_data.get("bio", "").lower()
    
    actions = ["*crosses arms*", "*nods slowly*", "*sighs deep*", "*smirks*"]
    
    # Custom response trigger if the user sent an image file
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

    # Render previous messages (including images if they exist)
    for msg in st.session_state.messages[active_char]:
        with st.chat_message(msg["role"]):
            if msg.get("image") and os.path.exists(msg["image"]):
                st.image(msg["image"], width=250)
            if msg["content"]:
                st.write(msg["content"])

    # --- IMAGE ATTACHMENT HUB ---
    st.markdown("<p style='font-size:13px; margin-bottom: -15px;'>📎 Attach an image to your message:</p>", unsafe_allow_html=True)
    chat_image_file = st.file_uploader("", type=["png", "jpg", "jpeg"], key="chat_uploader", label_visibility="collapsed")

    # Capture chat input text
    user_input = st.chat_input(f"Send a message to {active_char}...")

    # Trigger action if either text is typed OR an image file is dropped in
    if user_input or chat_image_file:
        saved_chat_img_path = None
        
        # If user attached an image, process and save it
        if chat_image_file is not None:
            try:
                img = Image.open(chat_image_file)
                file_extension = os.path.splitext(chat_image_file.name)[1]
                file_name = f"msg_{random.randint(1000, 9999)}{file_extension}"
                saved_chat_img_path = os.path.join(CHAT_MEDIA_DIR, file_name)
                img.save(saved_chat_img_path)
            except Exception as e:
                st.error(f"Failed to process chat image: {e}")

        # Construct the user message log
        user_message_entry = {
            "role": "user", 
            "content": user_input if user_input else "", 
            "image": saved_chat_img_path
        }
        st.session_state.messages[active_char].append(user_message_entry)
        
        # Display user message instantly
        with st.chat_message("user"):
            if saved_chat_img_path:
                st.image(saved_chat_img_path, width=250)
            if user_input:
                st.write(user_input)
            
        # Generate and log character reply
        has_img_flag = True if saved_chat_img_path else False
        reply = generate_reply(user_input, active_char, has_image=has_img_flag)
        
        st.session_state.messages[active_char].append({"role": "assistant", "content": reply, "image": None})
        with st.chat_message("assistant"):
            st.write(reply)
            
        # Force rerun to clear the image file uploader slot for the next message
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
                    file_extension = os.path.splitext(uploaded_avatar.name)[1]
                    file_name = f"{new_name.lower().replace(' ', '_')}_avatar{file_extension}"
                    saved_avatar_path = os.path.join(AVATAR_DIR, file_name)
                    img.save(saved_avatar_path)
                except Exception as e:
                    st.error(f"Media compile tracking error: {e}")

            CHARACTERS[new_name] = {
                "title": new_title,
                "greeting": new_greet,
                "bio": new_bio,
                "avatar": saved_avatar_path
            }
            
            with open(CHAR_FILE, "w") as f:
                json.dump(CHARACTERS, f, indent=4)
                
            st.balloons()
            st.success(f"Successfully deployed {new_name} to the runtime profile index!")
            st.session_state.current_char = new_name
            st.rerun()
        else:
            st.error("Validation Halt: Please fill in all parameters requiring asterisks (*).")
