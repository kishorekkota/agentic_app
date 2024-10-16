import streamlit as st
import requests

st.title("Simple ChatBot UI")

col1, col2, col3 = st.columns([4, 1, 1])

if 'new_chat' not in st.session_state:
    st.session_state.new_chat = True

def end_chat():
    st.session_state.input_text = ""
    st.session_state.history = []
    st.session_state.new_chat = True
    

with st.container():
    with col1:
        user_input = st.text_input(label="You:", placeholder="Please enter your question here...", key="input_text")
    with col2:
        chat_button = st.button(label="Chat", key="chat_button")
    with col3:
        end_button = st.button(label="End", key="end_button",on_click=end_chat)

url = 'http://localhost:8000/chat'


if 'history' not in st.session_state:
    st.session_state.history = []


if user_input:
    st.session_state.history.append({"message": user_input, "is_user": True})
    try:
        print("user_input: ", user_input + " new_chat: ", st.session_state.new_chat)
        chat_response = requests.post(url, json={"message": user_input, "new_chat": st.session_state.new_chat})
        chat_response.raise_for_status()
        st.session_state.history.append({"message": chat_response.json()["response"], "is_user": False})
        st.session_state.new_chat = False
        print(st.session_state.new_chat)
    except requests.exceptions.RequestException as e:
        st.error(f"Error: {e}")


for message in st.session_state.history:
    if message.get("is_user"):
        st.write("You: "+message.get("message"))
    else:
        st.markdown(f"<b>{message.get('message')}</b>", unsafe_allow_html=True)



def chatbot_response(user_input):
    # Placeholder logic for response
    response = requests.post(url, json={"message": user_input, "new_chat": st.session_state.new_chat})
    return response.json()["response"]