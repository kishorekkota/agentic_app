import streamlit as st
import logging
from utils import end_chat, load_sidebar, user_feedback
from langsmith import Client
import html
from environment_variables import EnvironmentVariables
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from reportlab.lib import utils
from downaload_doc import *
from download_pdf import *

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

env = EnvironmentVariables.get_instance()

langsmith_client = Client(api_key=env.langchain_api_key)

def display_references(sources):
    logger.debug("rendering reference... %s",sources)
    with st.expander("Reference", expanded=False):
        if sources:
            for ref in sources:
                title = ref.get('title')
                url = ref.get('url')
                st.markdown(f"[{title}]({url})")

def display_feedback_form(index, message):
    logger.debug("display_feedback_form index %s",index)
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
                col1,col2 = st.columns([1,1])
                with col1:
                    feedback_choice_accuracy = st.radio(
                        "The response accurately answered my question:",
                        ('👍 Positive', '👎 Negative'),
                        key=f'feedback_choice_accuracy_{index}',horizontal=True
                    )
                    feedback_choice_detailed = st.radio(
                            "The response was detailed enough:",
                            ('👍 Positive', '👎 Negative'),
                            key=f'feedback_choice_detailed_{index}',horizontal=True
                    )
                    feedback_choice_relevant = st.radio(
                                "The references were relevant to the question:",
                                ('👍 Positive', '👎 Negative'),
                                key=f'feedback_choice_relevant_{index}',horizontal=True
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
                            'deatiled_score': feedback_choice_detailed_score,
                            'relevant_score': feedback_choice_relevant_score,
                            'timestamp': message.get('timestamp'),
                            'comment': ''
                        }

                        logger.debug("Writing feedback for %s",st.session_state.history[index])

                        langsmith_client.create_feedback(
                            key='feedback_choice_accuracy_score',
                            score=feedback_choice_accuracy_score,
                            comment='',
                            run_id=st.session_state.history[index].get('run_id')
                            # feedback_config={
                            #     {'accuracy_score': feedback_choice_accuracy_score,
                            #     'deatiled_score': feedback_choice_detailed_score,
                            #     'relevant_score': feedback_choice_relevant_score}}
                        )
                        langsmith_client.create_feedback(
                            key='feedback_choice_detailed_score',
                            score=feedback_choice_detailed_score,
                            comment='',
                            run_id=st.session_state.history[index].get('run_id')
                            # feedback_config={
                            #     {'accuracy_score': feedback_choice_accuracy_score,
                            #     'deatiled_score': feedback_choice_detailed_score,
                            #     'relevant_score': feedback_choice_relevant_score}}
                        )
                        langsmith_client.create_feedback(
                            key='feedback_choice_relevant_score',
                            score=feedback_choice_relevant_score,
                            comment='',
                            run_id=st.session_state.history[index].get('run_id')
                            # feedback_config={
                            #     {'accuracy_score': feedback_choice_accuracy_score,
                            #     'deatiled_score': feedback_choice_detailed_score,
                            #     'relevant_score': feedback_choice_relevant_score}}
                        )
                        langsmith_client.create_feedback(
                            key='feedback_comment',
                            score=1,
                            comment=comment,
                            value=comment,
                            run_id=st.session_state.history[index].get('run_id')
                            # feedback_config={
                            #     {'accuracy_score': feedback_choice_accuracy_score,
                            #     'deatiled_score': feedback_choice_detailed_score,
                            #     'relevant_score': feedback_choice_relevant_score}}
                        )
                        st.success("Thank you for your feedback!")
                        st.session_state.history[index]['feedback_given'] = True
                        logger.debug(f"Feedback submitted: {feedback}")
    else:
        st.write("Feedback received. Thank you!")

def display_chat_history():
    history_len = len(st.session_state.history)


    # st.markdown("""
    #     <style>
    #         .st-container {

    #             width: 8.5in; /* 8.5 inches in pixels */

    #             height: 11in; /* 11 inches in pixels */

    #             margin: auto;

    #         }

    #     </style>
    # """,unsafe_allow_html=True)
    with st.container(height=400,key='chat-window'):
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

                #print(st.session_state.history[idx])
                if st.session_state.history[history_len-idx-1].get('classification') == 'job descriptions':
                    pdf_buffer = generate_pdf(st.session_state.history[history_len-idx-1])
                    st.download_button(
                        label="Download PDF",
                        data=pdf_buffer,
                        file_name="chat_history.pdf",
                        mime="application/pdf",key=f'pdf_{history_len-idx-1}'
                    )

                
                if st.session_state.history[history_len-idx-1].get('classification') == 'job descriptions':
                    doc_buffer = generate_doc(st.session_state.history[history_len-idx-1])
                    st.download_button(
                        label="Download DOC",
                        data=doc_buffer,
                        file_name="chat_history.doc",
                        mime="application/doc",key=f'doc_{history_len-idx-1}'
                    )

                display_references(st.session_state.history[history_len-idx-1].get('sources'))
                
                if not st.session_state.history[history_len-idx-1].get('additional_info_needed'):
                    display_feedback_form(history_len-idx-1, message)

                logger.debug("classificaiton of the resposne %s",st.session_state.history[history_len-idx-1].get('classification') )


# def generate_pdf():
#     buffer = BytesIO()
#     c = canvas.Canvas(buffer, pagesize=letter)
#     width, height = letter

#     c.setFont("Helvetica", 12)
#     y = height - 60  # Add header space
#     line_height = 14

#     # Add header
#     c.drawString(40, height - 40, "")
#     c.drawString(40, height - 55, "")

#     for idx, message in enumerate(st.session_state.history):
#         if message.get("is_user"):
#             #text = f"You: {message.get('message')}"
#             text = ""
#             print("skipping")
#         else:
#             text = f"{message.get('message')}"
#         y = wrap_text(text, width - 80, c, 40, y, line_height)
#         y -= line_height  # Add line break between messages
#         if y < 40:
#             c.showPage()
#             c.setFont("Helvetica", 12)
#             y = height - 60  # Reset y position with header space

#     c.save()
#     buffer.seek(0)
#     return buffer
# def wrap_text(text, width, canvas, x, y, line_height):
#     lines = utils.simpleSplit(text, canvas._fontname, canvas._fontsize, width)
#     for line in lines:
#         canvas.drawString(x, y, line)
#         y -= line_height
#     return y
# def wrap_text(text, width, canvas, x, y, line_height):
#     lines = utils.simpleSplit(text, canvas._fontname, canvas._fontsize, width)
#     for line in lines:
#         if y < line_height:
#             canvas.showPage()
#             canvas.setFont("Helvetica", 12)
#             y = letter[1] - line_height
#         canvas.drawString(x, y, line)
#         y -= line_height
#     return y