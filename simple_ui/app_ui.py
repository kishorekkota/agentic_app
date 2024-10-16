import streamlit as st
import requests


CHATBOT_API_URL = 'http://localhost:8000/chat'


st.title("Simple ChatBot UI")

# Create session state variables to store new chat flag.
if 'new_chat' not in st.session_state:
    st.session_state.new_chat = True

def chatbot_response(user_input,new_chat):
    """
    Sends a user's input to the chatbot API and retrieves the response.

    Parameters:
    user_input (str): The message from the user to be sent to the chatbot.

    Returns:
    str: The response from the chatbot.

    Raises:
    requests.exceptions.RequestException: If there is an error with the HTTP request.
    """
    response = requests.post(CHATBOT_API_URL, json={"message": user_input, "new_chat": new_chat})
    response.raise_for_status()
    return response.json()["response"]

def end_chat():
    """
    Resets the chat session state to start a new chat.

    This function clears the current input text, chat history, and sets the 
    new_chat flag to True, indicating the beginning of a new chat session.
    """
    st.session_state.input_text = ""
    st.session_state.history = []
    st.session_state.new_chat = True
    

# Building a container for chat input, chat button, and end button.
col1, col2, col3 = st.columns([4, 1, 1])
with st.container():
    with col1:
        user_input = st.text_input(label="You:", placeholder="Please enter your question here...", key="input_text")
    with col2:
        chat_button = st.button(label="Chat", key="chat_button")
    with col3:
        end_button = st.button(label="End", key="end_button",on_click=end_chat)




if 'history' not in st.session_state:
    st.session_state.history = []


if user_input:
    st.session_state.history.append({"message": user_input, "is_user": True})
    try:
        print("user_input: ", user_input + " new_chat: ", st.session_state.new_chat)
        chat_response = chatbot_response(user_input, st.session_state.new_chat)
        st.session_state.history.append({"message": chat_response, "is_user": False})
        st.session_state.new_chat = False
        print(st.session_state.new_chat)
    except requests.exceptions.RequestException as e:
        st.error(f"Error: {e}")


for message in st.session_state.history:
    if message.get("is_user"):
        st.write("You: "+message.get("message"))
    else:
        st.markdown(f"<b>{message.get('message')}</b>", unsafe_allow_html=True)



