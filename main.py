import csv 
import os
from google.cloud import logging
from datetime import datetime, timedelta
from alive_progress import alive_bar
from urllib.parse import unquote
from google.cloud import resourcemanager_v3
from google.cloud import storage
import time


def get_logging_entries(days,kind=None,type=None,apilog=None,severity_filter=None):
    client = logging.Client()
    #

    # Calculate the start and end timestamps for the last 'days' days
    end_timestamp = datetime.utcnow()
    start_timestamp = end_timestamp - timedelta(days=days)

    # Format timestamps for the filter string
    start_timestamp_str = start_timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')
    end_timestamp_str = end_timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')

    # Define a filter to narrow down the logs within the specified time range
    filter_str = f'timestamp >= "{start_timestamp_str}" AND timestamp <= "{end_timestamp_str}"'

    # Add severity filter if provided
    if severity_filter:
        filter_str += f' AND severity >= "{severity_filter}"'

    # Exclude logs with specific log name
        filter_str += ' AND NOT logName:"cloud.googleapis.com%2Fipsec_events"'

    if "project" in type.lower():
        resource="projects/" + str(kind)
    if "folder" in type.lower():
        resource="folders/" + str(kind)
    if "organizations" in type.lower():
        resource="organizations/" + str(kind)
    else: None

    entries = client.list_entries(
        #resource_names=["organizations/orgnizationID"],
        filter_=filter_str,
        resource_names=[resource]
        )
        
    # Fields to extract from each log entry
    fields_to_extract = ['insert_id','severity', 'timestamp', 'method','@type','service']
    #fields_to_extract = ['insert_id', 'severity', 'timestamp', 'method','@type','service']

    results = []
 
    for entry in entries:
        if apilog >= 1800: 
           apilog = 0
           print("taking a nap to avoid API issue..")
           time.sleep(60)
        log_data = {}
        for field in fields_to_extract:
            # Handle nested fields
            if '.' in field:
                nested_fields = field.split('.')
                value = getattr(entry, nested_fields[0], {})
                for nested_field in nested_fields[1:]:
                    value = getattr(value, nested_field, {})
                log_data[field] = value
            else:
                # Check if the attribute exists before attempting to access it
                log_data[field] = getattr(entry, field) if hasattr(entry, field) else None
        # Special handling for timestamp
        log_data['timestamp'] = str(log_data['timestamp'])

        # Extract method from payload if payload is not None
        try:
            log_data['service'] = entry.payload.get('serviceName') if entry.payload is not None else None
        except: 
            print ("error on id : " + entry.insert_id)
            log_data['service'] = entry.insert_id
        try: 
            log_data['method'] = entry.payload.get('methodName') if entry.payload is not None else None
        except: 
            print ("error on id : " + entry.insert_id)
            log_data['method'] = entry.insert_id
        # Add @type field
        try:
            log_data['@type'] = entry.payload.get('@type') if entry.payload is not None else None
        except: 
            print ("error on id : " + entry.insert_id)
            log_data['@type'] = "None"

        # Extract "Level" and "Kind" from LogName
        log_name_parts = entry.log_name.split('/')
        log_data['Level'] = log_name_parts[0] if len(log_name_parts) > 1 else None
        log_data['Kind'] = unquote(log_name_parts[-1].split('%2F')[-1]) if len(log_name_parts) > 1 else None

        results.append(log_data)
        apilog = apilog+1

    return results, apilog

def export_to_csv(data, csv_filename):
    if not data:
        print("No data to export.")
        return
    # Extract header fields from the first entry
    header_fields = list(data[0].keys())

    # Check if the file already exists
    file_exists = os.path.exists(csv_filename)

    with open(csv_filename, 'a', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=header_fields)

        # If the file doesn't exist, write the header
        if not file_exists:
            writer.writeheader()

        # Write the data
        writer.writerows(data)

    #print(f"CSV file '{csv_filename}' has been successfully created.")

