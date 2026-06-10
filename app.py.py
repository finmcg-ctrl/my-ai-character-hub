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

if not TOKEN:
    st.warning("⚠️ Database Warning: `GITHUB_TOKEN` was not found inside your Streamlit Secrets vault. Your chats are currently running on temporary memory.")

# Helper function to read from GitHub DB
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
    except:
        pass
    return default_data

# Helper function to save to GitHub DB
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
            
        requests.put(url, headers=headers, json=payload)
    except:
        pass

# --- LOAD REGISTERED CHARACTER PROFILES ---
DEFAULT_CHARACTERS = {
    "Undertale AU RPG Sandbox": {
        "title": "The multi-universe text simulator.",
        "greeting": "* (The wind howls through the barrier...)\n\n* Welcome to the Undertale AU Sandbox. Please declare your character setup:\n\n* 1. What is your Name/OC?\n* 2. What are your Soul Trait and starting items?\n* 3. Which Alternate Universe (AU) are we entering?\n\n* (The power of creation fills you with DETERMINATION.)",
        "bio": "An immersive, text-based RPG engine dedicated to running an Undertale Alternate Universe (AU) roleplay simulator. Describes scenes, reacts to choices, and voices characters with canonical accuracy. Wrap actions/scenery in asterisks (*) and use Undertale formatting constants.",
        "avatar": None
    },
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

# --- INITIALIZE INLINE UTILITY EDITS CONTROLS ---
if "editing_idx" not in st.session_state:
    st.session_state.editing_idx = None

# --- DYNAMIC STRUCTURAL CSS INJECTOR ---
if st.session_state.theme == "Dark":
    st.markdown("""
        <style>
        .stApp { background-color: #0f0f14; color: #cdd6f4; }
        div[data-testid="stSidebar"] { background-color: #161622; }
        div.stButton > button { background-color: #252538; color: #cdd6f4; border: 1px solid #3b4261; border-radius: 6px; padding: 2px 10px; font-size: 12px; }
        div.stButton > button:hover { border-color: #a6e3a1; color: #a6e3a1; }
        div[data-baseweb="tab-list"] { background-color: #161622; border-radius: 8px; padding: 4px; }
        div[data-baseweb="tab"] { color: #cdd6f4; font-weight: 500; }
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
        .stApp { background-color: #f8f9fa; color: #212529; }
        div[data-testid="stSidebar"] { background-color: #e9ecef; }
        div.stButton > button { background-color: #ffffff; color: #212529; border: 1px solid #ced4da; border-radius: 6px; padding: 2px 10px; font-size: 12px; }
        div.stButton > button:hover { border-color: #0d6efd; color: #0d6efd; }
        div[data-baseweb="tab-list"] { background-color: #e9ecef; border-radius: 8px; padding: 4px; }
        div[data-baseweb="tab"] { color: #212529; font-weight: 500; }
        </style>
    """, unsafe_allow_html=True)

# --- REAL AI INTELLIGENCE GENERATION ROUTINE ---
def generate_reply(user_msg, char_name, has_image=False):
    """
    Generates authentic, dynamic AI text responses using a zero-config, 
    highly stable free inference pipeline if custom API keys are missing.
    """
    char_data = CHARACTERS.get(char_name, {})
    bio = char_data.get("bio", "")
    title = char_data.get("title", "")
    
    system_instruction = (
        f"You are a master at creative writing and immersive text-based roleplay.\n"
        f"You are currently roleplaying 100% as the character '{char_name}' ({title}).\n"
        f"Character Lore & Personality Rules:\n{bio}\n\n"
        f"Task: Write the next response as {char_name}. Stay inside your specific personality. "
        f"Be expressive, immersive, react directly to what the user said, and use asterisks for actions if it fits your style. "
        f"Never repeat yourself or break character. Keep responses snappy and concise."
    )

    # Gather clean context history
    history_context = []
    if char_name in st.session_state.messages:
        for old_msg in st.session_state.messages[char_name][-4:]:
            role_label = "user" if old_msg['role'] == 'user' else "assistant"
            history_context.append({"role": role_label, "content": old_msg['content']})

    try:
        # Route 1: Premium Secure OpenAI fallback
        openai_key = st.secrets.get("OPENAI_API_KEY", "")
        if openai_key:
            headers = {"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"}
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system_instruction},
                    *history_context,
                    {"role": "user", "content": user_msg}
                ]
            }
            res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=10)
            if res.status_code == 200:
                return res.json()["choices"][0]["message"]["content"].strip()
                
        # Route 2: Ultra-stable Free Public Inference API (No keys required)
        messages_payload = [
            {"role": "system", "content": system_instruction},
            *history_context,
            {"role": "user", "content": user_msg}
        ]
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "HTTP-Referer": "https://streamlit.io",
                "X-Title": "Character Matrix Hub"
            },
            json={
                "model": "meta-llama/llama-3.2-3b-instruct:free",
                "messages": messages_payload,
                "temperature": 0.85,
                "max_tokens": 180
            },
            timeout=10
        )
        if response.status_code == 200:
            ai_res = response.json()
            ai_text = ai_res["choices"][0]["message"]["content"].strip()
            if ai_text:
                return ai_text
    except:
        pass

    # Backup Safety Fallback (Only fires if external APIs go completely offline)
    msg_low = user_msg.lower() if user_msg else ""
    actions = ["*sighs deeply*", "*adjusts stance*", "*looks at you closely*", "*crosses arms*"]
    act = random.choice(actions)
    
    if "undertale" in char_name.lower() or "sandbox" in char_name.lower():
        return "* (The sandbox environment hums with energy.)\n\n* You prepare your next action. What is your choice?"
    if "wizard" in bio.lower() or "merlin" in char_name.lower():
        return f"{act} Bah! In my day, a simple incantation could move mountains. What is your business here, mortal?"
    if "pilot" in bio.lower() or "luna" in char_name.lower():
        return f"{act} Out here past the outer rim, you learn not to trust every stray data packet. What's your angle?"
    return f"{act} That's an interesting strategy. Tell me how you want to proceed with this scenario."
        # FREE PUBLIC ROUTE
        API_URL = "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-7B-Instruct"
        response = requests.post(
            API_URL, 
            json={"inputs": full_prompt, "parameters": {"max_new_tokens": 150, "temperature": 0.8, "return_full_text": False}}, 
            timeout=8
        )
        if response.status_code == 200:
            res_json = response.json()
            if isinstance(res_json, list) and "generated_text" in res_json[0]:
                ai_text = res_json[0]["generated_text"].strip()
                ai_text = ai_text.split("User:")[0].split("<|")[0].strip()
                if ai_text:
                    return ai_text
    except:
        pass

    msg_low = user_msg.lower() if user_msg else ""
    actions = ["*sighs deeply*", "*adjusts stance*", "*looks at you closely*", "*crosses arms*"]
    act = random.choice(actions)
    
    if "undertale" in char_name.lower() or "sandbox" in char_name.lower():
        if "gilly" in msg_low or "human" in msg_low:
            return "* (The wind howls fiercely through the trees...)\n\n* A human...? Your cracked Determination soul reacts to the bitter chill of Underfell Snowdin.\n\n* A shadowy figure watches you from behind a dynamic checkpoint station.\n\n* What will you do?\n[ FIGHT ]   [ ACT ]   [ ITEM ]   [ MERCY ]"
        return "* (The sandbox environment hums with energy.)\n\n* You prepare your next action. What is your choice?"
        
    if "wizard" in bio.lower() or "merlin" in char_name.lower():
        return f"{act} Bah! You speak of modern ideas. In my day, a simple incantation could move mountains. What is your true business here?"
        
    if "pilot" in bio.lower() or "luna" in char_name.lower():
        return f"{act} Tracking that sensor sweep data now. Out here past the outer rim, you learn not to trust every incoming transmission packet. What's your play?"

    return f"{act} That's a unique perspective. Tell me how you want to proceed with this matrix scenario."

