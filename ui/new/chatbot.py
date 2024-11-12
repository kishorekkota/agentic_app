# chatbot.py

import streamlit as st
import logging
from assistant_api import chatbot_request
from datetime import datetime

logger = logging.getLogger(__name__)

def process_user_input(user_input):
    try:
        logger.info(f"User input: {user_input}")
        chat_response = chatbot_request(
            user_input,
            st.session_state.new_chat,
            st.session_state.thread_id or "",
            st.session_state.scope,
            st.session_state.username or ""
        )

        st.session_state.history.append({"message": user_input, "is_user": True})
        st.session_state.history.append({
            "message": chat_response.get("response"),
            "is_user": False,
            "timestamp": datetime.utcnow().isoformat(),
            "feedback_given": False
        })
        st.session_state.new_chat = False
        st.session_state.thread_id = chat_response.get("thread_id")
        st.session_state.run_id = chat_response.get("run_id")

        logger.info("Chatbot response added to history.")

    except Exception as e:
        logger.error(f"Error processing user input: {e}")
        st.error(f"Error: {e}")