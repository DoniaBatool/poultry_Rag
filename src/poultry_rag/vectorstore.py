import os
import pdfplumber
import pandas as pd
from pdf2image import convert_from_path
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.schema import Document


def load_documents():
    """Load the stored vector database."""
    return Chroma(persist_directory="db", embedding_function=HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2"))

# Extract text and tables from PDF
def extract_text_and_tables_from_pdf(pdf_path):
    text = ""
    tables = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # ✅ Extract text
            text += page.extract_text() or ""  

            # ✅ Extract tables
            extracted_tables = page.extract_tables()
            for table in extracted_tables:
                df = pd.DataFrame(table[1:], columns=table[0])  # Convert to DataFrame
                tables.append(df.to_dict())  # Convert to dictionary for storage

    return text.strip(), tables

# Convert PDF pages to images
def save_pdf_as_images(pdf_path, output_folder="extracted_pages"):
    os.makedirs(output_folder, exist_ok=True)
    images = convert_from_path(pdf_path, dpi=400)  # High-quality images
    image_paths = []

    for idx, img in enumerate(images):
        img_path = os.path.join(output_folder, f"{os.path.basename(pdf_path)}_page{idx+1}.png")
        img.save(img_path, "PNG")
        image_paths.append(img_path)

    return image_paths

# Store extracted text, tables, and images in vector database
def store_pdf_in_vector_db(pdf_path):
    text, tables = extract_text_and_tables_from_pdf(pdf_path)
    saved_images = save_pdf_as_images(pdf_path)

    docs = []

    # ✅ Store extracted text
    if text:
        docs.append(Document(page_content=text, metadata={"type": "text", "source": os.path.basename(pdf_path)}))

    # ✅ Store extracted tables
    if tables:
       for i, table in enumerate(tables):
          table_text = "\n".join([", ".join(row) for row in table])  # Convert table to readable text
          docs.append(Document(page_content=table_text, metadata={"type": "table", "source": os.path.basename(pdf_path), "table_index": i}))
    # ✅ Store extracted images
    for img_path in saved_images:
        docs.append(Document(page_content="", metadata={"type": "image", "source": img_path}))

    # Store everything in ChromaDB
    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = Chroma.from_documents(docs, embedding_model, persist_directory="db")

    print("✅ PDF text, tables, and images stored in ChromaDB")
    return vectorstore  
