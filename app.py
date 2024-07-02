import streamlit as st
import pandas as pd
import io
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A5, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import zipfile
import os

def add_textboxes_to_pdf(input_pdf, output_pdf, texts, date, font_path, font_name, name_font_size, date_font_size, page_num=0):
    coordinates = [(160, 355), (160, 90), (149, 50)]
    pdfmetrics.registerFont(TTFont(font_name, font_path))
    
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=A5)
    
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

def create_blank_pdf_with_text(output_pdf, texts, date, font_path, font_name, name_font_size, date_font_size):
    coordinates = [(160, 355), (160, 90), (149, 50)]
    pdfmetrics.registerFont(TTFont(font_name, font_path))
    
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=landscape(A5))
    
    for text, (x, y) in zip(texts, coordinates[:2]):
        can.setFont(font_name, name_font_size)
        can.drawString(x, y, text)
    
    can.setFont(font_name, date_font_size)
    can.drawString(coordinates[2][0], coordinates[2][1], date)
    
    can.save()
    packet.seek(0)

    with open(output_pdf, "wb") as output_stream:
        output_stream.write(packet.getvalue())

def generate_pdfs(df, date, template_pdf, font_path, use_blank_template):
    output_files = []
    for index, row in df.iterrows():
        chinese_name = row['中文姓名 Chinese Name']
        dharma_name = row['法名']
        texts = [chinese_name, dharma_name]
        
        output_pdf = f"output_{chinese_name}_{dharma_name}.pdf"
        if use_blank_template:
            create_blank_pdf_with_text(output_pdf, texts, date, font_path, "Kaiti-Bold", 16, 11)
        else:
            add_textboxes_to_pdf(template_pdf, output_pdf, texts, date, font_path, "Kaiti-Bold", 16, 11)
        output_files.append(output_pdf)
    return output_files

st.title("皈依证 PDF Generator App")

uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
date = st.date_input("Select a date")
use_blank_template = st.checkbox("Use blank template (⚠️：若要打印名字在已盖章的皈依证内页，才选择这个)")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    location_column = "我要参与的地点：（请选择一个）"
    locations = df[location_column].unique().tolist()
    
    selected_location = st.selectbox("Select a location", locations)
    
    df_filtered = df[(df[location_column] == selected_location) & (df['法名'].notna())][['中文姓名 Chinese Name','法名']]
    st.write(f"Loaded {len(df_filtered)} valid entries for {selected_location}")

    if st.button("Generate PDFs"):
        template_pdf = "内页2_resized.pdf"
        font_path = "font/Kaiti-SC-Bold.ttf"  # Ensure this file is in the same directory as your script
        
        formatted_date = date.strftime("%Y年%m月%d日")
        
        output_files = generate_pdfs(df_filtered, formatted_date, template_pdf, font_path, use_blank_template)
        
        zip_filename = "generated_pdfs.zip"
        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            for file in output_files:
                zipf.write(file)
                os.remove(file)  # Remove individual PDF files after adding to zip
        
        with open(zip_filename, "rb") as f:
            bytes = f.read()
            st.download_button(
                label="Download PDFs",
                data=bytes,
                file_name=zip_filename,
                mime="application/zip"
            )
        
        os.remove(zip_filename)  # Remove the zip file after offering download
        template_type = "blank (Landscape)" if use_blank_template else "original"
        st.success(f"Generated {len(output_files)} PDFs for {selected_location} using {template_type} template. Click the button above to download.")