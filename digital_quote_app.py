import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import gspread
from google.oauth2.service_account import Credentials
import io

# ==========================================
# 1. INITIAL SETUP & CONFIG
# ==========================================
st.set_page_config(page_title="Digital Quotation System", layout="wide", page_icon="📝")

# --- Fixed Unit Rates ---
RATES = {
    "artwork_setup": 500.00,
    "adjust_artwork": 650.00,
    "layout_design": 800.00,
    "generate_barcode": 190.00,
    "photo_manip": 1000.00,
    "colour_retouch": 1000.00,
}

# ==========================================
# 2. HELPER FUNCTIONS (Place at top)
# ==========================================

def get_gsheet_client():
    """Authenticates using Streamlit Secrets."""
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    
    # Updated this line to match your specific secret header:
    creds_dict = st.secrets["connections"]["gsheets"] 
    
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    return gspread.authorize(creds)

def update_spreadsheet(data):
    """Appends quote totals to the Google Sheet."""
    try:
        client = get_gsheet_client()
        sheet_id = "1wGEVCxH4wEra_BRa-3z9QWaH8g5dvCQy-xO2-KJhciM"
        sheet = client.open_by_key(sheet_id).sheet1
        
        # Prepare row data (adjust columns as needed for your sheet)
        row = [
            data["Quote No."],
            data["Pre-Prod No."],
            data["Client"],
            data["Description"],
            data["Nett"],
            data["Vat"],
            data["Gross"],
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ]
        sheet.append_row(row)
        return True
    except Exception as e:
        st.error(f"Google Sheets Error: {e}")
        return False

