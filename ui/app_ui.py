import streamlit as st
import os
import requests
import logging
from assistant_api import chatbot_request
from utils import end_chat, load_sidebar
from datetime import datetime
import uuid

from langsmith import Client 

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

langsmith_client = Client(api_key=os.getenv('LANGSMITH_API_KEY'))


st.title("ChatBot")

st.sidebar.header("History")

load_sidebar()

st.session_state.username = "user_abc"
st.session_state.thread_id = ""

# Create session state variables to store new chat flag.
if 'new_chat' not in st.session_state:
    st.session_state.new_chat = True

choices = ["Payroll", "Hiring", "Termination", "Leave", "Benefits", "Others"]

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

if 'history' not in st.session_state:
    st.session_state.history = []

if user_input:
    st.session_state.history.append({"message": user_input, "is_user": True})
    try:
        logger.info(f"user_input: {user_input}, new_chat: {st.session_state.new_chat}, thread_id: {st.session_state.thread_id}, scope: {st.session_state.scope}, username: {st.session_state.username}")
        
        chat_response = chatbot_request(
            user_input, 
            st.session_state.new_chat, 
            st.session_state.thread_id if 'thread_id' in st.session_state else "", 
            st.session_state.scope,
            st.session_state.username if 'username' in st.session_state else ""
        )
        
        st.session_state.history.append({"message": chat_response.get("response"), "is_user": False,"timestamp": datetime.utcnow().isoformat(),
    "feedback_given": False})
        st.session_state.new_chat = False
        st.session_state.thread_id = chat_response.get("thread_id")
        st.session_state.run_id = chat_response.get("run_id")
        
        logger.info(f"Chat response received: {chat_response.get('response')}")
        logger.debug(f"new_chat: {st.session_state.new_chat}, thread_id: {st.session_state.thread_id}")
    except requests.exceptions.RequestException as e:
        logger.error(f"RequestException occurred: {e}")
        st.error(f"Error: {e}")

# for idx, message in enumerate(st.session_state.history):
#     if message.get("is_user"):
#         st.write("You: " + message.get("message"))
#     else:
#         st.markdown(f"<b>{message.get('message')}</b>", unsafe_allow_html=True)
        
#         # Add feedback buttons
#         col1, col2,col3 = st.columns([1,4,1],vertical_alignment="center",gap="small")
#         feedback_given = message.get('feedback_given', False)
#         if not feedback_given:

            
#             with col1:
#                 if st.button('👍', key=f'thumbs_up_{idx}',use_container_width=True):
#                     # Handle thumbs up feedback
                    
#                     feedback = {
#                         'user': st.session_state.username,
#                         'message': message.get('message'),
#                         'feedback': 'positive',
#                         'timestamp': message.get('timestamp')
#                     }
                 
#                     print(st.session_state.run_id)
                    
#                     langsmith_client.create_feedback(key='feedback_key',score=5,comment="",run_id=st.session_state.run_id)
#                     st.success("Thank you for your feedback!")
#                     st.session_state.history[idx]['feedback_given'] = True
#             with col2:
#                 comment_key = f"comment_{idx}"
#                 comment = st.text_input("Comment (optional):", key=comment_key)
#                 # st.markdown(
#                 #     """
#                 #     <div align="center">
#                 # """,
#                 #     unsafe_allow_html=True
#                 # )
#                 # comment = st.text_input("Add a comment (optional):", key=comment_key)
#                 # st.markdown("</div>", unsafe_allow_html=True)

#             with col3:
#                 if st.button('👎', key=f'thumbs_down_{idx}',use_container_width=True):
#                     # Handle thumbs down feedback
#                     feedback = {
#                         'user': st.session_state.username,
#                         'message': message.get('message'),
#                         'feedback': 'negative',
#                         'timestamp': message.get('timestamp')
#                     }
#                     langsmith_client.send_feedback(feedback)
#                     st.success("Thank you for your feedback!")
#                     st.session_state.history[idx]['feedback_given'] = True
#         else:
#             st.write("Feedback received. Thank you!")
# ... [existing imports and code above] ...

for idx, message in enumerate(st.session_state.history):
    if message.get("is_user"):
        st.write("You: " + message.get("message"))
    else:
        st.markdown(f"<b>{message.get('message')}</b>", unsafe_allow_html=True)

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