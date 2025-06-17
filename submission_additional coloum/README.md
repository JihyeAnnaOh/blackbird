# BlackBird CRM Data Processing Script

This script processes and manages CRM data by integrating form submissions with existing CRM records, analyzing feedback, and maintaining a sorted contact history provided by BLACKBIRD.

## Features

### 1. Data Collection and Processing
- Fetches CRM data from the API endpoint
- Retrieves form submissions from the API endpoint
- Processes and cleans data from both sources

### 2. Contact Management
- Merges form submissions with existing CRM data
- Updates existing contacts based on matching criteria:
  - Email address
  - Phone number
  - Name (first and last)
- Adds new contacts from form submissions
- Maintains complete contact history

### 3. Feedback Analysis
- Analyzes feedback messages for key topics:
  - Product features
  - Events and meetups
  - Content and newsletters
  - Technical issues
  - General feedback
- Categorizes feedback into action statuses:
  - Urgent Review
  - Review for Improvement
  - General Note

### Feedback Action Status Categorization Logic

The script categorizes feedback based on the number of keywords found in the message. The same set of keywords is used for all categories, but the count determines the priority level:

Keywords used for analysis:
- "number", "phone", "contact", "email", "address"
- "urgent", "asap", "immediately", "right away"
- "issue", "problem", "error", "bug", "broken"
- "security", "hack", "breach", "vulnerability"
- "complaint", "unhappy", "dissatisfied", "angry"
- "better", "improve", "enhance", "upgrade"
- "suggestion", "recommend", "advise", "propose"
- "location", "venue", "place", "room"
- "food", "coffee", "breakfast", "lunch", "dinner"
- "time", "schedule", "timing", "duration"

Categorization based on keyword count:
1. **Urgent Review** (Highest Priority)
   - Assigned when 3 or more keywords are found in the message
   - Example: "Can you please provide me Maria's number so I can send her some information from a conversation we had?" (contains "number", "information", "conversation")

2. **Review for Improvement** (Medium Priority)
   - Assigned when 1-2 keywords are found in the message
   - Examples:
     - "Location could have been better" (contains "location", "better")
     - "More coffee next time" (contains "coffee")
     - "Breakfast was a little cold but otherwise good" (contains "breakfast")

3. **General Note** (Default Priority)
   - Assigned when no keywords are found in the message
   - Examples:
     - "The content was excellent as always"
     - "The offsite was fantastic"
     - "I had some great conversations"

The categorization process:
1. Counts the number of keywords present in the feedback message
2. Assigns category based on the count:
   - 3+ keywords → Urgent Review
   - 1-2 keywords → Review for Improvement
   - 0 keywords → General Note

This count-based approach ensures that messages with multiple relevant keywords are prioritized for urgent review, while simpler feedback is categorized appropriately.

### 4. Data Cleaning and Formatting
- Formats phone numbers (removes '.0' suffix)
- Standardizes date formats
- Handles missing values appropriately
- Cleans and formats text fields

### 5. Sorting and Organization
- Sorts data by multiple criteria:
  1. Last contact date (newest first)
  2. Feedback action status (priority order):
     - Urgent Review
     - Review for Improvement
     - General Note
- Maintains chronological order within each status category

## Output Files

The script generates three CSV files:

1. `raw_crm.csv`
   - Contains the original CRM data
   - Preserves all original fields and formatting

2. `raw_form.csv`
   - Contains the original form submission data
   - Includes all form fields as received

3. `crm_update.csv`
   - Contains the merged and processed data
   - Includes all CRM fields plus:
     - Updated contact information
     - Complete contact history
     - Feedback analysis results
     - Action status
   - Sorted by date and feedback status

## How to Run

1. Ensure you have Python 3.x installed
2. Install required packages:
   ```bash
   pip install requests pandas numpy
   ```
3. Run the script:
   ```bash
   python "script w addtional.py"
   ```

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