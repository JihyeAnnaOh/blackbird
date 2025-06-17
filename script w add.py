import requests
import pandas as pd
from io import StringIO
import ast # Import the ast module to safely evaluate string literals
import numpy as np # Import numpy for NaN handling
import re # Import re for regular expressions

# Helper function to split full names into first and last names
def parse_name(full_name):
    if pd.isna(full_name):
        return pd.Series([None, None])
    parts = str(full_name).strip().split()
    if len(parts) >= 2:
        return pd.Series([parts[0], ' '.join(parts[1:])])
    return pd.Series([parts[0], None])

# Set up API authorization header
# Replace 'your_access_token' with your actual token
headers = {
    'Authorization': 'Bearer your_access_token'
}

# Set base URL
BASE_URL = 'https://it-hiring.blackbird.vc'

# Get CRM data from the API (CSV format)
crm_url = f'{BASE_URL}/api/data/crm'
crm_response = requests.get(crm_url, headers=headers)
crm_df = pd.read_csv(StringIO(crm_response.text))

# Get form submissions from the API (JSON format)
form_url = f'{BASE_URL}/api/data/form-submissions'
form_response = requests.get(form_url, headers=headers)
form_data = form_response.json()

# Debug: print the structure of form_data
print('DEBUG: form_data =', form_data)

# Process form data and convert to DataFrame
form_df = pd.DataFrame(form_data)

# Clean up form data
# Split names into first and last
form_df[['form_first', 'form_last']] = form_df['form_name'].apply(parse_name)

# Extract and clean email addresses
form_df['form_email'] = form_df['form_message'].str.extract(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})')

# Extract and clean phone numbers
form_df['form_phone'] = form_df['form_message'].str.extract(r'(\d{10,})')
form_df['form_phone'] = pd.to_numeric(form_df['form_phone'], errors='coerce')

# Extract timestamps
form_df['form_timestamp'] = form_df['form_message'].str.extract(r'(\d{4}-\d{2}-\d{2})')

# Extract the actual message content
form_df['form_message'] = form_df['form_message'].str.replace(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '', regex=True)
form_df['form_message'] = form_df['form_message'].str.replace(r'\d{10,}', '', regex=True)
form_df['form_message'] = form_df['form_message'].str.replace(r'\d{4}-\d{2}-\d{2}', '', regex=True)
form_df['form_message'] = form_df['form_message'].str.strip()

# Save raw form data for reference
form_df.to_csv("raw_form.csv", index=False)

# Save raw CRM data for reference
crm_df.to_csv("raw_crm.csv", index=False)

# Merge form submissions with CRM data
# First, try to match by email
merged_df = pd.merge(crm_df, form_df, left_on='email', right_on='form_email', how='left')

# For unmatched records, try to match by phone
unmatched = merged_df[merged_df['form_email'].isna()]
matched_by_phone = pd.merge(unmatched, form_df, left_on='phone', right_on='form_phone', how='left')

# For still unmatched records, try to match by name
unmatched = matched_by_phone[matched_by_phone['form_phone'].isna()]
matched_by_name = pd.merge(unmatched, form_df, 
                          left_on=['first', 'last'], 
                          right_on=['form_first', 'form_last'], 
                          how='left')

# Combine all matches
merged_df = pd.concat([
    merged_df[~merged_df['form_email'].isna()],
    matched_by_phone[~matched_by_phone['form_phone'].isna()],
    matched_by_name[~matched_by_name['form_first'].isna()]
])

# Update CRM data with new form submissions
for idx, row in merged_df.iterrows():
    if pd.notna(row['form_timestamp']):
        # Update last contact date and text
        merged_df.at[idx, 'last contact date'] = row['form_timestamp']
        merged_df.at[idx, 'last contact text'] = row['form_message']
        
        # Update all contact text
        if pd.isna(merged_df.at[idx, 'all contact text']):
            merged_df.at[idx, 'all contact text'] = f"{row['form_timestamp']} - {row['form_message']}"
        else:
            merged_df.at[idx, 'all contact text'] = f"{row['form_timestamp']} - {row['form_message']}\n\n{merged_df.at[idx, 'all contact text']}"

