# CRM Update Script

This script processes form submissions and updates the CRM data based on the latest contact information. It includes feedback analysis and sorting logic to prioritize urgent reviews.

## Features
- Fetches CRM data and form submissions from the API.
- Processes form submissions to update existing contacts or add new ones.
- Analyzes feedback text to assign action statuses based on keyword count.
- Sorts the updated CRM data by 'last contact date' (newest first) and 'feedback_action_status' (Urgent Review > Review for Improvement > General Note).

## Feedback Analysis
The script analyzes feedback text using a predefined list of keywords. The action status is assigned as follows:
- **Urgent Review**: If 3 or more keywords are found in the feedback text.
- **Review for Improvement**: If 1 or 2 keywords are found.
- **General Note**: If no keywords are found or the feedback is missing.

## Output
The updated CRM data is saved to `crm_update.csv`, and the sorted data is displayed in the console.

## Usage
Run the script using Python 3:
```bash
python3 submission_add/script_add.py
```

## Dependencies
- Python 3.x
- pandas
- requests
- numpy
- re

## Data Structure

### CRM Data Fields
- `id`: Unique identifier
- `first`: First name
- `last`: Last name
- `email`: Email address
- `phone`: Phone number
- `last contact date`: Most recent contact date
- `last contact text`: Most recent message
- `all contact text`: Complete contact history
- `feedback_action_status`: Categorized feedback status

### Form Submission Fields
- `form_first`: First name
- `form_last`: Last name
- `form_email`: Email address
- `form_phone`: Phone number
- `form_timestamp`: Submission date
- `form_message`: Feedback message

## Error Handling

The script includes comprehensive error handling for:
- API connection issues
- Data parsing errors
- Missing or malformed data
- File I/O operations

## Notes

- The script maintains data integrity by preserving all historical information
- Feedback analysis is performed automatically on new submissions
- Sorting is applied to the final output for easy review of recent and urgent items
- Phone numbers are standardized to remove decimal points
- Dates are formatted consistently as YYYY-MM-DD 