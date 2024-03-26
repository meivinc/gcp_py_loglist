# GCP Logs Inventory Script

This Python script allows you to retrieve logs from Google Cloud Platform for various hierarchy levels over a specified period. The script generates a CSV file with information about ServiceName, associated methods, severity and types of logs (e.g., data access, activity).

I created this script to retrieve easily information about which kind of logs exists on my GCP organization. In that way, it's more easy for me to determine on which kind of logs i have to create log-based metrics. 

To parse the data, you can use several tools. In my case i'm using Looker Studio. 
## Introduction

When working with the `google.cloud.logging` API, the `list_entries()` method returns a generator object, making it challenging to determine the number of queries made to the Cloud Logging service. This became a concern due to the Cloud Logging Quota, which limits the usage to 40 read requests per minute.

To address this limitation, the `get_logging_entries` function includes a mechanism to count the number of iterations. After approximately 1800 iterations, the script estimates it's close to the quota limit and introduces a 60-second sleep to adhere to the quota restrictions. This ensures smooth execution without hitting quota limits and provides better control over the script's interaction with the Cloud Logging service.

## Documentation Links

- [google.cloud.resourcemanager_v3](https://googleapis.dev/python/cloudresourcemanager/latest/index.html): Python client library for Google Cloud Resource Manager API.
  - **Methods:**
    - [`ProjectsClient`](https://cloud.google.com/python/docs/reference/cloudresourcemanager/latest/google.cloud.resourcemanager_v3.services.projects.ProjectsClient)
    - [`FoldersClient`](https://cloud.google.com/python/docs/reference/cloudresourcemanager/latest/google.cloud.resourcemanager_v3.services.folders.FoldersClient)
    - [`search_folders()`](https://cloud.google.com/python/docs/reference/cloudresourcemanager/latest/google.cloud.resourcemanager_v3.services.folders.FoldersClient#google_cloud_resourcemanager_v3_services_folders_FoldersClient_search_folders)
    - [`OrganizationsClient`](https://cloud.google.com/python/docs/reference/cloudresourcemanager/latest/google.cloud.resourcemanager_v3.services.organizations.OrganizationsClient)
    - [`search_organizations()`](https://cloud.google.com/python/docs/reference/cloudresourcemanager/latest/google.cloud.resourcemanager_v3.services.organizations.OrganizationsClient#google_cloud_resourcemanager_v3_services_organizations_OrganizationsClient_search_organizations)

- [google.cloud.logging](https://googleapis.dev/python/logging/latest/index.html): Python client library for Google Cloud Logging API.
  - **Methods:**
    - [`list_entries()`](https://cloud.google.com/python/docs/reference/logging/latest/client)

## Usage

### Prerequisites

- Python 3.9.6 minimum
- Google Cloud SDK installed and authenticated

### Installation

Clone the repository and install the required dependencies:

```bash
git clone https://github.com/meivinc/gcp_py_loglist.git
cd gcp_py_loglist

# Set python Environment if desired :
python -m venv pylog
source pylog/bin/activate

# Install the modules
pip install -r requirements.txt
```

### Configuration

Modify the script's parameters in `main.py` on your convenience :

```python
# main.py

DebugMode = False  # Set to True for debugging
days = 7  # Number of days for log retrieval
csv_filename = "logs_inventory.csv"  # Name of the CSV file to be generated
severity = None # Specify your severity level if needed 
```


| Enum        | Severity Level | Description                                            |
|-------------|-----------------|--------------------------------------------------------|
| DEFAULT     | 0               | The log entry has no assigned severity level.          |
| DEBUG       | 100             | Debug or trace information.                            |
| INFO        | 200             | Routine information, such as ongoing status or performance. |
| NOTICE      | 300             | Normal but significant events, such as start up, shut down, or a configuration change. |
| WARNING     | 400             | Warning events might cause problems.                   |
| ERROR       | 500             | Error events are likely to cause problems.             |
| CRITICAL    | 600             | Critical events cause more severe problems or outages. |
| ALERT       | 700             | A person must take action immediately.                 |
| EMERGENCY   | 800             | One or more systems are unusable.                      |


### Functions

1. **get_logging_entries**: Retrieves logging entries from Google Cloud Platform based on the resource hierarchy retrieved from function 3.

2. **export_to_csv**: Exports the retrieved data to a CSV file.

3. **list_google_cloud_resources**: Lists Google Cloud resources (Projects, Folders and Organizations).

4. **scriptcalculation**: Calculate Script duration.

5. **logging_loop**: Implements the logging loop for iterating through logs.

6. **debug_cloudresource**: Provides debugging information for Google Cloud resources if parameters DebugMode is set to True .


### How to Run

Execute the script using the following command:

```bash
python main.py
```


## Contributing

Feel free to contribute by opening issues or submitting pull requests.