def generate_pdf(data):
    """Generates a professional PDF document."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Header
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 10, "DIGITAL QUOTATION", ln=True, align="C")
    pdf.ln(10)
    
    # Metadata
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(40, 8, "Quote No:", 0); pdf.set_font("Helvetica", "", 12); pdf.cell(0, 8, f"{data['Quote No.']}", 0, 1)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(40, 8, "Client:", 0); pdf.set_font("Helvetica", "", 12); pdf.cell(0, 8, f"{data['Client']}", 0, 1)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(40, 8, "Date:", 0); pdf.set_font("Helvetica", "", 12); pdf.cell(0, 8, datetime.now().strftime("%Y-%m-%d"), 0, 1)
    
    pdf.ln(5)
    pdf.set_font("Helvetica", "I", 11)
    pdf.multi_cell(0, 8, f"Project Description: {data['Description']}")
    pdf.ln(10)
    
    # Table Header
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(100, 10, "Service Description", 1, 0, "C", fill=True)
    pdf.cell(30, 10, "Qty", 1, 0, "C", fill=True)
    pdf.cell(60, 10, "Total", 1, 1, "C", fill=True)
    
    # Table Rows
    pdf.set_font("Helvetica", "", 10)
    for item in data['items']:
        if item['Qty'] > 0:
            pdf.cell(100, 10, item['Service'], 1)
            pdf.cell(30, 10, str(item['Qty']), 1, 0, "C")
            pdf.cell(60, 10, f"R {item['Total']:,.2f}", 1, 1, "R")
            
    # Summary
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(130, 8, "Nett Total:", 0, 0, "R"); pdf.cell(60, 8, f"R {data['Nett']:,.2f}", 0, 1, "R")
    pdf.cell(130, 8, "VAT (15%):", 0, 0, "R"); pdf.cell(60, 8, f"R {data['Vat']:,.2f}", 0, 1, "R")
    pdf.set_font("Helvetica", "B", 13); pdf.set_text_color(0, 123, 255)
    pdf.cell(130, 10, "GROSS TOTAL:", 0, 0, "R"); pdf.cell(60, 10, f"R {data['Gross']:,.2f}", 0, 1, "R")

    return pdf.output()

# ==========================================
# 3. STREAMLIT UI
# ==========================================
st.title("📝 Digital Quotation Generator")

# --- Sidebar Inputs ---
with st.sidebar:
    st.header("📋 New Quotation Details")
    quote_no = st.text_input("Quote No.", value=f"Q-{datetime.now().strftime('%y%m%d%H%M')}")
    pre_prod_no = st.text_input("Pre-Prod No.")
    client = st.text_input("Client")
    description = st.text_area("Description / Project Name")
    
    st.divider()
    
    with st.expander("🛠️ Foil Cost Calculator (Internal Only)"):
        f_nett = st.number_input("Supplier Nett Cost (Foil)", min_value=0.0, value=0.0, step=10.0)
        f_rate = f_nett * 1.56 # 56% markup
        st.write(f"Marked up Rate: **R{f_rate:,.2f}**")

    st.subheader("🔢 Enter Units")
    u_artwork = st.number_input("Artwork setup and Trial", min_value=0, value=0, step=1)
    u_adjust = st.number_input("Adjust artwork supplied by Client", min_value=0, value=0, step=1)
    u_layout = st.number_input("Layout Design and Finished artwork", min_value=0, value=0, step=1)
    u_barcode = st.number_input("Generate Barcode", min_value=0, value=0, step=1)
    u_photo = st.number_input("Photo manipulation and Deep-etching", min_value=0, value=0, step=1)
    u_colour = st.number_input("Colour retouching", min_value=0, value=0, step=1)
    u_foil = st.number_input("Foil block", min_value=0, value=0, step=1)
    
    # Calculate Totals
    items_data = [
        {"Service": "Artwork setup and Trial", "Qty": u_artwork, "Total": u_artwork * RATES["artwork_setup"]},
        {"Service": "Adjust artwork supplied by Client", "Qty": u_adjust, "Total": u_adjust * RATES["adjust_artwork"]},
        {"Service": "Layout Design and Finished artwork", "Qty": u_layout, "Total": u_layout * RATES["layout_design"]},
        {"Service": "Generate Barcode", "Qty": u_barcode, "Total": u_barcode * RATES["generate_barcode"]},
        {"Service": "Photo manipulation and Deep-etching", "Qty": u_photo, "Total": u_photo * RATES["photo_manip"]},
        {"Service": "Colour retouching", "Qty": u_colour, "Total": u_colour * RATES["colour_retouch"]},
        {"Service": "Foil block", "Qty": u_foil, "Total": u_foil * f_rate},
    ]
    
    nett_total = sum(item["Total"] for item in items_data)
    vat_total = nett_total * 0.15
    gross_total = nett_total + vat_total
    
    # --- The Generate Button (Triggers Save & View) ---
    if st.button("Generate & Save Quote", type="primary", use_container_width=True):
        st.session_state['last_quote'] = {
            "Quote No.": quote_no, "Pre-Prod No.": pre_prod_no, "Client": client,
            "Description": description, "items": items_data,
            "Nett": nett_total, "Vat": vat_total, "Gross": gross_total
        }
        
        # Save to Google Sheets automatically
        with st.status("Saving data to Google Sheets...") as status:
            if update_spreadsheet(st.session_state['last_quote']):
                status.update(label="✅ Saved to Google Sheets!", state="complete")
            else:
                status.update(label="❌ Failed to save to Sheets.", state="error")
        
        st.balloons()

# --- Main Area Display ---
if 'last_quote' in st.session_state:
    q = st.session_state['last_quote']
    st.subheader(f"Quotation Preview: {q['Quote No.']}")
    
    st.write(f"**Client:** {q['Client']} | **Pre-Prod:** {q['Pre-Prod No.']} | **Date:** {datetime.now().strftime('%Y-%m-%d')}")
    st.info(f"**Project:** {q['Description']}")

    # Create a new tab for Database view
tab1, tab2 = st.tabs(["📄 Quotation Preview", "📊 Spreadsheet Database"])

with tab1:
    # ... (Keep your existing Quote Preview and PDF code here) ...
    pass

with tab2:
    st.subheader("Google Sheets Database")
    
    # Option 1: A big button to open the actual sheet for editing
    sheet_url = f"https://docs.google.com/spreadsheets/d/1wGEVCxH4wEra_BRa-3z9QWaH8g5dvCQy-xO2-KJhciM/edit"
    st.link_button("🚀 Open Full Spreadsheet (Edit Mode)", sheet_url, use_container_width=True)
    
    st.divider()
    
    # Option 2: Show the data live in the app
    if st.button("🔄 Refresh Data View"):
        try:
            client = get_gsheet_client()
            sheet = client.open_by_key("1wGEVCxH4wEra_BRa-3z9QWaH8g5dvCQy-xO2-KJhciM").sheet1
            
            # Read all records into a Dataframe
            data = sheet.get_all_records()
            df_db = pd.DataFrame(data)
            
            if not df_db.empty:
                st.dataframe(df_db, use_container_width=True)
            else:
                st.info("The spreadsheet is currently empty.")
        except Exception as e:
            st.error(f"Could not load data: {e}")
    
    # Filter and Display Table
    df = pd.DataFrame(q['items'])
    df = df[df['Qty'] > 0]
    
    if not df.empty:
        st.table(df.assign(Total=lambda x: x.Total.map('R{:,.2f}'.format)))
        
        st.markdown(f"""
        <div style="text-align: right; font-size: 1.2em; background-color: #f0f2f6; padding: 15px; border-radius: 10px;">
            <p><b>Nett Total:</b> R{q['Nett']:,.2f}</p>
            <p><b>VAT (15%):</b> R{q['Vat']:,.2f}</p>
            <p style="color: #007BFF; font-size: 1.4em;"><b>GROSS TOTAL: R{q['Gross']:,.2f}</b></p>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # PDF Download Button
        pdf_bytes = generate_pdf(q)
        st.download_button(
            label="📥 Download Quote as PDF",
            data=bytes(pdf_bytes),
            file_name=f"Quotation_{q['Quote No.']}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    else:
        st.warning("Please enter at least 1 unit to generate a preview.")
else:
    st.info("👈 Enter details in the sidebar and click 'Generate & Save Quote'.")