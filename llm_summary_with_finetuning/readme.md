# LLM Summary with Fine-Tuning

This module is designed to generate plain-English summaries of customer interactions in a banking call center. It leverages a glossary of shortcodes and descriptions to interpret and summarize call memos effectively using Vertex AI and fine-tuned LLMs.

## Features

- **Shortcode Glossary**: A comprehensive list of banking-related shortcodes and their meanings, used to decode call memos.
- **Call Summarization**: Generates concise summaries of customer interactions using fine-tuned LLMs.
- **Text Embedding**: Embeds glossary data for efficient retrieval and contextual understanding.
- **Account Activity Retrieval**: Fetches account-specific activity from large datasets for analysis.

## Files

### 1. `llm_with_summary.py`
This script contains the core logic for summarizing call memos. It uses Vertex AI for embedding and generative tasks.

**Key Functions**:
- `provide_account_activity(csv_path: str, account_id: str = None)`: Fetches account activity from a CSV file.
- `embed_text(csv_path: str, model_name: str)`: Generates text embeddings for glossary data.
- `get_shortcode_description(memo_text: str)`: Looks up shortcode descriptions from the glossary.
- `summarize_call(memo_text: str)`: Generates a plain-English summary of a call using glossary definitions.

### 2. `LLM_with_finetuning.ipynb`
A Jupyter notebook demonstrating the use of Vertex AI for embedding and summarization tasks. It includes:
- Examples of embedding glossary data.
- Retrieval of account activity.
- Summarization of call memos.

### 3. `banking_call_center_shortcodes.csv`
A CSV file containing the glossary of shortcodes, their full forms, and descriptions.

**Columns**:
- `Shortcode`: The abbreviation used in call memos.
- `FullForm`: The expanded form of the shortcode.
- `Description`: A detailed explanation of the shortcode's meaning.

### 4. `large_call_center_memos.csv`
A dataset containing call memos with details such as account ID, date, shortcode, memo text, and more.

**Columns**:
- `Memo ID`, `account_id`, `Date`, `Shortcode`, `Memo`, `Rep ID`, `Sentiment`, `Channel`, `Intent`.

## Usage

1. **Prepare the Environment**:
   - Install required dependencies:
     ```bash
     pip install pandas google-cloud-aiplatform
     ```

2. **Authenticate with Google Cloud**:
   - Run the following command to authenticate:
     ```bash
     gcloud auth application-default login
     ```

3. **Run the Script**:
   - Execute `llm_with_summary.py` to generate summaries:
     ```bash
     python llm_with_summary.py
     ```

4. **Example Output**:
   - For a given memo text, the script generates a summary like:
     ```
     Call Summary:
     - Customer requested a new personal savings account on 2025-03-08.
     - Positive sentiment recorded during the interaction.
     ```

## Dependencies

- `pandas`: For handling CSV data.
- `google-cloud-aiplatform`: For interacting with Vertex AI.
- `re`: For regex-based shortcode extraction.

## Future Enhancements

- Finetuning with RAG and retrieval tool