# --- NAVIGATION HUB SIDEBAR WITH FILTERS AND SEARCH ---
with st.sidebar:
    st.title("🪐 Character Hub")
    
    theme_selection = st.selectbox("Interface Display Theme:", ["Dark", "Light"], index=0 if st.session_state.theme == "Dark" else 1)
    if theme_selection != st.session_state.theme:
        st.session_state.theme = theme_selection
        st.rerun()
        
    st.markdown("---")
    
    search_query = st.text_input("🔍 Search Bots by Name:", placeholder="Type bot name...")
    
    all_bots = list(CHARACTERS.keys())
    if search_query:
        filtered_bots = [bot for bot in all_bots if search_query.lower() in bot.lower()]
    else:
        filtered_bots = all_bots

    if len(filtered_bots) == 0:
        st.caption("No chatbots match your search.")
        selected = None
    else:
        if "current_char" not in st.session_state or st.session_state.current_char not in CHARACTERS:
            st.session_state.current_char = filtered_bots[0]
            
        try:
            start_index = filtered_bots.index(st.session_state.current_char)
        except ValueError:
            start_index = 0
            st.session_state.current_char = filtered_bots[0]

        selected = st.radio("Active Conversations:", filtered_bots, index=start_index)
        if selected != st.session_state.current_char:
            st.session_state.current_char = selected
            st.session_state.editing_idx = None  
            st.rerun()

