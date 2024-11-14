# Automate creating tedious jira tickets

![JIRABOT](assets/jirabot.jpeg)

Jirabot helps you scaffold out long lists of tickets with some AI magic to help you along...

## Setup
1. Install [ollama](https://ollama.com/)
2. Install the python dependencies with `pip install -r requirements.txt`
3. Define a Jira API key for your user [here](https://id.atlassian.com/manage-profile/security/api-tokens)
4. Install 1password cli (optional) `brew install 1password-cli`
5. Create a new login with username = *YOUR_EMAIL* & password = *JIRA_API_KEY*
6. Look up jira ids you need to define the jira project's config

   e.g. Find your jira project's id using:
    `curl -u saimon.moore@xing.com:{API_KEY} -X GET -H "Accept: application/json" "https://new-work.atlassian.net/rest/api/3/project"`
    
    e.g. Find your project's issue types using:
    `curl -u saimon.moore@xing.com:{API_KEY} -X GET -H "Accept: application/json" "https://new-work.atlassian.net/rest/api/3/issue/createmeta?projectKeys={PROJECT_KEY: e.g. XJM}"`

    e.g Find the investment profile custom field id using:
    `curl -u saimon.moore@xing.com:{API_KEY} -X GET -H "Accept: application/json" "https://new-work.atlassian.net/rest/api/3/field"`

    e.g. Find the investment profile custom field possible values using:
    `curl -u saimon.moore@xing.com:{API_KEY} -X GET -H "Accept: application/json" "https://new-work.atlassian.net/rest/api/3/field/customfield_10089/context"`
    (Apparently only jira admins can do this so talk to them or use the network panel when creating a task to look for a request like: `/rest/gira/1/?operation=JiraGlobalIssueCreateModalLoad`)

7. Define project config json files under the config/ folder using this json structure:

e.g. config/XJM.json // {PROJECT_KEY}.json
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

At this point, the initial setup is done for a particular project.

8. Now, just create a csv file under ./projects/{PROJECT_KEY}.csv with a description of all the tickets you want to create that looks like this:
```
issueType,title,parent,investmentProfile,duedate,labels
Task,Create reusable nextjs kafka module for BCL,XJM-2939,New or improved Functionality,,
Investigation,[Spike] Investigate how to create OpenSearch index,XJM-2939,New or improved Functionality,,
```
9. Run the script 🦙
   It will ask you for which project do you want to create issues and then read the issues specified in the corresponding CSV files.

__Note__: _The templates used to generate the description are hard coded. Feel free to fork and change them or enhance the code to read the templates from a project specific folder_.

Just keep editing the CSV file and rerunning the script...