#!/usr/bin/env python3
import time
import random
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- Configuration ---
# WARNING: Do not hardcode credentials in a real application.
# Use environment variables or a secure vault.
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.example.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "your_email@example.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "your_password")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "Your Name <your_email@example.com>")
SENDER_NAME = "Your Name" # Can be customized

class B2BSalesAgent:
    """
    A B2B Sales Agent to identify target accounts and run email outreach.
    """

    def __init__(self, simulate_only=True):
        """
        Initializes the agent.
        :param simulate_only: If True, prints emails instead of sending them.
        """
        self.simulate_only = simulate_only
        if not simulate_only:
            self._validate_smtp_config()

    def _validate_smtp_config(self):
        """Checks if SMTP configuration looks plausible for real sending."""
        if SMTP_SERVER == "smtp.example.com" or SMTP_USERNAME == "your_email@example.com":
            raise ValueError(
                "SMTP settings are set to default values. "
                "Please configure SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, "
                "SMTP_PASSWORD, and SENDER_EMAIL environment variables to send real emails."
            )

    def identify_target_accounts(self, source="mock"):
        """
        Identifies potential enterprise accounts from a given source.
        In a real-world scenario, this would connect to a CRM, a database,
        or a prospecting tool API (e.g., Clearbit, ZoomInfo, LinkedIn Sales Navigator).
        """
        print(f"[*] Identifying target accounts from source: {source}...")
        # Mock data for demonstration purposes
        mock_accounts = [
            {"company": "Innovate Corp", "contact_name": "Dr. Eleanor Vance", "email": "eleanor.v@examplecorp.com", "title": "CTO", "industry": "AI Research"},
            {"company": "Global Solutions Ltd.", "contact_name": "Marcus Holloway", "email": "m.holloway@globalsolutions.io", "title": "VP of Operations", "industry": "Logistics"},
            {"company": "Quantum Dynamics", "contact_name": "Anya Sharma", "email": "anya.s@quantumdynamics.net", "title": "Head of R&D", "industry": "Biotechnology"},
            {"company": "NextGen Retail", "contact_name": "Ben Carter", "email": "b.carter@nextgenretail.com", "title": "Director of E-commerce", "industry": "Retail Tech"},
            {"company": "Starlight Financial", "contact_name": "Sofia Rossi", "email": "s.rossi@starlightfinancial.com", "title": "Chief Financial Officer", "industry": "FinTech"},
        ]
        time.sleep(1) # Simulate API call delay
        print(f"[+] Found {len(mock_accounts)} potential target accounts.")
        return mock_accounts

    def get_email_templates(self):
        """
        Returns a list of email templates for the outreach sequence.
        """
        templates = {
            "initial_outreach": {
                "subject": "Quick Question about {company}",
                "body": """Hi {contact_name},

My name is {sender_name}, and I came across your profile while researching leaders in the {industry} space.

I was impressed with {company}'s work and wanted to briefly introduce our solution that helps companies like yours streamline their operations.

Would you be open to a brief 15-minute call next week to explore if this could be valuable for your team?

Best regards,
{sender_name}
"""
            },
            "follow_up_1": {
                "subject": "Re: Quick Question about {company}",
                "body": """Hi {contact_name},

Just wanted to gently follow up on my previous email.

We're helping other leaders in the {industry} sector achieve significant improvements, and I'm confident we could do the same for {company}.

Let me know if you have a moment to connect this week.

Best,
{sender_name}
"""
            }
        }
        return templates

    def run_outreach_sequence(self, accounts, sequence_steps=["initial_outreach", "follow_up_1"]):
        """
        Executes an email outreach sequence for the given accounts.
        """
        print("\n[*] Starting automated email outreach sequence...")
        templates = self.get_email_templates()
        
        for account in accounts:
            print(f"\n--- Processing: {account['company']} ---")
            for i, step in enumerate(sequence_steps):
                if step not in templates:
                    print(f"[!] Warning: Template for step '{step}' not found. Skipping.")
                    continue

                template = templates[step]
                subject = template["subject"].format(**account)
                body = template["body"].format(sender_name=SENDER_NAME, **account)

                print(f"[*] Preparing email for step '{step}' to {account['email']}...")
                self.send_email(account['email'], subject, body)

                # Simulate delay between emails to one prospect
                if i < len(sequence_steps) - 1:
                    delay = random.uniform(3, 5) # In a real sequence, this would be days
                    print(f"[*] (Simulating delay before next follow-up: {delay:.1f} seconds)")
                    time.sleep(delay)
            
            # Simulate delay between different prospects
            prospect_delay = random.uniform(5, 10)
            print(f"[*] Waiting {prospect_delay:.1f} seconds before contacting next prospect...")
            time.sleep(prospect_delay)
        
        print("\n[+] Outreach sequence completed.")

    def send_email(self, recipient_email, subject, body):
        """
        Sends an email. If in simulation mode, it prints to console.
        """
        if self.simulate_only:
            print("-" * 50)
            print(f"TO: {recipient_email}")
            print(f"FROM: {SENDER_EMAIL}")
            print(f"SUBJECT: {subject}")
            print("-" * 50)
            print(body)
            print("-" * 50)
            return

        # --- Real Email Sending Logic ---
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        try:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(msg)
                print(f"[+] Successfully sent email to {recipient_email}")
        except Exception as e:
            print(f"[!] Failed to send email to {recipient_email}: {e}")

def main():
    """Main function to run the B2B Sales Agent."""
    print("--- MISO B2B Sales Agent V19 ---")
    
    # Set to False to send real emails (requires environment variable setup)
    # Be very careful with this setting.
    SIMULATE = True 
    
    agent = B2BSalesAgent(simulate_only=SIMULATE)
    
    # 1. Identify potential customers
    target_accounts = agent.identify_target_accounts()

    if not target_accounts:
        print("[!] No target accounts found. Exiting.")
        return

    # 2. Initiate the outreach sequence
    agent.run_outreach_sequence(target_accounts)

if __name__ == "__main__":
    main()
