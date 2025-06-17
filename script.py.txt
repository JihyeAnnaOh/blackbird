import requests
import pandas as pd
from io import StringIO
import ast  # For safely evaluating string data
import numpy as np  # For handling missing values
import re  # For text pattern matching

# Patterns to validate email and phone formats
EMAIL_REGEX = r'^[\w\.-]+@[\w\.-]+\.\w{2,}$'
PHONE_REGEX = r'^\d{10,15}$'  # Phone numbers should be 10-15 digits after removing + and spaces

# Split a full name into first and last name
# For names with multiple words, use first word as first name and last word as last name
def parse_name(full_name):
    if pd.isna(full_name):
        return None, None
    parts = str(full_name).strip().split()
    if len(parts) == 1:
        return parts[0], None
    elif len(parts) >= 2:
        return parts[0], parts[-1]  # First word as first name, last word as last name
    return None, None

# Sort CRM data by date and last name
def sort_crm_by_date_name(input_file='crm_update.csv', output_file='crm_update_sorted_date_name.csv'):
    try:
        # Read the CSV file
        df = pd.read_csv(input_file)

        # Convert 'last contact date' to datetime objects for proper sorting
        df['last contact date'] = pd.to_datetime(df['last contact date'], errors='coerce')

        # Sort the DataFrame
        # Primary sort: last contact date (descending - newest first)
        # Secondary sort: last (ascending - alphabetized)
        sorted_df = df.sort_values(by=['last contact date', 'last'], ascending=[False, True])

        # Save the sorted data to a new CSV file
        sorted_df.to_csv(output_file, index=False)
        print(f"\nSorted CRM data saved to {output_file}")
        print("\n==== Sorted CRM Data (by Date & Last Name) ====")
        print(sorted_df.to_string())

    except FileNotFoundError:
        print(f"Error: The file {input_file} was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

# Your unique access token for the API
ACCESS_TOKEN = 'ce46319c012e01c63b13aed9cc67b72c'

# Base URL for the API endpoints
BASE_URL = 'https://it-hiring.blackbird.vc'

# Set up the authorization header for API requests
headers = {
    'Authorization': f'Bearer {ACCESS_TOKEN}'
}

# Get the latest CRM data from the API
crm_url = f'{BASE_URL}/api/data/crm'
crm_response = requests.get(crm_url, headers=headers)
crm_df = pd.read_csv(StringIO(crm_response.text))

# Get the event feedback form submissions from the API
form_url = f'{BASE_URL}/api/data/form-submissions'
form_response = requests.get(form_url, headers=headers)
form_data = form_response.json()
form_df = pd.DataFrame(form_data)

# Clean and organize the form submission data
form_df['parsed_data'] = form_df['data'].apply(lambda x: ast.literal_eval(x.strip('\"')) if isinstance(x, str) else x)
form_df['form_email'] = form_df['parsed_data'].apply(lambda x: x.get('email'))
form_df['form_phone'] = form_df['parsed_data'].apply(lambda x: str(x.get('phone')).replace('+', '').replace(' ', '') if x.get('phone') else None)
form_df['form_timestamp'] = form_df['parsed_data'].apply(lambda x: x.get('timestamp'))
form_df['form_message'] = form_df['parsed_data'].apply(lambda x: x.get('message'))
form_df[['form_first', 'form_last']] = form_df['parsed_data'].apply(lambda x: pd.Series(parse_name(x.get('name'))))

# Validate email and phone formats, mark invalid entries as missing
form_df['form_email'] = form_df['form_email'].apply(lambda x: x if pd.notna(x) and re.fullmatch(EMAIL_REGEX, str(x)) else None)
form_df['form_phone'] = form_df['form_phone'].apply(lambda x: x if pd.notna(x) and re.fullmatch(PHONE_REGEX, str(x)) else None)

# Convert dates to proper datetime format for comparison
crm_df['last contact date'] = pd.to_datetime(crm_df['last contact date'], errors='coerce')
form_df['form_timestamp'] = pd.to_datetime(form_df['form_timestamp'], errors='coerce')

# Start with existing CRM data and prepare for updates
merged_df = crm_df.copy()
new_contact_id_counter = crm_df['id'].apply(lambda x: int(x.split('-')[1]) if pd.notna(x) and '-' in x else 0).max() + 1

# Process each form submission
for index, form_row in form_df.iterrows():
    f_first = form_row['form_first']
    f_last = form_row['form_last']
    f_email = form_row['form_email']
    f_phone = form_row['form_phone']
    f_timestamp = form_row['form_timestamp']
    f_message = form_row['form_message']

    # Skip submissions missing essential information
    if pd.isna(f_timestamp) or pd.isna(f_message) or (pd.isna(f_email) and pd.isna(f_phone) and pd.isna(f_first)):
        continue

    matched_idx = -1
    potential_matches = pd.DataFrame()

    # Try to match the submission with existing CRM records
    # First try matching by email (most reliable)
    if pd.notna(f_email):
        potential_matches = merged_df[merged_df['email'].str.lower() == str(f_email).lower()]
        if not potential_matches.empty:
            matched_idx = potential_matches.index[0]

    # If no email match, try matching by phone number
    if matched_idx == -1 and pd.notna(f_phone):
        potential_matches = merged_df[merged_df['phone'].astype(str).str.replace('.0', '', regex=False) == str(f_phone)]
        if not potential_matches.empty:
            matched_idx = potential_matches.index[0]

    # If still no match, try matching by name
    if matched_idx == -1 and pd.notna(f_first):
        first_matches = merged_df[merged_df['first'].str.lower() == str(f_first).lower()]

        if not first_matches.empty:
            if pd.notna(f_last):
                # Try matching by both first and last name
                full_name_matches = first_matches[first_matches['last'].str.lower() == str(f_last).lower()]
                if not full_name_matches.empty:
                    # If multiple people have the same name, try to find the best match
                    if len(full_name_matches) == 1:
                        matched_idx = full_name_matches.index[0]
                    else:
                        # For multiple matches, prefer the one with matching email or phone
                        for idx_cand in full_name_matches.index:
                            crm_cand_email = merged_df.loc[idx_cand, 'email']
                            crm_cand_phone = merged_df.loc[idx_cand, 'phone']
                            if (pd.notna(f_email) and pd.notna(crm_cand_email) and str(f_email).lower() == str(crm_cand_email).lower()) or \
                               (pd.notna(f_phone) and pd.notna(crm_cand_phone) and str(f_phone) == str(crm_cand_phone).replace('.0', '', regex=False)):
                                matched_idx = idx_cand
                                break
                        if matched_idx == -1 and not full_name_matches.empty:  # If still no unique match, use the first one
                            matched_idx = full_name_matches.index[0]
                elif len(first_matches) == 1:  # If only one first name match and no last name match, use it
                    matched_idx = first_matches.index[0]
            elif len(first_matches) == 1:  # If only one first name match and no last name provided, use it
                matched_idx = first_matches.index[0]

    # Update existing contact or add new one
    if matched_idx != -1:
        # Update existing contact information
        current_crm_row = merged_df.loc[matched_idx]

        # Save the old contact entry before updating
        old_contact_entry = ""
        if pd.notna(current_crm_row['last contact date']) and pd.notna(current_crm_row['last contact text']):
            old_contact_entry = f"{current_crm_row['last contact date'].strftime('%Y-%m-%d')} - {current_crm_row['last contact text']}"

        # Update contact date and message if the new submission is more recent
        if pd.isna(current_crm_row['last contact date']) or f_timestamp > current_crm_row['last contact date']:
            merged_df.loc[matched_idx, 'last contact date'] = f_timestamp
            merged_df.loc[matched_idx, 'last contact text'] = f_message

        # Add the new message to the contact history
        new_all_contact_entry = f"{f_timestamp.strftime('%Y-%m-%d')} - {f_message}"
        current_all_contact_text = str(current_crm_row['all contact text']) if pd.notna(current_crm_row['all contact text']) else ""

        # Update the contact history, keeping the newest entries at the top
        updated_all_contact_text_parts = []
        if new_all_contact_entry not in current_all_contact_text:
            updated_all_contact_text_parts.append(new_all_contact_entry)
        
        # Add existing entries, avoiding duplicates
        existing_entries = [entry.strip() for entry in current_all_contact_text.split('\n\n') if entry.strip()]
        for entry in existing_entries:
            if entry not in updated_all_contact_text_parts:
                updated_all_contact_text_parts.append(entry)

        merged_df.loc[matched_idx, 'all contact text'] = '\n\n'.join(updated_all_contact_text_parts)

    else:
        # Create a new contact entry
        new_id = f'bfx-{new_contact_id_counter}'
        new_contact_id_counter += 1
        new_row = {
            'id': new_id,
            'first': f_first,
            'last': f_last,
            'email': f_email,
            'phone': f_phone,
            'last contact date': f_timestamp,
            'last contact text': f_message,
            'all contact text': f"{f_timestamp.strftime('%Y-%m-%d')} - {f_message}"
        }
        merged_df = pd.concat([merged_df, pd.DataFrame([new_row])], ignore_index=True)

# Format dates consistently as YYYY-MM-DD
merged_df['last contact date'] = merged_df['last contact date'].dt.strftime('%Y-%m-%d')

# Clean up phone numbers: remove '.0' suffix and ensure they're strings
merged_df['phone'] = merged_df['phone'].apply(lambda x: str(int(float(x))) if pd.notna(x) and isinstance(x, (float, np.number)) else str(x) if pd.notna(x) else '')

# Format names in title case (first letter of each word capitalized)
merged_df['first'] = merged_df['first'].apply(lambda x: str(x).title() if pd.notna(x) else x)
merged_df['last'] = merged_df['last'].apply(lambda x: str(x).title() if pd.notna(x) else x)

# Keywords to help categorize feedback (for internal use only)
problem_keywords = [
    'issue', 'problem', 'bug', 'difficult', 'confused', 'not working', 'error'
]
suggestion_keywords = [
    'please', 'need', 'next', 'more', 'better',
    'feature', 'request', 'suggestion', 'improve', 'can we', 'would like', 'missing'
]

# Find specific keywords in feedback text
def find_keywords_in_text(text, keywords_list):
    if pd.isna(text) or not isinstance(text, str):
        return []
    found = []
    for keyword in keywords_list:
        # Look for whole words only, ignoring case
        if re.search(r'\b' + re.escape(keyword) + r'\b', text, re.IGNORECASE):
            found.append(keyword)
    # Special handling for question marks
    if re.search(r'\?', text) and '?' not in found:
        found.append('?')
    return list(set(found))  # Return unique keywords

# Categorize feedback based on keywords (for internal use)
def get_feedback_action_status(last_contact_text):
    found_problem_keywords = find_keywords_in_text(last_contact_text, problem_keywords)
    if found_problem_keywords:
        return 'Urgent Review'

    found_suggestion_keywords = find_keywords_in_text(last_contact_text, suggestion_keywords)
    if found_suggestion_keywords:
        return 'Review for Improvement'

    return 'General Note'

# Keep only the required columns in the final output
final_columns = ['id', 'first', 'last', 'email', 'phone', 'last contact date', 'last contact text', 'all contact text']
merged_df = merged_df[final_columns]

# Clean up any remaining empty or invalid values
columns_to_clean = ['first', 'last', 'email', 'phone', 'last contact date', 'last contact text', 'all contact text']
for col in columns_to_clean:
    # Replace missing values with empty strings
    merged_df[col] = merged_df[col].replace({np.nan: '', None: ''})
    # Clean up string representations of missing values
    if merged_df[col].dtype == 'object':  # Only for text columns
        merged_df[col] = merged_df[col].astype(str).str.replace(r'^(nan|none|na)$' , '', flags=re.IGNORECASE, regex=True)

# Display the updated CRM data
print("\n[Original CRM Data]")
print(crm_df)
print("\n[Form Submission Data]")
print(form_df)
print("\n[Updated CRM Data (crm.csv)]")
print(merged_df)

# Save the original data files
crm_df.to_csv('raw_crm.csv', index=False)
form_df.to_csv('raw_form.csv', index=False)

# Save the updated CRM data
merged_df.to_csv('crm.csv', index=False)

# Sort the updated CRM data by date and last name
sort_crm_by_date_name(input_file='crm.csv', output_file='crm_update.csv')