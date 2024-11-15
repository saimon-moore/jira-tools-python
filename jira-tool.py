
import csv
import json
import os
import logging
import sys
import getpass
import subprocess

from enum import Enum
from dotenv import load_dotenv
from datetime import datetime
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict
from jira import JIRA, Issue

import ollama

load_dotenv()

# Uncomment to enable logging
# logging.basicConfig(level=logging.INFO)

# Constants
JIRA_SERVER_URL = "https://new-work.atlassian.net"
CONFIG_FOLDER = "config"
CUSTOMFIELD_INVESTMENT_PROFILE = "customfield_10089"
DEFAULT_OLLAMA_MODEL = "llama3.2"

# Enum for input methods
class InputMethod(Enum):
    """Input method enumeration for selecting how to input credentials."""
    ONEPASSWORD = "1"
    MANUAL = "2"

@dataclass
class IssueLink:
    """Data structure for issue link information."""
    link_type: str
    issue_key: str

# Data structure for Jira ticket information
@dataclass
class JiraTicket:
    issue_type: str
    title: str
    investment_profile: str
    due_date: Optional[str] = None
    labels: Optional[List[str]] = None
    parent: Optional[str] = None
    issue_link: Optional[IssueLink] = None

def get_jira_credentials() -> Tuple[Optional[str], Optional[str]]:
    """Get Jira credentials from the user or 1Password."""
    item_name = os.getenv("JIRA_OP_ITEM_NAME")
    if item_name:
        credentials = fetch_jira_credentials(item_name)
        if all(credentials):
            return credentials

    choice = input_with_clear("Choose input method:\n1. 1Password CLI\n2. Manual input\n")
    if choice == InputMethod.ONEPASSWORD.value:
        item_name = input_with_clear(
            "### Hint - you can store it in the environment variable \"JIRA_OP_ITEM_NAME\" for easier usage in the future ### \n"
            "Enter the 1Password item name: ")
        return fetch_jira_credentials(item_name) or (None, None)

    jira_email = input_with_clear("Enter your Jira email: ")
    jira_api_token = getpass.getpass("Enter your Jira API token: ")
    return jira_api_token, jira_email

