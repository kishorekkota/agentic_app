# authentication.py

import streamlit as st
import streamlit_authenticator as stauth

def login():
    # User credentials
    names = ["John Doe", "Jane Smith"]
    usernames = ["johndoe", "janesmith"]
    passwords = ["password123", "mysecurepassword"]  # Replace with secure passwords

    # Hash passwords
    hashed_passwords = stauth.Hasher(passwords).hash_passwords()

    # Credentials dictionary
    credentials = {
        'usernames': {
            usernames[i]: {
                'name': names[i],
                'password': hashed_passwords[i],
            } for i in range(len(usernames))
        }
    }

    # Authenticator instance
    authenticator = stauth.Authenticate(
        credentials,
        'chatbot_cookie',
        'some_signature_key',
        cookie_expiry_days=1
    )

    # Login widget
    name, authentication_status, username = authenticator.login('Login', 'main')

    if authentication_status:
        return {'authenticated': True, 'username': username}
    elif authentication_status == False:
        st.error('Username/password is incorrect')
    elif authentication_status == None:
        st.warning('Please enter your username and password')
    return {'authenticated': False, 'username': None}