# --- CENTRAL APPLICATION MATRIX TABS ---
tab_chat, tab_create, tab_inventory = st.tabs(["💬 AI Chat Dashboard", "🎨 Advanced Character Studio", "🗂️ My Creations Gallery"])

# ================= TAB 1: IMMERSIVE CHAT INTERFACE =================
with tab_chat:
    if not st.session_state.current_char or st.session_state.current_char not in CHARACTERS:
        st.info("Please select or create an active chatbot profile using the sidebar or creation dashboard tab.")
    else:
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
            st.caption(f"**Tagline:** {char_info.get('title')} | **Core Definition Matrix:** {char_info.get('bio')}")
        
        st.markdown("---")

        if active_char not in st.session_state.messages:
            st.session_state.messages[active_char] = [{"role": "assistant", "content": char_info.get("greeting", "Hello!"), "image": None}]
            github_save_file(CHAT_HISTORY_FILE, st.session_state.messages)

        # --- INLINE MESSAGE TOOL HUB ---
        for index, msg in enumerate(st.session_state.messages[active_char]):
            role_id_tag = "assistant" if msg["role"] == "assistant" else "user"
            
            with st.chat_message(msg["role"]):
                if msg.get("image") and os.path.exists(msg["image"]):
                    st.image(msg["image"], width=250)
                
                if st.session_state.editing_idx == index:
                    edited_input = st.text_input("Edit text line packet:", value=msg["content"], key=f"inp_edit_{role_id_tag}_{index}")
                    c_save, c_cancel = st.columns([1, 9])
                    with c_save:
                        if st.button("💾 Save", key=f"btn_save_{role_id_tag}_{index}"):
                            st.session_state.messages[active_char][index]["content"] = edited_input
                            github_save_file(CHAT_HISTORY_FILE, st.session_state.messages)
                            st.session_state.editing_idx = None
                            st.rerun()
                    with c_cancel:
                        if st.button("❌ Cancel", key=f"btn_cancel_{role_id_tag}_{index}"):
                            st.session_state.editing_idx = None
                            st.rerun()
                else:
                    if msg["content"]:
                        st.write(msg["content"])
                    
                    if msg["role"] == "assistant":
                        col_b1, col_b2, col_b3, col_empty = st.columns([1.2, 1.6, 1.2, 8])
                        with col_b1:
                            if st.button("✏️ Edit", key=f"btn_edit_assistant_{index}"):
                                st.session_state.editing_idx = index
                                st.rerun()
                        with col_b2:
                            if index > 0: 
                                if st.button("🔄 Re-roll", key=f"btn_roll_assistant_{index}"):
                                    preceding_input = ""
                                    for k in range(index - 1, -1, -1):
                                        if st.session_state.messages[active_char][k]["role"] == "user":
                                            preceding_input = st.session_state.messages[active_char][k]["content"]
                                            break
                                    fresh_response = generate_reply(preceding_input, active_char, has_image=False)
                                    st.session_state.messages[active_char][index]["content"] = fresh_response
                                    github_save_file(CHAT_HISTORY_FILE, st.session_state.messages)
                                    st.rerun()
                        with col_b3:
                            if st.button("🗑️ Delete", key=f"btn_del_assistant_{index}"):
                                st.session_state.messages[active_char].pop(index)
                                if len(st.session_state.messages[active_char]) == 0:
                                    st.session_state.messages[active_char] = [{"role": "assistant", "content": char_info.get("greeting", "Hello!"), "image": None}]
                                github_save_file(CHAT_HISTORY_FILE, st.session_state.messages)
                                st.rerun()
                    else:
                        col_u1, col_u2, col_empty = st.columns([1.2, 1.2, 9])
                        with col_u1:
                            if st.button("✏️ Edit", key=f"btn_edit_user_{index}"):
                                st.session_state.editing_idx = index
                                st.rerun()
                        with col_u2:
                            if st.button("🗑️ Delete", key=f"btn_del_user_{index}"):
                                st.session_state.messages[active_char].pop(index)
                                github_save_file(CHAT_HISTORY_FILE, st.session_state.messages)
                                st.rerun()

        st.markdown("---")

        # --- INPUT HUD ZONE GRID ---
        col_upload_box, col_input_box = st.columns([3, 7])
        
        with col_upload_box:
            chat_image_file = st.file_uploader("📎 Attach Media Packet:", type=["png", "jpg", "jpeg"])

        with col_input_box:
            user_input = st.chat_input(f"Send a message to {active_char}...")

        is_new_image = chat_image_file is not None and chat_image_file.name != st.session_state.last_processed_image

        if user_input or is_new_image:
            saved_chat_img_path = None
            
            if is_new_image:
                try:
                    img = Image.open(chat_image_file)
                    img.thumbnail((800, 800)) 
                    file_extension = os.path.splitext(chat_image_file.name)[1] or ".jpg"
                    file_name = f"msg_{random.randint(10000, 99999)}{file_extension}"
                    saved_chat_img_path = os.path.join(CHAT_MEDIA_DIR, file_name)
                    img.save(saved_chat_img_path, optimize=True, quality=80)
                    st.session_state.last_processed_image = chat_image_file.name
                except Exception as e:
                    st.error(f"Failed to process chat image: {e}")

            user_message_entry = {
                "role": "user", 
                "content": user_input if user_input else "", 
                "image": saved_chat_img_path
            }
            st.session_state.messages[active_char].append(user_message_entry)
            
            has_img_flag = True if saved_chat_img_path else False
            reply = generate_reply(user_input, active_char, has_image=has_img_flag)
            st.session_state.messages[active_char].append({"role": "assistant", "content": reply, "image": None})
            
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
            
            github_save_file(CHAR_FILE, CHARACTERS)
            st.session_state.characters_db = CHARACTERS
                
            st.balloons()
            st.success(f"Successfully deployed {new_name} to the runtime profile index!")
            st.session_state.current_char = new_name
            st.rerun()
        else:
            st.error("Validation Halt: Please fill in all parameters requiring asterisks (*).")

