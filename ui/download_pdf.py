from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from reportlab.lib import utils

def generate_pdf(chat_history):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica", 12)
    y = height - 60  # Add header space
    line_height = 14

    # Add header
    c.drawString(40, height - 40, "Job Description")
    c.drawString(40, height - 55, "----------------")

    text = f"{chat_history.get('message')}"
    y = wrap_text(text, width - 80, c, 40, y, line_height)
    y -= line_height  # Add line break between messages
    if y < 40:
        c.showPage()
        c.setFont("Helvetica", 12)
        y = height - 60  # Reset y position with header space

    c.save()
    buffer.seek(0)
    return buffer

def wrap_text(text, width, canvas, x, y, line_height):
    lines = utils.simpleSplit(text, canvas._fontname, canvas._fontsize, width)
    for line in lines:
        if y < line_height:
            canvas.showPage()
            canvas.setFont("Helvetica", 12)
            y = letter[1] - line_height
        canvas.drawString(x, y, line)
        y -= line_height
    return y