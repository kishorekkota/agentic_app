import streamlit_authenticator as stauth

passwords_1 = list(['123', '456'])

hashed_passwords = stauth.Hasher(passwords_1).hash_list()

print(hashed_passwords)