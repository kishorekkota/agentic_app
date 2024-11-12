# utils.py

import streamlit as st

def end_chat():
    st.session_state.history = []
    st.session_state.new_chat = True
    st.session_state.thread_id = ""
    st.session_state.run_id = ""
    st.success("Chat ended.")

def load_sidebar():
    # Placeholder for sidebar functionality
    pass