# Load project configuration
def load_project_config(project_name: str) -> Dict:
    config_path = os.path.join(CONFIG_FOLDER, f"{project_name}.json")
    try:
        with open(config_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        logging.error(f"Project config file not found: {config_path}")
        sys.exit(1)

# Connect to Jira
def connect_to_jira(jira_email: str, jira_api_token: str) -> JIRA:
    return JIRA(server=JIRA_SERVER_URL, basic_auth=(jira_email, jira_api_token))

# Load tickets from CSV
def load_tickets_from_csv(csv_path: str) -> List[JiraTicket]:
    tickets = []
    with open(csv_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row.get('issueLink'):
                issue_link = parse_issue_link(row.get('issueLink', '').strip())
            else:
                issue_link = None

            tickets.append(JiraTicket(
                issue_type=row['issueType'].strip(),
                title=row['title'].strip(),
                investment_profile=row['investmentProfile'].strip(),
                due_date=row.get('duedate').strip(),
                labels=row.get('labels', '').strip().split(','),
                parent=row.get('parent').strip(),
                issue_link=issue_link
            ))
    return tickets

# Generate description using Ollama
def generate_description(issue_type: str, title: str) -> str:
    templates = {
        "Task": """
            h2. User Story
            AS A customer
            I WANT TO be able to
            SO THAT
            
            h2. Acceptance Criteria
            GIVEN I'm at
            WHEN I click on
            THEN I see a
            
            h2. Dependencies
            This changes affects this, this and this
            
            h2. Open questions
            Does a user need to log in to see the briefing?
            
            h2. Pending
            Share icon
            Google analytics tracking code
            
            h2. Translations
        """,
        "Investigation": """
            h2. Why?
            Why the investigation is needed.
            
            h2. What?
            What should be investigated providing as many details as possible.
            
            h2. Outcome
            A list of tasks that when completed, would implement
        """,
        "Technical Debt": """
            h2. Why?
            Why is this technical debt task necessary? What do we stand to gain from the investment in effort?
            
            h2. What?
            What exactly are we trying to avoid or improve? 
            
            h2. Technical Details
            What needs to be done, described with as much technical details as possible.
        """,
        "User Story": """
            h2. Summary
            Brief summary based on title
            
            h2. Context
            Extra context to understand the requirements...
            
            AS A customer
            I WANT TO be able to
            SO THAT
            
            h2. Acceptance criteria
            GIVEN I'm a ....
            WHEN I ...
            THEN I ...
            
            h2. Other information
            Any other information (to be added once the issue is created)
        """,
        "Epic": """
            h2. Why?
            Brief summary based on title
            
            h2. What?
            Why should this epic be done.
            
            h2. Other information
            Any other information (to be added once the issue is created)
        """,
        "Bug": """
            h2. What?
            What is the bug?
            
            h2. Affected?
            Who or what is affected?
            
            h2. Steps to reproduce
            1. Do this
            2. Do that
            3. Boom
            
            h2. Extra information
            Any other info
        """
    }

    template = templates.get(issue_type, "")

    if not template:
        raise ValueError(f"Invalid issue type: {issue_type}")

    # Analysis prompt for evaluating comments
    analysis_prompt = (
        f"""Given the following jira issue structure for a '{issue_type}':
        ```
        {template}
        ``` and the following title: `{title}` then output the exact same text but prefill the h2. sections accordingly given the title.
        """
    )

    try:
        response = ollama.chat(model=get_ollama_model(), messages=[{"role": "user", "content": analysis_prompt}])
        description = response["message"]["content"].strip()

        return description

    except Exception as e:
        logging.error(f"Error analyzing comments: {e}")
        return "Error during analysis.", False


def parse_issue_link(link_str: str) -> Optional[IssueLink]:
    """Parse issue link string in the format 'link_type:issue_key'."""
    if not link_str:
        return None
    
    try:
        link_type, issue_key = link_str.strip().split(':')
        return IssueLink(link_type=link_type, issue_key=issue_key)
    except ValueError:
        logging.warning(f"Invalid issue link format: {link_str}")
        return None

def create_issue_link(jira: JIRA, source_issue: Issue, link: IssueLink) -> None:
    """Create a link between two issues."""
    try:
        jira.create_issue_link(
            type=link.link_type,
            inwardIssue=source_issue.key,
            outwardIssue=link.issue_key
        )
        print(f"Created '{link.link_type}' link to {link.issue_key}")
    except Exception as e:
        logging.error(f"Error creating issue link: {e}")

# Create Jira ticket
def create_jira_ticket(jira: JIRA, project_config: Dict, ticket: JiraTicket) -> Issue:
    issue_type_id = project_config['issueTypes'].get(ticket.issue_type)
    investment_profile_id = next(
        (profile['id'] for profile in project_config['investmentProfiles'] if profile['value'] == ticket.investment_profile),
        None
    )
    if not issue_type_id or not investment_profile_id:
        logging.error(f"Invalid issue type or investment profile for ticket: {ticket.title}")
        return None

    description = generate_description(ticket.issue_type, ticket.title)

    fields = {
        "project": {"id": project_config["projectId"]},
        "summary": ticket.title,
        "issuetype": {"id": issue_type_id},
        "description": description,
        CUSTOMFIELD_INVESTMENT_PROFILE: {"id": investment_profile_id}
    }
    
    if ticket.due_date:
        try:
            due_date_formatted = datetime.strptime(ticket.due_date, "%Y-%m-%d").strftime("%Y-%m-%d")
            fields["duedate"] = due_date_formatted
        except ValueError:
            logging.error(f"Invalid date format for ticket: {ticket.title}")
    
    if ticket.labels:
        fields["labels"] = ticket.labels

    if ticket.parent:
        fields["parent"] = {"key": ticket.parent}

    try:
        created_issue = jira.create_issue(fields=fields)

        logging.info(f"Created ticket: {ticket.title} - {created_issue.key} (link: {ticket.issue_link})")
        # Create issue link if specified
        if ticket.issue_link:
            try:
              create_issue_link(jira, created_issue, ticket.issue_link)
            except Exception as e:
                logging.error(f"Error creating link to ticket {ticket.title} - {ticket.issue_link}: {e}")
        
        return created_issue

    except Exception as e:
        logging.error(f"Error creating ticket {ticket.title}: {e}")
        return None

## Utility Functions
def clear_terminal() -> None:
    """Clear the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")

def input_with_clear(prompt: str) -> str:
    """Prompt for input and clear the terminal afterwards."""
    user_input = input(prompt)
    clear_terminal()
    return user_input

def fetch_jira_credentials(item_name: str) -> Tuple[Optional[str], Optional[str]]:
    """Fetch Jira credentials from 1Password using the given item name."""
    try:
        result = subprocess.run(
            ["op", "item", "get", item_name, "--format", "json"],
            capture_output=True, text=True, check=True
        )
        item = json.loads(result.stdout)
        return item["fields"][1]["value"], item["fields"][0]["value"]
    except subprocess.CalledProcessError as e:
        logging.error(f"Error fetching credentials: {e}")
        return None, None

def check_for_running_ollama() -> None:
    """Check if the Ollama service is running."""
    try:
        ollama.list()  
    except Exception as e:
        print(f"Ollama is not working: {e}")
        sys.exit(1)

def get_ollama_model() -> str:
    model_name = os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)
    try:
      ollama.show(model_name)
      return model_name
    except ollama.ResponseError as e:
      if e.status_code == 404:
         print(f"Pulling Ollama model: {model_name}")
         ollama.pull(model_name)
         return model_name
      else:
        print(f"Error using Ollama model: {e}")
        sys.exit(1)

# Main function
def main():
    check_for_running_ollama()

    jira_api_token, jira_email = get_jira_credentials()
    jira = connect_to_jira(jira_email, jira_api_token)

    project_name = input("Enter the project: ")
    csv_path = f"./projects/{project_name}.csv"
    project_config = load_project_config(project_name)

    tickets = load_tickets_from_csv(csv_path)
    logging.info(f"Loaded {len(tickets)} tickets from CSV")
    for ticket in tickets:
        created_ticket = create_jira_ticket(jira, project_config, ticket)
        if created_ticket:
            print(f"Created ticket: {created_ticket.key} - {ticket.title}")

if __name__ == "__main__":
    main()
