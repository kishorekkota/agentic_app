# If you don't have fpdf installed, uncomment and run the following:
# !pip install fpdf

from fpdf import FPDF
import textwrap

# Define a function to create a PDF from a title and text content
def create_pdf(pdf_filename, title, content):
    pdf = FPDF()
    pdf.add_page()
    
    # Set some basic font properties
    pdf.set_font("Arial", size=16, style="B")
    pdf.multi_cell(0, 10, title, align='C')
    pdf.ln(10)
    
    # Switch to a smaller font for the content
    pdf.set_font("Arial", size=12)
    
    # Wrap each paragraph in the content so it fits in the PDF
    wrapped_text = textwrap.wrap(content, width=80)
    for line in wrapped_text:
        safe_line = line.encode("latin-1", errors="replace").decode("latin-1")

        pdf.multi_cell(0, 6, safe_line)
        pdf.ln(1)
    
    pdf.output(pdf_filename)
    print(f"PDF created: {pdf_filename}")

# 1. Document: “New Checking Account Opening Procedure”
doc1_title = "New Checking Account Opening Procedure"
doc1_content = """Effective Date: Jan 1, 2025
Department: Retail Banking

Overview:
- This procedure details how to open a new personal checking account for a retail customer.

Procedure:
1. Customer Identification
   - Request valid government-issued ID (passport, driver’s license, or national ID).
   - Collect proof of address (utility bill, lease agreement, etc.).

2. Compliance Checks
   - Perform a Know Your Customer (KYC) screening.
   - Run Anti-Money Laundering (AML) checks using the bank’s internal system.

3. Application Form
   - Gather personal details (full name, date of birth, social security/national ID number).
   - Obtain signatures on the account application form and terms & conditions.

4. Account Setup
   - Enter customer information into the core banking system.
   - Assign account number and issue temporary debit card if applicable.

5. Confirmation & Welcome Kit
   - Provide account disclosure, fee schedule, and account usage details.
   - Hand over or mail the welcome kit with checkbook (if requested).

Additional Notes:
- Minimum initial deposit may apply depending on the account type.
- KYC records must be retained for at least five years.
"""

# 2. Document: “Domestic Wire Transfer Procedure”
doc2_title = "Domestic Wire Transfer Procedure"
doc2_content = """Effective Date: Jan 1, 2025
Department: Operations / Funds Transfer

Overview:
- This document describes how to initiate and process a domestic wire transfer request on behalf of a customer.

Procedure:
1. Verify Account Holder
   - Confirm the requesting customer’s identity (photo ID or phone authentication if remote).
   - Ensure the source account has sufficient funds.

2. Collect Transfer Details
   - Recipient bank’s name, routing number (ABA), and address.
   - Beneficiary name and account number.
   - Amount to be transferred and any reference details (e.g., invoice number).

3. Transaction Authorization
   - Obtain a signed or securely authenticated wire instruction from the account holder.
   - Follow dual-control policy: one staff member initiates, another approves.

4. Execute Transfer
   - Use the bank’s wire processing system to send the wire.
   - Confirm successful transmission via the internal messaging platform.

5. Notify Customer
   - Provide confirmation or reference number by email/SMS.
   - If the wire fails or is rejected, contact the customer immediately to resolve.

Additional Notes:
- Transfer cut-off time is 3:00 PM local time for same-day processing.
- Any amount exceeding $50,000 requires additional compliance approval.
"""

# 3. Document: “Loan Application & Approval Process”
doc3_title = "Loan Application & Approval Process"
doc3_content = """Effective Date: Jan 1, 2025
Department: Consumer Lending

Overview:
- This covers consumer loan applications (personal loans, auto loans).
- The policy outlines how agents should guide customers through the loan process.

Procedure:
1. Initial Inquiry
   - Gather basic customer info (employment status, monthly income, loan purpose).
   - Conduct a preliminary eligibility check based on credit score threshold.

2. Application Submission
   - Provide a formal loan application form.
   - Request supporting documents (income proof, ID, address proof).

3. Underwriting
   - Verify credit score using the credit bureau.
   - Assess debt-to-income ratio, job stability, and other risk factors.

4. Decision & Terms
   - If approved, prepare a loan offer with interest rate, tenure, and repayment terms.
   - If declined, notify the customer with a brief explanation and alternative suggestions.

5. Loan Disbursement
   - Have the customer sign the final agreement.
   - Disburse funds into the designated account or via check.

Additional Notes:
- Loan terms and maximum amounts vary based on credit grade.
- All rejections must be documented with reasons for compliance audits.
"""

# 4. Document: “Fraud Dispute Handling Procedure”
doc4_title = "Fraud Dispute Handling Procedure"
doc4_content = """Effective Date: Jan 1, 2025
Department: Customer Support / Fraud Department

Overview:
- This document details how to handle customer reports of unauthorized transactions or suspected fraud on their accounts.

Procedure:
1. Intake & Verification
   - Collect dispute details (date/time, transaction type, amount).
   - Confirm the caller’s identity using security questions.

2. Account Freeze & Investigation
   - If fraud is ongoing, temporarily freeze the account to block further unauthorized activity.
   - Create a fraud case in the CRM system and assign a unique reference number.

3. Evidence Collection
   - Instruct the customer to provide any supporting documentation (receipts, emails, etc.).
   - Gather internal transaction logs for further review.

4. Fraud Analysis
   - Collaborate with the Fraud Department to evaluate patterns (IP addresses, merchant codes).
   - Determine if the dispute is legitimate or if additional info is needed.

5. Provisional Credit & Resolution
   - If the fraud claim is validated, issue a provisional credit within the regulated timeframe.
   - Notify the customer of the final resolution and provide any necessary next steps (e.g., new debit card issuance).

Additional Notes:
- Always follow Reg E or relevant local regulations regarding timelines for provisional credits.
- Record all customer interactions in the fraud investigation log.
"""

# Create each PDF
create_pdf("New_Checking_Account_Opening_Procedure.pdf", doc1_title, doc1_content)
create_pdf("Domestic_Wire_Transfer_Procedure.pdf", doc2_title, doc2_content)
create_pdf("Loan_Application_and_Approval_Process.pdf", doc3_title, doc3_content)
create_pdf("Fraud_Dispute_Handling_Procedure.pdf", doc4_title, doc4_content)
