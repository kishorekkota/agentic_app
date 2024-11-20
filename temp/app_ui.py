import streamlit as st
import os
import requests
import logging
from environment_variables import EnvironmentVariables

# Load environment variables
hosted = os.getenv("HOSTED")
profile = os.getenv("PROFILE")
env = EnvironmentVariables.create_instance(hosted, profile)

from assistant_api import chatbot_request
from utils import end_chat, load_sidebar
from langsmith import Client
from validations import is_valid_us_state

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

langsmith_client = Client(api_key=env.langchain_api_key)

st.title("HR ChatBot")

st.sidebar.header("History")

load_sidebar()

# Initialization of session state
if 'history' not in st.session_state:
    st.session_state.history = []
    st.session_state.username = "user_abc"
    st.session_state.thread_id = ""
    st.session_state.additional_info_needed = False
    st.session_state.answer_input = None

# Create session state variables to store new chat flag.
if 'new_chat' not in st.session_state:
    st.session_state.new_chat = True

choices = ["Wage&Hour", "Overtime", "Sick Leave"]

# Create a tab-like interface for choices
tabs = st.tabs(choices)
for i, tab in enumerate(tabs):
    with tab:
        st.session_state.scope = choices[i]
        st.write(f"Selected: {choices[i]}")

# Building a container for chat input, chat button, and end button.
col1, col2, col3 = st.columns([4, 1, 1])
with st.container():
    with col1:
        user_input = st.chat_input(placeholder="Please enter your question here...")
    with col2:
        chat_button = st.button(label="Chat", key="chat_button", use_container_width=True)
    with col3:
        end_button = st.button(label="End", key="end_button", on_click=end_chat, use_container_width=True)

if user_input:
    st.session_state.history.append({"message": user_input, "is_user": True})
    try:
        logger.info(f"user_input: {user_input}, new_chat: {st.session_state.new_chat}, thread_id: {st.session_state.thread_id}, scope: {st.session_state.scope}, username: {st.session_state.username}")
        
        chat_response = chatbot_request(
            user_input, 
            st.session_state.new_chat, 
            st.session_state.thread_id if 'thread_id' in st.session_state else "", 
            st.session_state.scope,
            st.session_state.username if 'username' in st.session_state else "",
            st.session_state.additional_info_needed 
        )
        
        st.session_state.history.append({"message": chat_response["answer"], "is_user": False})
        st.session_state.new_chat = False
        st.session_state.thread_id = chat_response.get("thread_id")
        st.session_state.run_id = chat_response.get("run_id")
        st.session_state.additional_info_needed = chat_response.get("additional_info_needed")
        st.session_state.answer_input = None

        logger.debug(f"new_chat: {st.session_state.new_chat}, thread_id: {st.session_state.thread_id}, run_id: {st.session_state.run_id}")
    except requests.exceptions.RequestException as e:
        logger.error(f"RequestException occurred: {e}")
        st.error(f"Error: {e}")

if st.session_state.additional_info_needed:
    if st.session_state.answer_input:
        try:
            chat_response = chatbot_request(
                st.session_state.answer_input, 
                st.session_state.new_chat, 
                st.session_state.thread_id if 'thread_id' in st.session_state else "", 
                st.session_state.scope,
                st.session_state.username if 'username' in st.session_state else "",
                st.session_state.additional_info_needed 
            )
            
            st.session_state.history.append({"message": chat_response["answer"], "is_user": False})
            st.session_state.new_chat = False
            st.session_state.thread_id = chat_response.get("thread_id")
            st.session_state.run_id = chat_response.get("run_id")
            st.session_state.additional_info_needed = chat_response.get("additional_info_needed")

            logger.debug(f"new_chat: {st.session_state.new_chat}, thread_id: {st.session_state.thread_id}, run_id: {st.session_state.run_id}")
        except requests.exceptions.RequestException as e:
            logger.error(f"RequestException occurred: {e}")
            st.error(f"Error: {e}")

for idx, message in enumerate(st.session_state.history):
    if message.get("is_user"):
        st.write("You: " + message.get("message"))
    else:
        st.markdown(f"<b>{message.get('message')}</b>", unsafe_allow_html=True)

        if st.session_state.additional_info_needed and (idx + 1) == len(st.session_state.history):
            st.session_state.answer_input = st.text_input(placeholder="Please enter your response here...", label='Please provide your response', key=f'response_{idx}')

        if st.session_state.history[idx].get('run_id') is None:
            st.session_state.history[idx]['run_id'] = st.session_state.run_id
        
        feedback_given = message.get('feedback_given', False)
        if not feedback_given:
            # Create a form for feedback
            with st.expander("Provide Feedback", expanded=False):
                with st.form(key=f"feedback_form_{idx}"):
                    # Feedback selection
                    feedback_choice = st.radio(
                        "Please provide your feedback:",
                        ('👍 Positive', '👎 Negative'),
                        key=f'feedback_choice_{idx}'
                    )
                    # Comment field
                    comment = st.text_area("Add a comment (optional):", key=f'comment_{idx}')
                    # Submit button
                    submit_feedback = st.form_submit_button('Submit Feedback')
                    
                    if submit_feedback:
                        # Determine feedback score based on selection
                        feedback_score = 1 if feedback_choice == '👍 Positive' else 0
                        # Prepare feedback data
                        feedback = {
                            'user': st.session_state.username,
                            'message': message.get('message'),
                            'feedback': 'positive' if feedback_score == 5 else 'negative',
                            'timestamp': message.get('timestamp'),
                            'comment': comment
                        }
                        # Send feedback using langsmith_client
                        langsmith_client.create_feedback(
                            key='feedback_key',
                            score=feedback_score,
                            comment=comment,
                            run_id=st.session_state.history[idx].get('run_id')
                        )
                        st.success("Thank you for your feedback!")
                        st.session_state.history[idx]['feedback_given'] = True
        else:
            st.write("Feedback received. Thank you!")

if not st.session_state.additional_info_needed:
    st.session_state.answer_input = None