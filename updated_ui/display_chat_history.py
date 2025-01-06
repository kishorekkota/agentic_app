import streamlit as st
import logging
from utils import end_chat, load_sidebar, user_feedback
from langsmith import Client
from environment_variables import EnvironmentVariables
from download_doc import generate_doc
from download_pdf import generate_pdf
import uuid

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

env = EnvironmentVariables.get_instance()
langsmith_client = Client(api_key=env.langchain_api_key)

def display_references(sources):
    logger.debug("rendering reference... %s", sources)
    with st.expander("Reference", expanded=False):
        if sources:
            for ref in sources:
                title = ref.get('title')
                url = ref.get('url')
                st.markdown(f"[{title}]({url})")

def display_feedback_form(index, message):
    logger.debug("display_feedback_form index %s", index)
    feedback_given = message.get('feedback_given', False)

    st.markdown(
        """
        <style>
        .stExapnder {
            display: closed;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    if not feedback_given:
        with st.expander("Provide Feedback", expanded=False):
            with st.form(key=f"feedback_form_{index}"):
                col1, col2 = st.columns([1, 1])
                with col1:
                    feedback_choice_accuracy = st.radio(
                        "The response accurately answered my question:",
                        ('👍 Positive', '👎 Negative'),
                        key=f'feedback_choice_accuracy_{index}', horizontal=True
                    )
                    feedback_choice_detailed = st.radio(
                        "The response was detailed enough:",
                        ('👍 Positive', '👎 Negative'),
                        key=f'feedback_choice_detailed_{index}', horizontal=True
                    )
                    feedback_choice_relevant = st.radio(
                        "The references were relevant to the question:",
                        ('👍 Positive', '👎 Negative'),
                        key=f'feedback_choice_relevant_{index}', horizontal=True
                    )
                with col2:
                    comment = st.text_area("Add a comment:", key=f'comment_{index}')
                    submit_feedback = st.form_submit_button('Submit Feedback')

                    if submit_feedback:
                        feedback_choice_accuracy_score = 1 if feedback_choice_accuracy == '👍 Positive' else 0
                        feedback_choice_detailed_score = 1 if feedback_choice_detailed == '👍 Positive' else 0
                        feedback_choice_relevant_score = 1 if feedback_choice_relevant == '👍 Positive' else 0

                        feedback = {
                            'user': st.session_state.username,
                            'message': message.get('message'),
                            'accuracy_score': feedback_choice_accuracy_score,
                            'detailed_score': feedback_choice_detailed_score,
                            'relevant_score': feedback_choice_relevant_score,
                            'timestamp': message.get('timestamp'),
                            'comment': comment
                        }

                        logger.debug("Writing feedback for %s", st.session_state.history[index])

                        langsmith_client.create_feedback(
                            key='feedback_choice_accuracy_score',
                            score=feedback_choice_accuracy_score,
                            comment='',
                            run_id=st.session_state.history[index].get('run_id')
                        )
                        langsmith_client.create_feedback(
                            key='feedback_choice_detailed_score',
                            score=feedback_choice_detailed_score,
                            comment='',
                            run_id=st.session_state.history[index].get('run_id')
                        )
                        langsmith_client.create_feedback(
                            key='feedback_choice_relevant_score',
                            score=feedback_choice_relevant_score,
                            comment='',
                            run_id=st.session_state.history[index].get('run_id')
                        )
                        langsmith_client.create_feedback(
                            key='feedback_comment',
                            score=1,
                            comment=comment,
                            value=comment,
                            run_id=st.session_state.history[index].get('run_id')
                        )
                        st.success("Thank you for your feedback!")
                        st.session_state.history[index]['feedback_given'] = True
                        logger.debug(f"Feedback submitted: {feedback}")
    else:
        st.write("Feedback received. Thank you!")

def display_chat_history():
    history_len = len(st.session_state.history)

    with st.container(height=400, key='chat-window'):
        for idx, message in enumerate(reversed(st.session_state.history)):
            logger.debug(" chat history messages %s %s", message, idx)
            if message.get("is_user"):
                st.write("You: " + message.get("message"))
            else:
                escaped_message = message.get("message").replace("$", "&#36;")
                escaped_message = escaped_message.replace("\n", "<br>")
                st.markdown(f"{escaped_message}", unsafe_allow_html=True)

                if st.session_state.history[history_len-idx-1].get('run_id') is None:
                    st.session_state.history[history_len-idx-1]['run_id'] = st.session_state.run_id

                if st.session_state.history[history_len-idx-1].get('classification') == 'job descriptions':
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        doc_buffer = generate_doc(st.session_state.history[history_len-idx-1])
                        doc_uuid = uuid.uuid4()
                        st.download_button(
                            label="Download DOC",
                            data=doc_buffer,
                            file_name=f"job_description{doc_uuid}.docx",
                            mime="application/doc",
                            key=f'doc_{history_len-idx-1}'
                        )
                    with col2:
                        # pdf_buffer = generate_pdf(st.session_state.history[history_len-idx-1])
                        # st.download_button(
                        #     label="Download PDF",
                        #     data=pdf_buffer,
                        #     file_name="chat_history.pdf",
                        #     mime="application/pdf",
                        #     key=f'pdf_{history_len-idx-1}'
                        #)
                        logger.debug("Hiding PDF")

                display_references(st.session_state.history[history_len-idx-1].get('sources'))

                if not st.session_state.history[history_len-idx-1].get('additional_info_needed'):
                    display_feedback_form(history_len-idx-1, message)

                logger.debug("classification of the response %s", st.session_state.history[history_len-idx-1].get('classification'))