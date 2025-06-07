import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Contact Extractor", layout="wide")
st.title("📄 Contact Extractor from CSV")

# 🧠 Prompt Format Reminder
st.info("""
Please ensure your prompt includes this formatting so contact data can be extracted cleanly:

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

# File Upload
uploaded_file = st.file_uploader("📄 Upload your CSV file", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.success("✅ File uploaded successfully!")

    # Column selector
    contact_column = st.selectbox("📌 Select the column with contact info", df.columns)

    if st.button("Extract Contacts"):
        contacts = []

        for _, row in df.iterrows():
            block = row[contact_column]
            if not isinstance(block, str) or "* First Name:" not in block:
                continue

            entries = re.split(r'\* First Name:', block)
            for entry in entries[1:]:
                entry = "* First Name:" + entry  # Restore removed split

                contact = {
                    'First Name': re.search(r'\* First Name:\s*(.*)', entry).group(1).strip() if re.search(r'\* First Name:\s*(.*)', entry) else "Not listed",
                    'Last Name': re.search(r'\* Last Name:\s*(.*)', entry).group(1).strip() if re.search(r'\* Last Name:\s*(.*)', entry) else "Not listed",
                    'Job Title': re.search(r'\* Job Title:\s*(.*)', entry).group(1).strip() if re.search(r'\* Job Title:\s*(.*)', entry) else "Not listed",
                    'Phone': re.search(r'\* Phone:\s*(.*)', entry).group(1).strip() if re.search(r'\* Phone:\s*(.*)', entry) else "Not listed",
                    'Email': re.search(r'\* Email:\s*(.*)', entry).group(1).strip() if re.search(r'\* Email:\s*(.*)', entry) else "Not listed"
                }

                # Merge in metadata
                contact.update(row.drop(contact_column).to_dict())
                contacts.append(contact)

        if contacts:
            results_df = pd.DataFrame(contacts)
            st.success(f"✅ Extracted {len(contacts)} contacts successfully!")
            st.dataframe(results_df)

            csv = results_df.to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ Download CSV", csv, "extracted_contacts.csv", "text/csv")
        else:
            st.warning("⚠️ No contacts found. Make sure the column follows the expected format.")
