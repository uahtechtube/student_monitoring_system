import os
import sys

# Try to find which PDF libraries are available
libs = ['pypdf', 'PyPDF2', 'pdfplumber', 'fitz', 'pdfminer']
available = []
for lib in libs:
    try:
        __import__(lib)
        available.append(lib)
    except ImportError:
        pass

print(f"Available libraries: {available}")

# Let's see if we have MyProject.pdf or Student.pdf
pdf_path = "MyProject.pdf"
if not os.path.exists(pdf_path):
    pdf_path = "Student.pdf"
    print(f"MyProject.pdf not found, checking Student.pdf instead. Exists: {os.path.exists(pdf_path)}")
else:
    print("MyProject.pdf found.")

if os.path.exists(pdf_path):
    print(f"File size: {os.path.getsize(pdf_path)} bytes")
    
    # Try using pypdf if available
    if 'pypdf' in available:
        import pypdf
        reader = pypdf.PdfReader(pdf_path)
        print(f"Number of pages: {len(reader.pages)}")
        # Print first page text
        text = reader.pages[0].extract_text()
        print("--- Page 1 Text ---")
        print(text[:1000])
    elif 'PyPDF2' in available:
        import PyPDF2
        reader = PyPDF2.PdfReader(pdf_path)
        print(f"Number of pages: {len(reader.pages)}")
        text = reader.pages[0].extract_text()
        print("--- Page 1 Text ---")
        print(text[:1000])
    elif 'pdfplumber' in available:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            print(f"Number of pages: {len(pdf.pages)}")
            text = pdf.pages[0].extract_text()
            print("--- Page 1 Text ---")
            print(text[:1000])
    else:
        print("No standard PDF library found.")
else:
    print("No PDF files found.")
