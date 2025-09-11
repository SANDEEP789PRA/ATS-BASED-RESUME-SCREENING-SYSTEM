from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import os
import io
import base64
from PIL import Image
import pdf2image
import google.generativeai as genai


genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


def get_gemini_response(prompt, pdf_content, input_text):
    try:
        model = genai.GenerativeModel(
            model_name="models/gemini-2.5-pro", 
        )
        response = model.generate_content([prompt, pdf_content[0], input_text])
        return response.text
    except Exception as e:
        return f"❌ Error generating response: {str(e)}"


def input_pdf_setup(uploaded_file):
    if uploaded_file is not None:
        images = pdf2image.convert_from_bytes(
            uploaded_file.read(),
            poppler_path=r"C:\Release-25.07.0-0\poppler-25.07.0\Library\bin"
        )
        first_page = images[0]
        img_byte_arr = io.BytesIO()
        first_page.save(img_byte_arr, format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()

        pdf_parts = [
            {
                "mime_type": "image/jpeg",
                "data": base64.b64encode(img_byte_arr).decode()
            }
        ]
        return pdf_parts
    else:
        raise FileNotFoundError("No file uploaded")



st.set_page_config(page_title="AI-Based ATS Resume Screening System")
st.header("📄 AI-Based ATS Resume Screening System")

input_text = st.text_area("📝 Job Description:", key="input")
uploaded_file = st.file_uploader("📤 Upload your resume (PDF)...", type=["pdf"])

if uploaded_file is not None:
    st.success("✅ PDF Uploaded Successfully")

submit1 = st.button("📌 Tell me about the resume")
submit2 = st.button("🚀 How can I improve my skills?")
submit3 = st.button("📊 Percentage match")

# Prompt templates
input_prompt1 = """
You are an experienced HR with technical expertise in Data Science, Full Stack Web Development, Big Data Engineering, DevOps, and Data Analytics.
Your task is to review the provided resume against the job description for these roles.
Please share the strengths and weaknesses of the applicant in relation to the specified job role.
"""

input_prompt2 = """
You are a career mentor and HR professional with expertise in Data Science, Full Stack Web Development, Big Data Engineering, DevOps, and Data Analytics hiring.
Your task is to analyze the applicant’s resume and provide personalized guidance on how they can improve their skills.
List the missing technical skills, certifications, tools, or soft skills relevant to their target job role, and suggest a roadmap to enhance their career prospects.
"""

input_prompt3 = """
You are a skilled ATS (Applicant Tracking System) and HR specialist with technical hiring expertise in Data Science, Full Stack Web Development, Big Data Engineering, DevOps, and Data Analytics.
Your task is to compare the provided resume with the given job description.
Calculate the percentage match between the resume and job description, highlight the matched and missing keywords/skills, and suggest improvements to increase the ATS match score.
"""

# Button logic
if submit1:
    if uploaded_file is not None:
        with st.spinner("🔍 Analyzing resume..."):
            pdf_content = input_pdf_setup(uploaded_file)
            response = get_gemini_response(input_prompt1, pdf_content, input_text)
            st.subheader("🧠 Analysis Result")
            st.write(response)
    else:
        st.warning("⚠️ Please upload the resume.")

elif submit2:
    if uploaded_file is not None:
        with st.spinner("🔍 Generating improvement suggestions..."):
            pdf_content = input_pdf_setup(uploaded_file)
            response = get_gemini_response(input_prompt2, pdf_content, input_text)
            st.subheader("📈 Skill Improvement Suggestions")
            st.write(response)
    else:
        st.warning("⚠️ Please upload the resume.")

elif submit3:
    if uploaded_file is not None:
        with st.spinner("🔍 Calculating match percentage..."):
            pdf_content = input_pdf_setup(uploaded_file)
            response = get_gemini_response(input_prompt3, pdf_content, input_text)
            st.subheader("📊 ATS Match Report")
            st.write(response)
    else:
        st.warning("⚠️ Please upload the resume.")
