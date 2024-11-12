# feedback.py

import streamlit as st
from langsmith import Client
import os

langsmith_client = Client(api_key=os.getenv('LANGSMITH_API_KEY'))

def display_feedback_form(idx, message):
    feedback_given = message.get('feedback_given', False)
    if not feedback_given:
        with st.form(key=f"feedback_form_{idx}"):
            feedback_choice = st.radio(
                "Please provide your feedback:",
                ('👍 Positive', '👎 Negative'),
                key=f'feedback_choice_{idx}'
            )
            comment = st.text_area("Add a comment (optional):", key=f'comment_{idx}')
            submit_feedback = st.form_submit_button('Submit Feedback')
            if submit_feedback:
                submit_feedback_data(idx, feedback_choice, comment, message)
    else:
        st.write("Feedback received. Thank you!")

def submit_feedback_data(idx, feedback_choice, comment, message):
    feedback_score = 5 if feedback_choice == '👍 Positive' else 1
    langsmith_client.create_feedback(
        key='feedback_key',
        score=feedback_score,
        comment=comment,
        run_id=st.session_state.run_id
    )
    st.success("Thank you for your feedback!")
    st.session_state.history[idx]['feedback_given'] = True