# Add new contacts from form submissions
new_contacts = form_df[~form_df['form_email'].isin(merged_df['email']) & 
                      ~form_df['form_phone'].isin(merged_df['phone'])]

for _, row in new_contacts.iterrows():
    new_contact = {
        'id': f"bfx-{len(merged_df) + 1}",
        'first': row['form_first'],
        'last': row['form_last'],
        'email': row['form_email'],
        'phone': row['form_phone'],
        'last contact date': row['form_timestamp'],
        'last contact text': row['form_message'],
        'all contact text': f"{row['form_timestamp']} - {row['form_message']}"
    }
    merged_df = pd.concat([merged_df, pd.DataFrame([new_contact])], ignore_index=True)

# Clean up the data
# Remove '.0' from phone numbers
merged_df['phone'] = merged_df['phone'].astype(str).str.replace('.0', '')

# Define keywords for feedback analysis
keywords = [
    "number", "phone", "contact", "email", "address",
    "urgent", "asap", "immediately", "right away",
    "issue", "problem", "error", "bug", "broken",
    "security", "hack", "breach", "vulnerability",
    "complaint", "unhappy", "dissatisfied", "angry",
    "better", "improve", "enhance", "upgrade",
    "suggestion", "recommend", "advise", "propose",
    "location", "venue", "place", "room",
    "food", "coffee", "breakfast", "lunch", "dinner",
    "time", "schedule", "timing", "duration"
]

# Analyze feedback and assign action status based on keyword count
def analyze_feedback(text):
    if pd.isna(text):
        return "General Note"
    
    # Count how many keywords appear in the text
    keyword_count = sum(1 for keyword in keywords if keyword.lower() in text.lower())
    
    if keyword_count >= 3:
        return "Urgent Review"
    elif keyword_count >= 1:
        return "Review for Improvement"
    else:
        return "General Note"

# Apply feedback analysis to last contact text
merged_df['feedback_action_status'] = merged_df['last contact text'].apply(analyze_feedback)

# Clean up the data
# Replace string representations of NaN/None, case-insensitive
for col in merged_df.columns:
    if merged_df[col].dtype == 'object': # Only apply to object (string) columns
        merged_df[col] = merged_df[col].astype(str).str.replace(r'^(nan|none|na)$' , '', flags=re.IGNORECASE, regex=True)

# Sort the data by date and feedback status
# Convert 'last contact date' to datetime objects for proper sorting
merged_df['last contact date'] = pd.to_datetime(merged_df['last contact date'], errors='coerce')

# Define the custom order for feedback_action_status
feedback_order = ['Urgent Review', 'Review for Improvement', 'General Note', '']
# Create a categorical type with the custom order
merged_df['feedback_action_status'] = pd.Categorical(merged_df['feedback_action_status'], categories=feedback_order, ordered=True)

# Sort the DataFrame
# 1. By 'last contact date' in descending order (most recent first)
# 2. Then by 'feedback_action_status' using the custom order (ascending for the categorical type)
sorted_df = merged_df.sort_values(by=['last contact date', 'feedback_action_status'], ascending=[False, True])

# Convert 'last contact date' back to YYYY-MM-DD string format for output
sorted_df['last contact date'] = sorted_df['last contact date'].dt.strftime('%Y-%m-%d')

# Save the sorted DataFrame to a new CSV file
sorted_df.to_csv('crm_update.csv', index=False)

# Display the updated CRM data
print("\n[Original CRM Data]")
print(crm_df)
print("\n[Form Submission Data]")
print(form_df)
print("\n[Updated CRM Data (crm_update.csv)]")
print(sorted_df)