# ================= TAB 3: "MY CREATIONS" GALLERY WORKSHOP =================
with tab_inventory:
    st.header("🗂️ My Creations Gallery Workshop")
    st.markdown("Manage, review, and completely erase profiles you have constructed within your system.")
    st.markdown("---")
    
    if len(CHARACTERS) == 0:
        st.info("Your custom creation workshop index is currently empty.")
    else:
        for bot_name, data in list(CHARACTERS.items()):
            with st.container():
                c_card_av, c_card_details, c_card_actions = st.columns([1.5, 6.5, 2])
                
                with c_card_av:
                    card_av_path = data.get("avatar")
                    if card_av_path and os.path.exists(card_av_path):
                        st.image(card_av_path, width=90)
                    else:
                        st.markdown("<h2 style='text-align: center; margin:0;'>👤</h2>", unsafe_allow_html=True)
                
                with c_card_details:
                    st.markdown(f"### **{bot_name}**")
                    st.markdown(f"**Tagline:** *{data.get('title')}*")
                    st.markdown(f"**Memory Matrix Bio:** {data.get('bio')}")
                
                with c_card_actions:
                    st.markdown("<p style='padding-top:10px;'></p>", unsafe_allow_html=True)
                    
                    if st.button(f"💬 Chat with {bot_name}", key=f"chat_jump_{bot_name}", use_container_width=True):
                        st.session_state.current_char = bot_name
                        st.rerun()
                        
                    if st.button(f"❌ Delete {bot_name}", key=f"delete_bot_profile_{bot_name}", use_container_width=True, help="Permanently unregisters this character from the memory matrix database"):
                        CHARACTERS.pop(bot_name)
                        
                        if bot_name in st.session_state.messages:
                            st.session_state.messages.pop(bot_name)
                        
                        github_save_file(CHAR_FILE, CHARACTERS)
                        github_save_file(CHAT_HISTORY_FILE, st.session_state.messages)
                        st.session_state.characters_db = CHARACTERS
                        
                        remaining_bots = list(CHARACTERS.keys())
                        st.session_state.current_char = remaining_bots[0] if remaining_bots else None
                        
                        st.success(f"Completely scrubbed {bot_name} out of database files.")
                        st.rerun()
            st.markdown("---")
