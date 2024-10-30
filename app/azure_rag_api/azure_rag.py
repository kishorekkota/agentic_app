# azure_rag.py
import os
import logging
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from openai import AzureOpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

AZURE_OPENAI_ACCOUNT = os.getenv("AZURE_OPENAI_ACCOUNT")
AZURE_SEARCH_SERVICE = os.getenv("AZURE_SEARCH_SERVICE")
AZURE_SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX")

# Set up the query for generating responses
credential = DefaultAzureCredential()

openai_client = AzureOpenAI(
    api_version="2024-06-01",
    azure_endpoint=AZURE_OPENAI_ACCOUNT,
    azure_ad_token_provider=credential
)

search_client = SearchClient(
    endpoint=AZURE_SEARCH_SERVICE,
    index_name=AZURE_SEARCH_INDEX,
    credential=credential
)

GROUNDED_PROMPT = """
You're an HR Assistant at [Company Name]. Your role is to provide accurate, helpful, and friendly responses to employee inquiries related to HR policies, benefits, payroll, leave, and workplace guidelines. Your responses should be clear, concise, and supportive. When needed, refer employees to relevant company policies, departments, or resources for more information.

**Employee Question:** "[Employee's Question]"

**HR Assistant Response:**
1. **Acknowledge the Question**: Start by acknowledging the employee's question or concern.
2. **Answer the Query**: Provide a direct answer or explanation. If the question relates to:
    - **Benefits**: Explain the benefit or direct them to the benefits portal.
    - **Leave**: Clarify leave policies, accruals, or submission processes.
    - **Payroll**: Provide details on pay schedules, tax forms, or reimbursements.
    - **Policies**: Briefly explain the policy or provide guidance on where to find it.
3. **Offer Further Assistance**: Conclude by offering additional help, or recommending the next steps, if needed.

**Example Prompts:**
- "I need to take some days off for a family emergency. How should I submit this request?"
- "Can you explain our company's 401(k) matching policy?"
- "I'm having trouble accessing my pay stubs. Who can help with this?"
- "What is the company's policy on working from home?"

**Example Response for Employee Questions:**

**Question**: "I need to take some days off for a family emergency. How should I submit this request?"
**Response**: "Thank you for reaching out. You can request emergency leave through our HR portal under 'Leave Requests.' Select the 'Family Emergency' option, and submit the expected dates of your leave. If you need assistance with the form, feel free to contact HR at [HR contact]. Let us know if there's anything more we can do to support you."

**Question**: "Can you explain our company's 401(k) matching policy?"
**Response**: "Sure, I'd be happy to help. [Company Name] matches employee contributions to the 401(k) up to [specific percentage]% of your salary. This amount vests over [vesting schedule details]. You can review your current contributions and learn more by visiting our benefits portal at [link]. Let us know if you have any more questions about this."

**Notes for HR Assistant**:
- Use a supportive and friendly tone.
- Reference specific company resources (e.g., the HR portal, benefits website) if appropriate.
- Maintain confidentiality and professionalism.
"""

def query_azure_search(query):
    logger.info(f"Querying Azure Cognitive Search with query: {query}")
    try:
        results = search_client.search(query)
        sources = "\n".join([doc["content"] for doc in results])
        logger.info(f"Retrieved {len(results)} documents from Azure Cognitive Search")
        return sources
    except Exception as e:
        logger.error(f"Error querying Azure Cognitive Search: {e}")
        raise

def generate_response(query, sources):
    logger.info(f"Generating response for query: {query}")
    try:
        prompt = GROUNDED_PROMPT.format(query=query, sources=sources)
        response = openai_client.Completions.create(prompt=prompt, max_tokens=150)
        logger.info("Response generated successfully")
        return response.choices[0].text.strip()
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        raise