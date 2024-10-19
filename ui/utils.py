import streamlit as st

def end_chat():
    """
    Resets the chat session state to start a new chat.

    This function clears the current input text, chat history, and sets the 
    new_chat flag to True, indicating the beginning of a new chat session.
    """
    print("Ending chat...")
    st.session_state.input_text = ""
    st.session_state.history = []
    st.session_state.new_chat = True
    

def load_sidebar():
    options = ["My first chat....", "My Second chat...", "My Third chat....","My Fourth chat...."]
   
    for option in options:
        st.sidebar.link_button(option, "XXXXXXXXXXXXXXXXXXXXXX",use_container_width=True)
   