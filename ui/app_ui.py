import streamlit as st
import os
import requests
from assistant_api import chatbot_response
from utils import end_chat
from utils import load_sidebar



st.title("HR ChatBot")

st.sidebar.header("History")

load_sidebar()

# Create session state variables to store new chat flag.
if 'new_chat' not in st.session_state:
    st.session_state.new_chat = True
    
# Building a container for chat input, chat button, and end button.
col1, col2, col3 = st.columns([4, 1, 1])
with st.container():
    with col1:
        user_input = st.chat_input(placeholder="Please enter your question here...", key="input_text")
    with col2:
        chat_button = st.button(label="Chat", key="chat_button",use_container_width=True)
    with col3:
        end_button = st.button(label="End", key="end_button",on_click=end_chat,use_container_width=True)


if 'history' not in st.session_state:
    st.session_state.history = []

if user_input:
    st.session_state.history.append({"message": user_input, "is_user": True})
    try:
        print("user_input: ", user_input + " new_chat: ", st.session_state.new_chat)
        chat_response = chatbot_response(user_input, st.session_state.new_chat, st.session_state.thread_id if 'thread_id' in st.session_state else "")
        st.session_state.history.append({"message": chat_response.get("response"), "is_user": False})
        st.session_state.new_chat = False
        st.session_state.thread_id = chat_response.get("thread_id")
        print(st.session_state.new_chat)
        print(st.session_state.thread_id)
    except requests.exceptions.RequestException as e:
        st.error(f"Error: {e}")

for message in st.session_state.history:
    if message.get("is_user"):
        st.write("You: "+message.get("message"))
    else:
        st.markdown(f"<b>{message.get('message')}</b>", unsafe_allow_html=True)



