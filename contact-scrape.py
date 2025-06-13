import streamlit as st
import pandas as pd
import re
from collections import defaultdict, Counter

st.set_page_config(page_title="Contact Extractor", layout="wide")
st.title("📄 Contact Extractor from CSV")

# 🧠 Prompt Format Reminder
st.info("""
When generating your contact list, please include this text in your prompt so contact data can be extracted cleanly:

```
Please list them in the following format (one person per section):
* First Name: [First Name]
* Last Name: [Last Name]
* Job Title: [Job Title]
* Phone: [Phone Number]
* Email: [Email Address]

If any information is not available, please write "Not listed".
Please use this format exactly.
```

This format ensures the tool can consistently parse each contact entry.
""")

# Utility Functions
def clean(value):
    if not isinstance(value, str):
        return value
    return re.sub(r'\[\d+\]', '', value).strip()

def extract_field(pattern, entry):
    match = re.search(pattern, entry, re.DOTALL)
    return clean(match.group(1)) if match else "Not listed"

def generate_user_from_pattern(first, last, pattern):
    first = first.lower()
    last = last.lower()
    if not first or not last or first == "not listed" or last == "not listed":
        return None
    return {
        "first_last": f"{first}_{last}",
        "first.last": f"{first}.{last}",
        "firstlast": f"{first}{last}",
        "f.last": f"{first[0]}.{last}",
        "firstl": f"{first}{last[0]}",
        "flast": f"{first[0]}{last}",
        "lastf": f"{last}{first[0]}",
        "last.first": f"{last}.{first}",
        "last_first": f"{last}_{first}",
    }.get(pattern)

def all_patterns(first, last):
    return {
        "first_last": f"{first.lower()}_{last.lower()}",
        "first.last": f"{first.lower()}.{last.lower()}",
        "firstlast": f"{first.lower()}{last.lower()}",
        "f.last": f"{first[0].lower()}.{last.lower()}",
        "firstl": f"{first.lower()}{last[0].lower()}",
        "flast": f"{first[0].lower()}{last.lower()}",
        "lastf": f"{last.lower()}{first[0].lower()}",
        "last.first": f"{last.lower()}.{first.lower()}",
        "last_first": f"{last.lower()}_{first.lower()}",
    }

def match_pattern(first, last, email):
    if pd.isna(email) or "@" not in email:
        return None
    user, domain = email.lower().split("@")
    for pattern, value in all_patterns(first, last).items():
        if user == value:
            return pattern, domain
    return None

def infer_patterns(df):
    district_patterns = defaultdict(list)
    for _, row in df.iterrows():
        first, last, email, district = row['First Name'], row['Last Name'], row.get('Email'), row.get('Institution Name', '')
        match = match_pattern(first, last, email)
        if match:
            pattern, domain = match
            district_patterns[district].append((pattern, domain))

    dominant = {}
    for district, entries in district_patterns.items():
        if not entries:
            continue
        pattern_counts = Counter([p for p, _ in entries])
        most_common_pattern = pattern_counts.most_common(1)[0][0]
        domain = entries[0][1]  # assume same domain
        dominant[district] = (most_common_pattern, domain)
    return dominant

def generate_speculative_emails(df):
    df = df.copy()
    patterns_by_district = infer_patterns(df)

    speculative_emails = []
    for _, row in df.iterrows():
        first = row['First Name']
        last = row['Last Name']
        email = row['Email']
        district = row.get('Institution Name', '')

        if pd.notna(email) and email != "Not listed":
            speculative_emails.append(email)
        elif first != "Not listed" and last != "Not listed" and district in patterns_by_district:
            pattern, domain = patterns_by_district[district]
            user = generate_user_from_pattern(first, last, pattern)
            speculative_emails.append(f"{user}@{domain}" if user else "Not listed")
        else:
            speculative_emails.append("Not listed")

    df['Speculative Email'] = speculative_emails
    return df

# Streamlit UI
uploaded_file = st.file_uploader("📄 Upload your CSV file", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.success("✅ File uploaded successfully!")

    contact_column = st.selectbox("📌 Select the column with contact info", df.columns)

    if st.button("Extract Contacts"):
        contacts = []

        for _, row in df.iterrows():
            block = row[contact_column]
            if not isinstance(block, str) or "* First Name:" not in block:
                continue

            entries = re.split(r'\* First Name:', block)
            for entry in entries[1:]:
                entry = "* First Name:" + entry
                contact = {
                    'First Name': extract_field(r'\* First Name:\s*(.*?)\s*(?=\*|$)', entry),
                    'Last Name': extract_field(r'\* Last Name:\s*(.*?)\s*(?=\*|$)', entry),
                    'Job Title': extract_field(r'\* Job Title:\s*(.*?)\s*(?=\*|$)', entry),
                    'Phone': extract_field(r'\* Phone:\s*(.*?)\s*(?=\*|$)', entry),
                    'Email': extract_field(r'\* Email:\s*(.*?)\s*(?=\*|$)', entry)
                }
                contact.update(row.drop(contact_column).to_dict())
                contacts.append(contact)

        if contacts:
            results_df = pd.DataFrame(contacts)
            results_df = generate_speculative_emails(results_df)
            st.success(f"✅ Extracted {len(results_df)} contacts!")
            st.dataframe(results_df)

            csv = results_df.to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ Download CSV", csv, "extracted_contacts.csv", "text/csv")
        else:
            st.warning("⚠️ No contacts found. Make sure the column follows the expected format.")
