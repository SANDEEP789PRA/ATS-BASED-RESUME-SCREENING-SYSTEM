from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import os
import io
import base64
from PIL import Image
import pdf2image
import google.generativeai as genai
from PyPDF2 import PdfReader
from docx import Document

# 🔹 Configure Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# ---------- Custom UI Styling ----------
st.set_page_config(page_title="AI-Based ATS Resume Screening System", page_icon=":rocket:", layout="centered")

st.markdown("""
<style>
body, .reportview-container, .main {
    background: url('star.jpg') repeat center center fixed;
    background-size: cover;
    color: #f5f6fa;
}
.big-title {
    font-size:2.5rem;
    color:#00aaff;
    font-weight:800;
    text-align:center;
    margin-bottom:0.2em;
    text-shadow: 0 2px 12px #0055ff44;
}
.sub-title {
    font-size:1.15rem;
    color:#b2bec3;
    text-align:center;
    margin-bottom:1.5em;
}
.tagline {
    font-size:1.08rem;
    color:#00aaff;
    font-weight:600;
    text-align:center;
    margin-bottom:2em;
}
.imp-points {
    background:rgba(44,62,80,0.13);
    border-radius:10px;
    padding:18px 18px 12px 18px;
    margin-bottom:22px;
    box-shadow:0 2px 12px #0055ff22;
}
.footer {
    width:100%;
    left:0;
    bottom:0;
    font-size:1.05em;
    color:#fff;
    font-weight:bold;
    letter-spacing:1.5px;
    background: linear-gradient(90deg,#00aaff 0%,#0055ff 100%);
    border-radius:8px;
    padding:0.6em 0 0.2em 0;
    box-shadow:0 0 18px 2px #00aaff88;
    text-shadow:0 2px 8px #0055ff88;
    text-align:center;
    margin-top:2em;
}
.imp-points ul, .imp-points li, .imp-points a, .imp-points b {
    text-decoration: none !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="big-title">AI-Based ATS Resume Screening System</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Welcome to your intelligent resume screening assistant.</div>', unsafe_allow_html=True)
st.markdown('<div class="tagline">Upload, Analyze, and Optimize your Resume in Seconds.<br>Let our AI help you land your dream job.</div>', unsafe_allow_html=True)

# ---------- Quick Tips Section ----------
st.markdown("""
<div class="imp-points">
    <h3 style="color:#00aaff;"><i class="fas fa-info-circle"></i> Quick Tips</h3>
    <ul>
        <li>Upload your resume in <b>PDF</b> format.</li>
        <li>Paste the job description for best AI matching.</li>
        <li>Click <b>Start ATS Screening</b> to begin.</li>
        <li>Allow pop-ups for the ATS tab to open.</li>
        <li>Your data is <b>secure</b> & never stored.</li>
        <li>Need help? Use the top-right contact icons on the home page.</li>
    </ul>
</div>
""", unsafe_allow_html=True)

# ---------- Company selector ----------
company = st.selectbox("🏢 Select Company Template", ["TCS", "Google", "Sistec", "Adobe"])

# ---------- Job description input ----------
input_text = st.text_area("📝 Job Description:", key="input")

# ---------- Resume upload ----------
uploaded_file = st.file_uploader("📤 Upload your resume (PDF)...", type=["pdf"])
if uploaded_file is not None:
    st.success("✅ PDF Uploaded Successfully")

# ---------- Download company-specific sample resume ----------
sample_file_map = {
    "TCS": "TCS_sample_resume.docx",
    "Google": "Google_sample_resume.docx",
    "Sistec": "Sistec_sample_resume.pdf",
    "Adobe": "Adode_sample_resume.docx"
}
sample_path = os.path.join("templates", "samples", sample_file_map[company])
if os.path.exists(sample_path):
    with open(sample_path, "rb") as f:
        st.download_button(f"📥 Download {company} Sample Resume", f, file_name=sample_file_map[company])
else:
    st.warning(f"⚠️ Sample resume for {company} not found.")

# ---------- Load prompt template based on company ----------
prompt_file_map = {
    "TCS": "TCS_templates.docx",
    "Google": "Google_templates.docx",
    "Sistec": "Sistec_templates.pdf",
    "Adobe": "Adode_templates.docx"
}
def load_prompt_template(filename):
    try:
        ext = os.path.splitext(filename)[1].lower()
        path = os.path.join("templates", "prompts", filename)
        if ext == ".pdf":
            reader = PdfReader(path)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
            return text.strip()
        elif ext == ".docx":
            doc = Document(path)
            text = "\n".join([para.text for para in doc.paragraphs])
            return text.strip()
        else:
            return f"❌ Unsupported file type: {ext}"
    except Exception as e:
        return f"❌ Error loading template: {str(e)}"
selected_prompt = load_prompt_template(prompt_file_map[company])

# ---------- Gemini response handler ----------
def get_gemini_response(prompt, pdf_content, input_text):
    try:
        model = genai.GenerativeModel(model_name="models/gemini-2.5-pro")
        # For reformatting, just pass the prompt if pdf_content is empty
        if pdf_content:
            response = model.generate_content([prompt, pdf_content[0], input_text])
        else:
            response = model.generate_content([prompt])
        return response.text
    except Exception as e:
        return f"❌ Error generating response: {str(e)}"

# ---------- Convert uploaded PDF to image ----------
def input_pdf_setup(uploaded_file):
    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        images = pdf2image.convert_from_bytes(
            file_bytes,
            poppler_path=r"C:\Release-25.07.0-0\poppler-25.07.0\Library\bin"
        )
        if not images:
            raise ValueError("❌ No pages found in PDF.")
        first_page = images[0]
        img_byte_arr = io.BytesIO()
        first_page.save(img_byte_arr, format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()
        pdf_parts = [{
            "mime_type": "image/jpeg",
            "data": base64.b64encode(img_byte_arr).decode()
        }]
        return pdf_parts, file_bytes
    else:
        raise FileNotFoundError("No file uploaded")

# ---------- Extract full resume text from PDF ----------
def extract_resume_text(file_bytes):
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
        if not text.strip():
            return "❌ No readable text found in the PDF. It may be scanned or image-based."
        return text.strip()
    except Exception as e:
        return f"❌ Error extracting resume text: {str(e)}"

# ---------- Button actions ----------
col1, col2, col3, col4 = st.columns(4)
with col1:
    submit1 = st.button("📌 Tell me about the resume")
with col2:
    submit2 = st.button("🚀 How can I improve my skills?")
with col3:
    submit3 = st.button("📊 Percentage match")
with col4:
    submit4 = st.button("🧾 Convert Resume to Selected Format")

if submit1:
    if uploaded_file is not None:
        with st.spinner(f"🔍 Analyzing resume using {company} template..."):
            pdf_content, _ = input_pdf_setup(uploaded_file)
            response = get_gemini_response(selected_prompt, pdf_content, input_text)
            st.subheader("🧠 Analysis Result")
            st.write(response)
    else:
        st.warning("⚠️ Please upload the resume.")

elif submit2:
    if uploaded_file is not None:
        with st.spinner(f"🔍 Generating skill suggestions using {company} template..."):
            pdf_content, _ = input_pdf_setup(uploaded_file)
            response = get_gemini_response(selected_prompt, pdf_content, input_text)
            st.subheader("📈 Skill Improvement Suggestions")
            st.write(response)
    else:
        st.warning("⚠️ Please upload the resume.")

elif submit3:
    if uploaded_file is not None:
        with st.spinner(f"🔍 Calculating ATS match using {company} template..."):
            pdf_content, _ = input_pdf_setup(uploaded_file)
            response = get_gemini_response(selected_prompt, pdf_content, input_text)
            st.subheader("📊 ATS Match Report")
            st.write(response)
    else:
        st.warning("⚠️ Please upload the resume.")

elif submit4:
    if uploaded_file is not None:
        with st.spinner(f"🔄 Converting resume to {company} format..."):
            pdf_content, file_bytes = input_pdf_setup(uploaded_file)
            resume_text = extract_resume_text(file_bytes)
            if "❌" in resume_text or not resume_text:
                st.error("❌ Resume text could not be extracted. Please upload a text-based PDF.")
            else:
                reformat_prompt = f"""
                You are a professional resume formatter.

                Task:
                Reformat the resume below into the style used by {company}. Use clean headings, bullet points, and ATS-friendly layout. Keep it professional and tailored to the job description.

                Job Description:
                {input_text}

                Resume:
                {resume_text}
                """
                # Only pass the prompt for reformatting
                formatted_resume = get_gemini_response(reformat_prompt, pdf_content=None, input_text=None)
                st.subheader("📄 Reformatted Resume")
                st.text_area("✂️ AI-Generated Resume in Company Format", value=formatted_resume, height=400)
                st.download_button("📥 Download Reformatted Resume", formatted_resume.encode(), file_name=f"{company}_formatted_resume.txt")
    else:
        st.warning("⚠️ Please upload your resume first.")

# ---------- Footer ----------
st.markdown('<div class="footer">Powered by SANDEEP &mdash; Your career, upgraded.</div>', unsafe_allow_html=True)