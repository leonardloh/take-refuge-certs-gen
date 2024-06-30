import streamlit as st
import pandas as pd
import io
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import zipfile
import os

def add_textboxes_to_pdf(input_pdf, output_pdf, texts, date, font_path, font_name, name_font_size, date_font_size, page_num=0):
    coordinates = [(160, 355), (160, 90), (149, 50)]
    pdfmetrics.registerFont(TTFont(font_name, font_path))
    
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    
    for text, (x, y) in zip(texts, coordinates[:2]):
        can.setFont(font_name, name_font_size)
        can.drawString(x, y, text)
    
    can.setFont(font_name, date_font_size)
    can.drawString(coordinates[2][0], coordinates[2][1], date)
    
    can.save()
    packet.seek(0)
    new_pdf = PdfReader(packet)

    with open(input_pdf, "rb") as existing_file:
        existing_pdf = PdfReader(existing_file)
        output = PdfWriter()

        page = existing_pdf.pages[page_num]
        page.merge_page(new_pdf.pages[0])
        output.add_page(page)

        for i in range(len(existing_pdf.pages)):
            if i != page_num:
                output.add_page(existing_pdf.pages[i])

        with open(output_pdf, "wb") as output_stream:
            output.write(output_stream)

def generate_pdfs(df, date, template_pdf, font_path):
    output_files = []
    for index, row in df.iterrows():
        chinese_name = row['中文姓名 Chinese Name']
        dharma_name = row['法名']
        texts = [chinese_name, dharma_name]
        
        output_pdf = f"output_{chinese_name}_{dharma_name}.pdf"
        add_textboxes_to_pdf(template_pdf, output_pdf, texts, date, font_path, "Kaiti-Bold", 16, 11)
        output_files.append(output_pdf)
    return output_files

st.title("皈依证 PDF Generator App")

uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
date = st.date_input("Select a date")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    # Get unique locations from the CSV
    location_column = "我要参与的地点：（请选择一个）"
    locations = df[location_column].unique().tolist()
    
    # Create a dropdown for location selection
    selected_location = st.selectbox("Select a location", locations)
    
    # Filter the dataframe based on selected location and valid entries
    df_filtered = df[(df[location_column] == selected_location) & (df['法名'].notna())][['中文姓名 Chinese Name','法名']]
    st.write(f"Loaded {len(df_filtered)} valid entries for {selected_location}")

    if st.button("Generate PDFs"):
        template_pdf = "sy_template.pdf"  # Ensure this file is in the same directory as your script
        font_path = "font/Kaiti-SC-Bold.ttf"  # Ensure this file is in the same directory as your script
        
        formatted_date = date.strftime("%Y年%m月%d日")
        
        output_files = generate_pdfs(df_filtered, formatted_date, template_pdf, font_path)
        
        # Create a zip file containing all generated PDFs
        zip_filename = f"generated_pdfs_{selected_location}.zip"
        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            for file in output_files:
                zipf.write(file)
                os.remove(file)  # Remove individual PDF files after adding to zip
        
        # Offer the zip file for download
        with open(zip_filename, "rb") as f:
            bytes = f.read()
            st.download_button(
                label="Download PDFs",
                data=bytes,
                file_name=zip_filename,
                mime="application/zip"
            )
        
        os.remove(zip_filename)  # Remove the zip file after offering download
        st.success(f"Generated {len(output_files)} PDFs for {selected_location}. Click the button above to download.")