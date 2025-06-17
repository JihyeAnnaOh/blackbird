# CRM Data Update and Sorting

This project consists of a Python script designed to update and sort CRM (Customer Relationship Management) contact data based on event feedback and specific sorting criteria provided by BLACKBIRD.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Project Overview](#project-overview)
- [API Access](#api-access)
- [How to Run](#how-to-run)
- [Output Files](#output-files)
- [Troubleshooting](#troubleshooting)

## Prerequisites
Before running the script, ensure you have the following installed:
- Python 3.x
- pip (Python package installer)

### Setting up the Environment

#### For macOS/Linux:
1. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

#### For Windows:
1. Create a virtual environment:
```cmd
python -m venv venv
venv\Scripts\activate
```

2. Install the necessary Python libraries (same for all platforms):
```bash
pip install requests pandas numpy
```


#### CRM Data API
- **Endpoint**: `https://api.example.com/crm-data` (replace with actual endpoint)
- **Response Format**: JSON array of objects containing:
  - `id`: Unique identifier
  - `first`: First name
  - `last`: Last name
  - `email`: Email address
  - `phone`: Phone number
  - `last contact date`: Date of last contact
  - `last contact text`: Text of last contact
  - `all contact text`: All contact history

#### Form Submission API
- **Endpoint**: `https://api.example.com/form-submissions` (replace with actual endpoint)
- **Response Format**: JSON array of objects containing:
  - `name`: Full name
  - `email`: Email address
  - `phone`: Phone number
  - `feedback`: Event feedback text
  - `submission_date`: Date of form submission

## Project Overview

### `script.py`
This script is responsible for:
1. **Data Collection**:
   - Fetching the latest CRM data from the CRM Data API
   - Fetching event feedback form submission data from the Form Submission API

2. **Data Processing**:
   - Extracting `first` and `last` names from a `name` field, handling multi-word names by taking the first and last word
   - Cleaning phone numbers by removing `+` and spaces, and ensuring no '.0' suffix
   - Validating email and phone formats using regular expressions, treating invalid entries as missing
   - Converting dates to proper datetime format for comparison

3. **Data Merging**:
   - Merging the CRM data with the form submission data using a sophisticated tiered matching logic:
     1. First try matching by email (most reliable)
     2. If no email match, try matching by phone number
     3. If still no match, try matching by name (first and last)
   - For multiple name matches, prefer the one with matching email or phone
   - Creating new contact entries for unmatched form submissions

4. **Contact History Management**:
   - Updating contact information (`last contact date`, `last contact text`, `all contact text`)
   - Prioritizing the newest information
   - Maintaining a chronological history of all contacts
   - Ensuring no duplicate entries in contact history

5. **Data Cleaning and Formatting**:
   - Ensuring 'first' and 'last' names are in title case
   - Formatting dates consistently as YYYY-MM-DD
   - Cleaning phone numbers to remove '.0' suffix
   - Replacing all `None`, `NaN`, and case-insensitive string representations of `nan`, `none`, or `na` with empty strings

6. **Data Sorting**:
   - Sorting the final data by:
     1. Primary sort: `last contact date` (descending - newest first)
     2. Secondary sort: `last` name (ascending - alphabetized)
   - Generating a sorted output file

7. **Output Generation**:
   - Creating `raw_crm.csv` with original CRM data
   - Creating `raw_form.csv` with original form data
   - Creating `crm_update.csv` with updated and merged data
   - Creating `crm_update_sorted_date_name.csv` with sorted data

## How to Run

Follow these steps to run the script and generate updated and sorted CRM data:

1. **Clone or download the repository:**
```bash
git clone <repository-url>
cd <repository-directory>
```

2. **Set up the environment:**

#### For macOS/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
pip install requests pandas numpy
```

#### For Windows:
```cmd
python -m venv venv
venv\Scripts\activate
pip install requests pandas numpy
```

3. **Run the script:**

#### For macOS/Linux:
```bash
python3 submission/script.py
```

#### For Windows:
```cmd
python submission\script.py
```

The script will automatically:
- Process the CRM and form data
- Generate the unsorted `crm_update.csv`
- Create the sorted `crm_update_sorted_date_name.csv`
- Display the data at each step

## Output Files

The script will generate the following files in current directory:

1. **raw_crm.csv**: Original CRM data from the API
2. **raw_form.csv**: Original form submission data from the API
3. **crm_update.csv**: Updated and merged data (unsorted)
   - Required columns: `id`, `first`, `last`, `email`, `phone`, `last contact date`, `last contact text`, `all contact text`
4. **crm_update_sorted_date_name.csv**: Data sorted by date and last name
   - Sorted by most recent date first
   - Within each date, sorted alphabetically by last name

## Troubleshooting

### Common Issues and Solutions:

1. **ModuleNotFoundError: No module named 'pandas'**
   - Solution: Make sure you've activated the virtual environment and installed the required packages:
   
   #### For macOS/Linux:
   ```bash
   source venv/bin/activate
   pip install requests pandas numpy
   ```
   
   #### For Windows:
   ```cmd
   venv\Scripts\activate
   pip install requests pandas numpy
   ```

2. **FileNotFoundError: The file was not found**
   - Solution: Make sure you're running the script from the correct directory
   - The scripts expect to find the input files in the current directory

3. **Phone number format issues**
   - The script automatically handles phone number formatting
   - Removes '+', spaces, and '.0' suffixes
   - Converts to clean string format


### Notes:
- All scripts should be run from the project root directory
- The virtual environment needs to be activated only once per terminal session
- The output files will be created in the current directory
- Phone numbers are automatically cleaned and formatted
- Dates are stored in YYYY-MM-DD format
- Names are automatically converted to title case
- The `crm_update.csv` file must maintain the exact column structure specified in the requirements 