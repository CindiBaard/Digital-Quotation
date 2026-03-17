import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import io

# 1. PAGE CONFIG
st.set_page_config(page_title="Digital Quotation System", layout="wide", page_icon="📝")

# 2. PDF GENERATION FUNCTION
def generate_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Header
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 10, "DIGITAL QUOTATION", ln=True, align="C")
    pdf.ln(10)
    
    # Metadata
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(40, 8, "Quote No:", 0)
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 8, f"{data['Quote No.']}", 0, 1)
    
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(40, 8, "Client:", 0)
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 8, f"{data['Client']}", 0, 1)
    
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(40, 8, "Date:", 0)
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 8, datetime.now().strftime("%Y-%m-%d"), 0, 1)
    
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
            
    # Summary Totals
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(130, 8, "Nett Total:", 0, 0, "R")
    pdf.cell(60, 8, f"R {data['Nett']:,.2f}", 0, 1, "R")
    
    pdf.cell(130, 8, "VAT (15%):", 0, 0, "R")
    pdf.cell(60, 8, f"R {data['Vat']:,.2f}", 0, 1, "R")
    
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(0, 123, 255) 
    pdf.cell(130, 10, "GROSS TOTAL:", 0, 0, "R")
    pdf.cell(60, 10, f"R {data['Gross']:,.2f}", 0, 1, "R")

    return pdf.output()

# 3. FIXED UNIT RATES
RATES = {
    "artwork_setup": 500.00,
    "adjust_artwork": 650.00,
    "layout_design": 800.00,
    "generate_barcode": 190.00,
    "photo_manip": 1000.00,
    "colour_retouch": 1000.00,
}

# 4. APP HEADER
st.title("📝 Digital Quotation Generator")

# 5. SIDEBAR INPUTS
with st.sidebar:
    st.header("📋 New Quotation Details")
    quote_no = st.text_input("Quote No.", value=f"Q-{datetime.now().strftime('%y%m%d%H%M')}")
    pre_prod_no = st.text_input("Pre-Prod No.")
    client = st.text_input("Client")
    description = st.text_area("Description / Project Name")
    
    st.divider()
    
    with st.expander("🛠️ Foil Cost Calculator (Internal Only)"):
        foil_nett_input = st.number_input("Supplier Nett Cost (Foil)", min_value=0.0, value=0.0, step=10.0)
        foil_markup_rate = 0.56
        calculated_foil_rate = foil_nett_input * (1 + foil_markup_rate)
        st.write(f"Marked up Rate (56%): **R{calculated_foil_rate:,.2f}**")

    st.subheader("🔢 Enter Units")
    u_artwork = st.number_input("Artwork setup and Trial", min_value=0, value=0, step=1)
    u_adjust = st.number_input("Adjust artwork supplied by Client", min_value=0, value=0, step=1)
    u_layout = st.number_input("Layout Design and Finished artwork", min_value=0, value=0, step=1)
    u_barcode = st.number_input("Generate Barcode", min_value=0, value=0, step=1)
    u_photo = st.number_input("Photo manipulation and Deep-etching", min_value=0, value=0, step=1)
    u_colour = st.number_input("Colour retouching", min_value=0, value=0, step=1)
    u_foil = st.number_input("Foil block", min_value=0, value=0, step=1)
    
    # Calculations
    amt_artwork = u_artwork * RATES["artwork_setup"]
    amt_adjust = u_adjust * RATES["adjust_artwork"]
    amt_layout = u_layout * RATES["layout_design"]
    amt_barcode = u_barcode * RATES["generate_barcode"]
    amt_photo = u_photo * RATES["photo_manip"]
    amt_colour = u_colour * RATES["colour_retouch"]
    amt_foil = u_foil * calculated_foil_rate
    
    nett_total = amt_artwork + amt_adjust + amt_layout + amt_barcode + amt_photo + amt_colour + amt_foil
    vat_total = nett_total * 0.15
    gross_total = nett_total + vat_total
    
    if st.button("Generate Quotation Preview", type="primary", use_container_width=True):
        st.session_state['last_quote'] = {
            "Quote No.": quote_no,
            "Pre-Prod No.": pre_prod_no,
            "Client": client,
            "Description": description,
            "items": [
                {"Service": "Artwork setup and Trial", "Qty": u_artwork, "Rate": RATES["artwork_setup"], "Total": amt_artwork},
                {"Service": "Adjust artwork supplied by Client", "Qty": u_adjust, "Rate": RATES["adjust_artwork"], "Total": amt_adjust},
                {"Service": "Layout Design and Finished artwork", "Qty": u_layout, "Rate": RATES["layout_design"], "Total": amt_layout},
                {"Service": "Generate Barcode", "Qty": u_barcode, "Rate": RATES["generate_barcode"], "Total": amt_barcode},
                {"Service": "Photo manipulation and Deep-etching", "Qty": u_photo, "Rate": RATES["photo_manip"], "Total": amt_photo},
                {"Service": "Colour retouching", "Qty": u_colour, "Rate": RATES["colour_retouch"], "Total": amt_colour},
                {"Service": "Foil block", "Qty": u_foil, "Rate": calculated_foil_rate, "Total": amt_foil},
            ],
            "Nett": nett_total,
            "Vat": vat_total,
            "Gross": gross_total
        }

# 6. MAIN AREA DISPLAY
if 'last_quote' in st.session_state:
    q = st.session_state['last_quote']
    st.subheader(f"Digital Quotation: {q['Quote No.']}")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Client:** {q['Client']}")
        st.write(f"**Pre-Prod No:** {q['Pre-Prod No.']}")
    with col2:
        st.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}")
        
    st.info(f"**Project:** {q['Description']}")
    
    df_display = pd.DataFrame(q['items'])
    df_display = df_display[df_display['Qty'] > 0]
    
    if not df_display.empty:
        df_formatted = df_display.copy()
        df_formatted['Rate'] = df_formatted['Rate'].map('R{:,.2f}'.format)
        df_formatted['Total'] = df_formatted['Total'].map('R{:,.2f}'.format)
        st.table(df_formatted)
    
        st.markdown(f"""
        <div style="text-align: right; font-size: 1.2em; background-color: #f0f2f6; padding: 15px; border-radius: 10px;">
            <p><b>Nett Total:</b> R{q['Nett']:,.2f}</p>
            <p><b>VAT (15%):</b> R{q['Vat']:,.2f}</p>
            <p style="color: #007BFF; font-size: 1.4em;"><b>GROSS TOTAL: R{q['Gross']:,.2f}</b></p>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # --- PDF DOWNLOAD ---
        pdf_output = generate_pdf(q)
        st.download_button(
            label="📥 Download Quote as PDF",
            data=bytes(pdf_output),
            file_name=f"Quotation_{q['Quote No.']}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    else:
        st.warning("Please enter at least 1 unit in the sidebar.")
else:
    st.info("👈 Enter units and client details in the sidebar and click 'Generate'.")