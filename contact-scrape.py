import streamlit as st
import pandas as pd
import re
from io import StringIO

st.set_page_config(page_title="Contact Extractor", layout="wide")
st.title("📄 Contact Extractor from CSV")

# Upload CSV file
uploaded_file = st.file_uploader("Upload your CSV file", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.success("File uploaded successfully!")

    # Let user choose which column contains the contact data
    contact_column = st.selectbox("Select the column with contact info", df.columns)

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
                    'First Name': re.search(r'\* First Name:\s*(.*)', entry).group(1).strip() if re.search(r'\* First Name:\s*(.*)', entry) else "Not listed",
                    'Last Name': re.search(r'\* Last Name:\s*(.*)', entry).group(1).strip() if re.search(r'\* Last Name:\s*(.*)', entry) else "Not listed",
                    'Job Title': re.search(r'\* Job Title:\s*(.*)', entry).group(1).strip() if re.search(r'\* Job Title:\s*(.*)', entry) else "Not listed",
                    'Phone': re.search(r'\* Phone:\s*(.*)', entry).group(1).strip() if re.search(r'\* Phone:\s*(.*)', entry) else "Not listed",
                    'Email': re.search(r'\* Email:\s*(.*)', entry).group(1).strip() if re.search(r'\* Email:\s*(.*)', entry) else "Not listed"
                }

                contact.update(row.drop(contact_column).to_dict())
                contacts.append(contact)

        if contacts:
            results_df = pd.DataFrame(contacts)
            st.success(f"✅ Extracted {len(contacts)} contacts")

            st.dataframe(results_df)

            # Download button
            csv = results_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download CSV", csv, "extracted_contacts.csv", "text/csv")
        else:
            st.warning("No contacts found in the selected column.")
