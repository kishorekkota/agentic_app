# main.py

import streamlit as st
from authentication import login
from layout import initialize_ui, display_chat_interface, display_chat_history
from chatbot import process_user_input
from utils import load_sidebar
import logging

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def main():
    # Authenticate user
    user = login()
    if user['authenticated']:
        st.session_state.username = user['username']
        # Initialize UI components
        initialize_ui()
        # Load sidebar
        load_sidebar()
        # Display chat interface
        user_input = display_chat_interface()
        # Process user input
        if user_input:
            process_user_input(user_input)
        # Display chat history and feedback forms
        display_chat_history()
    else:
        st.error("Please log in to use the chatbot.")

if __name__ == "__main__":
    main()