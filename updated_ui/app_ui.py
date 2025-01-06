import streamlit as st
import os
import requests
import logging
import json
from environment_variables import EnvironmentVariables
from assistant_api import chatbot_request, validate_client_id
from utils import end_chat, load_sidebar, user_feedback
from langsmith import Client
from validations import is_valid_us_state
from display_chat_history import display_chat_history
from streamlit_extras.stylable_container import stylable_container

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# Load environment variables
hosted = os.getenv("HOSTED")
profile = os.getenv("PROFILE")
env = EnvironmentVariables.create_instance(hosted, profile)

langsmith_client = Client(api_key=env.langchain_api_key)

# Set page configuration
st.set_page_config(page_title="Paychex ChatBot", layout="wide")

# Custom CSS for styling
st.markdown(
    """
    <style>
    .chat-input-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .chat-input {
        width: 80%;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #ccc;
        font-size: 16px;
        background-color: #003366;
    }
    .chat-button {
        padding: 10px 20px;
        background-color: #004F8F;
        color: white;
        border: none;
        border-radius: 5px;
        cursor: pointer;
        font-size: 16px;
    }
    .chat-button:hover {
        background-color: #003366;
    }
    .stDecoration {
        background-image: linear-gradient(90deg, rgb(167, 199, 231), #004f8f)
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("HR ChatBot")
st.logo("logo-paychex.svg", size="medium", link=None, icon_image=None)

logger.debug(" st.query_params %s ", st.query_params)

# Sidebar content
def load_sidebar_content():
    logger.debug("load_sidebar_content")
    with st.sidebar:
        st.markdown("## Helpful Info")
        try:
            with open("config/hrbot_config.json", "r") as config_file:
                config = json.load(config_file)
                knowledge_categories = config.get("knowledge_categories", [])
                tools = config.get("tools", [])
                
                st.markdown(" Welcome to the HR ChatBot! As of today we can only answer questions about the following topics:")
                st.markdown("### Knowledge Categories")
                
                for category in knowledge_categories:
                    st.markdown(f"- **{category.capitalize()}**")

                st.markdown("### Tools")
                for tool in tools:
                    st.markdown(f"- **{tool.capitalize()}**")
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
            st.error("Error loading sidebar content. Please try again later.")

# Initialize session state
def initialize_session_state():
    logger.debug("initialize_session_state")

    if 'history' not in st.session_state:
        st.session_state.history = []
        st.session_state.source = []
        st.session_state.username = "user_abc"
        st.session_state.thread_id = ""
        st.session_state.additional_info_needed = False
        st.session_state.answer_input = None
        st.session_state.client_id_available = None
        st.session_state.client_id = ""
        st.session_state.scope = ""
        st.session_state.client_industry = ""
        st.session_state.client_state = ""
        st.session_state.client_id_invalid = False
        st.session_state.client_id_reset = False
        logger.debug("Initialized session state variables")

    if 'new_chat' not in st.session_state:
        st.session_state.new_chat = True
        logger.debug("Set new_chat to True")

# Display client information
def display_client_info():
    logger.debug("display_client_info")
    col1, col2, col3 = st.columns([2, 1, 3])
    with col1:
        st.markdown(f"**Paychex Client ID:** {st.session_state.client_id if st.session_state.client_id else 'N/A'}")
    with col2:
        st.markdown(f"**State:** {st.session_state.client_state if st.session_state.client_state else 'N/A'}")
    with col3:
        st.markdown(f"**Industry:** {st.session_state.client_industry if st.session_state.client_industry else 'N/A'}")

# Handle client ID input
def handle_client_id_input():
    logger.debug("handle_client_id_input")
    client_id_container = st.empty()
    if not st.session_state.client_id:
        logger.debug("Client ID not found in session state")
        logger.debug("client client_id_available %s", st.session_state.client_id_available)

        with client_id_container:
            st.session_state.client_id_available = st.radio(
                "Do you have a Paychex Client ID?",
                ("Yes", "No"),
                index=None
            )

            if st.session_state.client_id_reset:
                st.session_state.client_id_available = None
                st.session_state.client_id_reset = False

            logger.debug("Client ID availability selected: %s", st.session_state.client_id_available)

            if st.session_state.client_id_available == "Yes":
                client_id = st.text_input("Please enter your Paychex Client ID")
                if client_id:
                    logger.debug("client id provided by user, validate with backend.")
                    st.session_state.client_id = client_id
                    client_id_container.empty() 
                        
            if st.session_state.client_id_available == "No":
                client_id_container.empty()  # Clear the container
    else:
        if st.session_state.client_id_invalid:
            with client_id_container:
                st.markdown(f"***Client ID Not Found:** Please enter valid client id.*")
                logger.debug("Markdown should have been written")
                st.session_state.client_id_available = st.radio(
                    "Do you have a Paychex Client ID?",
                    ("Yes", "No"),
                    index=0
                )
                logger.debug("Client ID availability selected: %s", st.session_state.client_id_available)

                if st.session_state.client_id_available == "Yes":
                    client_id = st.text_input("Please enter your Paychex Client ID")
                    if client_id:
                        logger.debug("client id provided by user, validate with backend.")
                        st.session_state.client_id = client_id
                        st.session_state.client_id_invalid = False
                        query = st.session_state.history[-2].get('message')
                        logger.debug(" most recent query message is %s", query)
                        submit_request_to_backend(query)
                        client_id_container.empty() 
                            
                if st.session_state.client_id_available == "No":
                    client_id_container.empty()  # Clear the container
        else:
            client_id_container.empty()  # Clear the container

# Handle user input
def handle_user_input():
    logger.debug("handle_user_input")

    with stylable_container(
        key="green_button",
        css_styles="""
            button {
                background-color: #004F8F;
                color: white;
                border-radius: 20px;
            }
            textarea {
                background-color: white;
            }
            background-color: white;
            """
    ):
        col1, col2 = st.columns([5, 1])
        with st.container():
            with col1:
                user_input = st.chat_input(placeholder="Please enter your question/response here...")
                logger.debug("User input: %s", user_input)
            with col2:
                if st.button(label="End", key="end_button", use_container_width=True):
                    st.session_state.client_id = None
                    st.session_state.input_text = ""
                    st.session_state.history = []
                    st.session_state.new_chat = True
                    st.session_state.client_industry = ""
                    st.session_state.client_state = ""
                    st.session_state.client_id_available = None
                    st.session_state.client_id_reset = True
                    logger.debug(" st.session_state.client_id_available %s", st.session_state.client_id_available)
                    logger.debug("End button clicked")
                    st.rerun()

    if user_input:
        submit_request_to_backend(user_input)

# Submit request to backend
def submit_request_to_backend(user_input):
    logger.debug("submit_request_to_backend")
    st.session_state.history.append({"message": user_input, "is_user": True})
    logger.debug("Appended user input to history: %s", user_input)
    try:
        logger.info("Sending chat request with user_input: %s, new_chat: %s, thread_id: %s, scope: %s, username: %s",
                    user_input, st.session_state.new_chat, st.session_state.thread_id, st.session_state.scope, st.session_state.username)

        chat_response = chatbot_request(
            user_input,
            st.session_state.new_chat,
            st.session_state.thread_id if 'thread_id' in st.session_state else "",
            st.session_state.scope,
            st.session_state.username if 'username' in st.session_state else "",
            st.session_state.additional_info_needed,
            st.session_state.client_state,
            st.session_state.client_industry,
            st.session_state.client_id
        )
        st.session_state.history.append({"message": chat_response["answer"], "is_user": False, 
                                         "sources": chat_response["sources"], 
                                         "additional_info_needed": chat_response.get("additional_info_needed"),
                                         "classification": chat_response.get("classification")})
        st.session_state.new_chat = False
        st.session_state.thread_id = chat_response.get("thread_id")
        st.session_state.run_id = chat_response.get("run_id")
        st.session_state.additional_info_needed = chat_response.get("additional_info_needed")
        st.session_state.answer_input = None

        if chat_response.get("client_state") and chat_response.get("client_state") != "":
            logger.debug(chat_response.get("client_state"))
            st.session_state.client_state = chat_response.get("client_state")

        if chat_response.get("client_industry") and chat_response.get("client_industry") != "":
            logger.debug(chat_response.get("client_industry"))
            st.session_state.client_industry = chat_response.get("client_industry")
            st.rerun()

        if st.session_state.additional_info_needed and st.session_state.client_id and st.session_state.client_id != "":
            st.session_state.client_id_invalid = True
            st.session_state.additional_info_needed = False
            st.rerun()

        logger.debug("Chat response received: %s", chat_response["answer"])
        logger.debug("Updated session state: new_chat: %s, thread_id: %s, run_id: %s", st.session_state.new_chat, st.session_state.thread_id, st.session_state.run_id)
    except requests.exceptions.RequestException as e:
        logger.error("RequestException occurred: %s", e)
        st.error(f"Error: {e}")

# Main function
def main():
    logger.debug("main")

    load_sidebar_content()
    initialize_session_state()
    handle_client_id_input()
    display_client_info()
    handle_user_input()
    display_chat_history()

    # JavaScript to scroll to the bottom of the chat window
    st.markdown(
        """
        <script>
        function scrollToBottom() {
            var chatWindow = document.getElementsByClassName('st-key-chat-window')[0];
            chatWindow.scrollTop = chatWindow.scrollHeight;
        }
        window.onload = scrollToBottom;
        </script>
        """,
        unsafe_allow_html=True
    )

    if not st.session_state.additional_info_needed:
        st.session_state.answer_input = None
        logger.debug("No additional information needed")

if __name__ == "__main__":
    main()