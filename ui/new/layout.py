# layout.py

import streamlit as st
from utils import end_chat

def initialize_ui():
    st.title("ChatBot")
    st.sidebar.header("History")
    initialize_session_state()
    display_scope_tabs()

def initialize_session_state():
    if 'history' not in st.session_state:
        st.session_state.history = []
    if 'new_chat' not in st.session_state:
        st.session_state.new_chat = True
    st.session_state.thread_id = ""
    st.session_state.run_id = ""

def display_scope_tabs():
    choices = ["Payroll", "Hiring", "Termination", "Leave", "Benefits", "Others"]
    tabs = st.tabs(choices)
    for i, tab in enumerate(tabs):
        with tab:
            st.session_state.scope = choices[i]
            st.write(f"Selected: {choices[i]}")

def display_chat_interface():
    col1, col2, col3 = st.columns([4, 1, 1])
    with col1:
        user_input = st.chat_input(placeholder="Please enter your question here...")
    with col2:
        st.button(label="Chat", key="chat_button", use_container_width=True)
    with col3:
        st.button(label="End", key="end_button", on_click=end_chat, use_container_width=True)
    return user_input

def display_chat_history():
    from feedback import display_feedback_form
    for idx, message in enumerate(st.session_state.history):
        if message.get("is_user"):
            st.write("You: " + message.get("message"))
        else:
            st.markdown(f"<b>{message.get('message')}</b>", unsafe_allow_html=True)
            display_feedback_form(idx, message)