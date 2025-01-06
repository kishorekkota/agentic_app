import streamlit as st
import os
import requests
import logging
from environment_variables import EnvironmentVariables

# Load environment variables
hosted = os.getenv("HOSTED")
profile = os.getenv("PROFILE")
env = EnvironmentVariables.create_instance(hosted, profile)

from assistant_api import chatbot_request,validate_client_id
from utils import end_chat, load_sidebar, user_feedback
from langsmith import Client
from validations import is_valid_us_state
from display_chat_history import display_chat_history
from streamlit_extras.stylable_container import stylable_container

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

langsmith_client = Client(api_key=env.langchain_api_key)
# st.set_page_config(page_title="HR ChatBot")
st.title("HR ChatBot")
st.logo("logo-paychex.svg", size="medium", link=None, icon_image=None)


logger.debug(" st.query_params %s ", st.query_params)

# Sidebar content
def load_sidebar_content():
    with st.sidebar:
        st.markdown("## Helpful Info")
        st.markdown("""
        Welcome to the HR ChatBot! As of today we can only answer questions about the following topics:
        
        - **Wage & Hour**: Ask about wage and hour policies.
        - **Overtime**: Inquire about overtime rules and regulations.
        - **Sick Leave**: Get information on sick leave policies.
        
        If you need further assistance, please contact HR support.
        """)

# Initialize session state
def initialize_session_state():
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
        logger.debug("Initialized session state variables")

    if 'new_chat' not in st.session_state:
        st.session_state.new_chat = True
        logger.debug("Set new_chat to True")

# Display client information
def display_client_info():
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"**Paychex Client ID:** {st.session_state.client_id if st.session_state.client_id else 'N/A'}")
    with col2:
        st.markdown(f"**State:** {st.session_state.client_state if st.session_state.client_state else 'N/A'}")
    with col3:
        st.markdown(f"**Industry:** {st.session_state.client_industry if st.session_state.client_industry else 'N/A'}")

# Handle client ID input
def handle_client_id_input():
    client_id_container = st.empty()
    if not st.session_state.client_id:
        logger.debug("Client ID not found in session state")
        with client_id_container:
            st.session_state.client_id_available = st.radio(
                "Do you have a Paychex Client ID?",
                ("Yes", "No"),
                index=None
            )
            logger.debug("Client ID availability selected: %s", st.session_state.client_id_available)

            if st.session_state.client_id_available == "Yes":
                client_id = st.text_input("Please enter your Paychex Client ID")
                if client_id:
                    logger.debug("client id provided by user, validate with backend.")
                    st.session_state.client_id = client_id
                    client_id_container.empty()  # Clear the container
                    # verify_client_id_response = validate_client_id(client_id,scope=st.session_state.scope,username="")
                    # logger.debug("Backend verfication response %s",verify_client_id_response)

                    # if verify_client_id_response.get("client_state") and verify_client_id_response.get("client_state") != "":
                    #     logger.debug(verify_client_id_response.get("client_state"))
                    #     st.session_state.client_state = verify_client_id_response.get("client_state")

                    # if verify_client_id_response.get("client_industry") and verify_client_id_response.get("client_industry") != "":
                    #     logger.debug(verify_client_id_response.get("client_industry"))
                    #     st.session_state.client_industry = verify_client_id_response.get("client_industry")
                    #     st.rerun()
                        
            if st.session_state.client_id_available == "No":
                client_id_container.empty()  # Clear the container
    else:
        client_id_container.empty()  # Clear the container

# Handle user input
def handle_user_input():
    
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
            """
    ):
        col1, col2 = st.columns([5, 1])
        with st.container():
            with col1:
                user_input = st.chat_input(placeholder="Please enter your question/response here...")
                logger.debug("User input: %s", user_input)
            with col2:
                end_button = st.button(label="End", key="end_button", on_click=end_chat, use_container_width=True)
                logger.debug("End button rendered")

    if user_input:
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
            st.session_state.history.append({"message": chat_response["answer"], "is_user": False, "sources": chat_response["sources"], "additional_info_needed": chat_response.get("additional_info_needed")})
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

            logger.debug("Chat response received: %s", chat_response["answer"])
            logger.debug("Updated session state: new_chat: %s, thread_id: %s, run_id: %s", st.session_state.new_chat, st.session_state.thread_id, st.session_state.run_id)
        except requests.exceptions.RequestException as e:
            logger.error("RequestException occurred: %s", e)
            st.error(f"Error: {e}")

# Main function
def main():
    load_sidebar_content()
    initialize_session_state()
    handle_client_id_input()
    display_client_info()
    handle_user_input()
    display_chat_history()

    if not st.session_state.additional_info_needed:
        st.session_state.answer_input = None
        logger.debug("No additional information needed")

if __name__ == "__main__":
    main()