def list_google_cloud_resources(debug=False):
    client = resourcemanager_v3.ProjectsClient()
    folder_client = resourcemanager_v3.FoldersClient()
    # Retrieve all projects
    projects = list(client.search_projects())
    project_ids = []
    project_display_names = []
    # Use a set to track unique folder IDs
    unique_folder_ids = set()
    # Declare folder_ids and folder_display_names here
    folder_ids = []
    folder_display_names = []
    # Retrieve associated folders for each project
    for project in projects:
        # Check if the project is not in a deleted or pending deletion state
        if project.state == resourcemanager_v3.Project.State.ACTIVE:
            project_ids.append(project.project_id)
            # Fetch additional project details including display_name
            project_details = client.get_project(name=f'projects/{project.project_id}')
            project_display_name = project_details.display_name
            project_display_names.append(project_display_name if debug else None)
    # Retrieve all folders
    folders = list(folder_client.search_folders())
    for folder in folders:
        if folder.state == resourcemanager_v3.Folder.State.ACTIVE: 
            folder_id = folder.name.split('/')[-1]
            # Check if folder ID is not already encountered
            if folder_id not in unique_folder_ids:   
                if debug:
                    folder_display_name = folder.display_name
                    folder_ids.append(folder_id)
                    folder_display_names.append(folder_display_name)
                else:
                    folder_ids.append(folder_id)
                # Add the folder ID to the set
                unique_folder_ids.add(folder_id)
    # Retrieve all organizations
    org_client = resourcemanager_v3.OrganizationsClient()
    organizations = list(org_client.search_organizations())
    organization_ids = [organization.name.split('/')[-1] for organization in organizations]
    organization_display_names = [organization.display_name for organization in organizations] if debug else []
    result = {
        'Projects': project_ids,
        'Folders': folder_ids,
        'Organizations': organization_ids
    }
    if debug:
        result2 = result
        result2.update({
            'ProjectDisplayNames': project_display_names,
            'FolderDisplayNames': folder_display_names,
            'OrganizationDisplayNames': organization_display_names
        })
        debug_cloudresource(result2)
    
    return result

def scriptcalculation(start,end):
    # Calculate the duration
    duration = start - end
    # Convert the total seconds to hours, minutes, and seconds
    hours, remainder = divmod(duration.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    # Print the formatted duration
    formatted_time = "{:02}:{:02}:{:02}".format(int(hours), int(minutes), int(seconds))
    return formatted_time

def logging_loop(object_type,object_kind,func_fulllog_count,func_aggregate_logs,severity):
    with alive_bar(total=(len(object_kind)), title=f'Progress : {object_type} Parsing logs') as bar:
        print(f'=========  {object_type} FETCHING LOGS =========')
        for item in  object_kind:
            # print(prj)
            logging_entries,func_aggregate_logs  = get_logging_entries(days,kind=item,type=object_type,apilog=func_aggregate_logs,severity_filter=severity)
            export_to_csv(logging_entries, csv_filename)
            #print(f'Data exported to {csv_filename}')
            print(f'{object_type} :{item}, Number of logs parsed: {len(logging_entries)}')
            print("aggregated logs : " + str(func_aggregate_logs) )
            func_fulllog_count += len(logging_entries)

            bar()   
        # export_to_csv(logging_entries, csv_filename)
   ####     # upload_to_cloud_storage(csv_filename,bucket_name)

    return func_fulllog_count,func_aggregate_logs

def debug_cloudresource(input):
        print("======= RESOURCE MANAGER DEBUG MOD =======")        
        print("Projects:")
        for project_id, project_display_name in zip(input['Projects'], input.get('ProjectDisplayNames', [])):
            print(f"  {project_id} - {project_display_name}")

        print("\nFolders:")
        for folder_id, folder_display_name in zip(input['Folders'], input.get('FolderDisplayNames', [])):
            print(f"  {folder_id} - {folder_display_name}")

        print("\nOrganizations:")
        for organization_id, org_display_name in zip(input['Organizations'], input.get('OrganizationDisplayNames', [])):
            print(f"  {organization_id} - {org_display_name}")

def upload_to_cloud_storage(csv_filename, bucket_name):
    # Initialize a Cloud Storage client
    storage_client = storage.Client()

    # Get the bucket
    bucket = storage_client.get_bucket(bucket_name)

    # Create a blob (object) in the bucket
    blob = bucket.blob(csv_filename)

    # Upload the CSV file to the Cloud Storage blob
    blob.upload_from_filename(csv_filename)

    print(f"File '{csv_filename}' uploaded to Cloud Storage bucket '{bucket_name}' with object name '{csv_filename}'.")


if __name__ == "__main__":
    # Paremeters to set
    DebugMod = False
    days = 7
    csv_filename = 'logs_export.csv'
    bucket_name = "bucket-python-export"
    start_time = datetime.utcnow()
    severity="WARNING"


    # Retrieve Google resources for parsing logs
    google_cloud_resources = list_google_cloud_resources(debug=DebugMod)
     
    # Logs to manage API Quota limits
    aggregate_logs = 0

    # Total for all script
    full_log_count = 0


    # # # Retrieve Project Structure log
    full_logentries, aggregate_logs = logging_loop("project",(google_cloud_resources['Projects']),full_log_count,aggregate_logs,severity)
    full_log_count += (full_logentries)

    # # # Retrieve Folder Structure log
    full_logentries, aggregate_logs = logging_loop("folder",(google_cloud_resources['Folders']),full_log_count,aggregate_logs,severity)
    full_log_count += (full_logentries)
 
    # Retrieve Organization Structure log
    full_logentries, aggregate_logs  = logging_loop("Organizations",(google_cloud_resources['Organizations']),full_log_count,aggregate_logs,severity)
    full_log_count += full_logentries


    end_time = datetime.utcnow()

    formatted_duration= scriptcalculation(start_time, end_time)
    print ("total Log Retrieved : " + str(full_log_count))
    print(f"Total duration elapsed: {formatted_duration}")