import pandas as pd
import re
import vertexai
from vertexai import rag
from vertexai.language_models import TextEmbeddingModel, TextEmbeddingInput
from vertexai.generative_models import GenerativeModel

# Initialize Vertex AI
PROJECT_ID = "ai-experimentation-428115"
REGION = "us-central1"
vertexai.init(project=PROJECT_ID, location=REGION)

# Constants
CODES_PATTERN = r"\b[A-Z]{3,6}\b"
SHORTCODES_CSV = "banking_call_center_shortcodes.csv"
MEMOS_CSV = "large_call_center_memos.csv"

# Function to provide account activity
def provide_account_activity(csv_path: str, account_id: str = None):
    """Fetch account activity from the CSV file."""
    df = pd.read_csv(csv_path)
    return df[df['account_id'] == account_id] if account_id else df

# Function to embed text using Vertex AI
def embed_text(csv_path, model_name="text-embedding-005"):
    """Generate text embeddings for a list of texts using a specified model."""
    df = pd.read_csv(csv_path)
    model = TextEmbeddingModel.from_pretrained(model_name)
    inputs = [
        TextEmbeddingInput(
            text=f"{row.get('Shortcode', '')} {row.get('FullForm', '')} {row.get('Description', '')}"
        ) for _, row in df.iterrows()
    ]
    embeddings = model.get_embeddings(inputs)
    df["embeddings"] = [embedding.values for embedding in embeddings]
    return df

# Function to look up shortcode descriptions
def get_shortcode_description(memo_text: str):
    """Look up the description of shortcodes from the CSV file."""
    hits = set(re.findall(CODES_PATTERN, memo_text))
    df = pd.read_csv(SHORTCODES_CSV)
    defs = {}
    for code in hits:
        result = df[df['Shortcode'] == code]
        defs[code] = result.iloc[0]['Description'] if not result.empty else "No description found"
    return defs

# Function to summarize a call
def summarize_call(memo_text: str):
    """Generate a plain-English summary of a call using glossary definitions."""
    defs = get_shortcode_description(memo_text)
    glossary_block = "\n".join(f"{k} = {v}" for k, v in defs.items())
    prompt = f"""
### Glossary
{glossary_block}

### Memo
{memo_text}

### Task
Write a plain-English call summary for the account representative.
- Use the glossary meanings where applicable.
- Avoid jargon and technical terms.
- Keep the summary concise and under 120 words.
- Format the summary as bullet points for clarity.
- Remove abbreviations and shortcodes from the summary.
- Include information that is missing abbreviations.
- Predict customer call intent based on the memo.
- Only respond with the summary and return in 3-5 bullet points.
- Respond with "Call Summary:" and then the summary based on recent information with respective dates with call intent.
"""
    summarizer = GenerativeModel(model_name="gemini-2.0-flash-001")
    return summarizer.generate_content(prompt).text

# Main execution
if __name__ == "__main__":
    # Example: Provide account activity
    account_activity = provide_account_activity(MEMOS_CSV, account_id="e3dce91d-ea4f-4d97-9514-bdeb43dacd04")
    print(account_activity)

    # Example: Embed text
    embedded_df = embed_text(SHORTCODES_CSV)
    print(embedded_df.head())

    # Example: Summarize a call
    memo_text = pd.concat([account_activity['Date'], account_activity['Memo']], axis=1).to_string(index=False)
    summary = summarize_call(memo_text)
    print("Call Summary:")
    print(summary)