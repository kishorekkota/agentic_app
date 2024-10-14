import streamlit as st
import requests

st.title("Simple ChatBot UI")


url = 'http://localhost:8000/chat'


user_input = st.text_input("You: ", placeholder="Please enter your question here...")


if 'history' not in st.session_state:
    st.session_state.history = []


if user_input:
    st.session_state.history.append({"message": user_input, "is_user": True})

    # chat_response = f"Chatbot: You said {user_input}"
    chat_response = requests.post(url, json={"message": user_input})
    st.session_state.history.append({"message": chat_response.json()["response"], "is_user": False})


for message in st.session_state.history:
    st.write(message)



def chatbot_response(user_input):
    # Placeholder logic for response

    response = requests.post(url, json={"message": user_input})

    return response.json()["response"]