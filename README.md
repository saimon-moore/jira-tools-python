# Automate chewing through tedious jira tickets and comments

![llama eating sticky notes](assets/jirabot.jpeg)

## Setup
1. Install [ollama](https://ollama.com/)
2. Install the python dependencies with `pip install -r requirements.txt`
3. Define a Jira API key for your user [here](https://id.atlassian.com/manage-profile/security/api-tokens)
3.1 Install 1password cli (optional) `brew install 1password-cli`
3.2 Create a new login with username = *YOUR_EMAIL* & password = *JIRA_API_KEY*
3.3 Find your jira project's id using:
    `curl -u saimon.moore@xing.com:{API_KEY} -X GET -H "Accept: application/json" "https://new-work.atlassian.net/rest/api/3/project"`
3.3 Find your project's issue types using:
    `curl -u saimon.moore@xing.com:{API_KEY} -X GET -H "Accept: application/json" "https://new-work.atlassian.net/rest/api/3/issue/createmeta?projectKeys={PROJECT_KEY: e.g. XJM}"`
3.3 Find the investment profile custom field id using:
    `curl -u saimon.moore@xing.com:{API_KEY} -X GET -H "Accept: application/json" "https://new-work.atlassian.net/rest/api/3/field"`
3.3 Find the investment profile custom field possible values using:
    `curl -u saimon.moore@xing.com:{API_KEY} -X GET -H "Accept: application/json" "https://new-work.atlassian.net/rest/api/3/field/customfield_10089/context"`
    (Apparently only jira admins can do this so talk to them or use the network panel when creating a task to look for a request like: `/rest/gira/1/?operation=JiraGlobalIssueCreateModalLoad`)
3.3 Define project config json files under the projects/ folder using this json structure:

e.g. projects/XJM.json // {PROJECT_KEY}.json
```
{
    "projectKey": "XJM",
    "projectId": 10154,
    "issueTypes": [
        "Bug": 10014,
        "Epic": 10000,
        "Investigation": 10019,
        "Task": 10015,
        "Technical Debt": 10040,
        "Training": 10038,
        "User Story": 10004
    ],
    "investmentProfiles": [
        "NONE": "",
        "NEW_OR_IMPROVED_FUNCTIONALITY": "New or improved Functionality",
        "NEW_OR_ADDITIONAL_REVENUE": "New or additional Revenue",
        "TECH_DEBT": "Tech Debt",
        "OPERATIONS_AND_SUSTAINABILITY": "Operations & Sustainability",
        "EXTERNAL_REQUEST_OR_CITIZENSHIP": "External Request / Citizenship",
        "BUG_OR_DEFECT": "Bug or Defect",
        "OTHER": "Other",
    ],
},
```
4. Run the script 🦙