# filepath: /Users/kishorekota/git/agentic_app/rag_vertex_ai/pdf_to_json_converter.py
import PyPDF2
import textwrap
import json
import os

def pdf_to_json(pdf_path: str, json_path: str, chunk_size: int = 1000, chunk_overlap: int = 200):
    """
    Extracts text from a PDF, splits it into chunks, and writes the result to a JSON file.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    # Read PDF text
    pdf_text = ""
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page_num, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text() or ""
            pdf_text += f"\n[Page {page_num}]\n" + page_text

    # Split into overlapping chunks
    words = pdf_text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk_tokens = words[start:end]
        chunk_text = " ".join(chunk_tokens)
        chunks.append(chunk_text)
        start += (chunk_size - chunk_overlap)

    # Prepare JSON structure
    data = []
    for i, chunk in enumerate(chunks):
        # Extra: wrap for consistent line widths
        wrapped = textwrap.wrap(chunk, width=80)
        data.append({
            "id": f"chunk_{i}",
            "text": "\n".join(wrapped),
            "metadata": {
                "source_pdf": os.path.basename(pdf_path),
                "chunk_index": i
            }
        })

    # Write to JSON
    with open(json_path, "w", encoding="utf-8") as out_file:
        json.dump(data, out_file, indent=2, ensure_ascii=False)

    print(f"JSON output created: {json_path}")


if __name__ == "__main__":
    # Example usage:
    pdf_file = "Fraud_Dispute_Handling_Procedure.pdf"
    json_file = "Fraud_Dispute_Handling_Procedure.json"
    pdf_to_json(pdf_file, json_file)

    pdf_file = "Domestic_Wire_Transfer_Procedure.pdf"
    json_file = "Domestic_Wire_Transfer_Procedure.json"
    pdf_to_json(pdf_file, json_file)

    pdf_file = "Loan_Application_and_Approval_Process.pdf"
    json_file = "Loan_Application_and_Approval_Process.json"
    pdf_to_json(pdf_file, json_file)

    pdf_file = "New_Checking_Account_Opening_Procedure.pdf"
    json_file = "New_Checking_Account_Opening_Procedure.json"
    pdf_to_json(pdf_file, json_file)