
import streamlit as st
import io
import os
from datetime import datetime
import openai

# Try to import document processing libraries
try:
    from PyPDF2 import PdfReader
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="Document Insights Generator",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1F77B4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #555;
        text-align: center;
        margin-bottom: 2rem;
    }
    .insight-box {
        background-color: #f0f7ff;
        border-left: 5px solid #1F77B4;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border-left: 5px solid #28a745;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">📄 Document Insights Generator</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Upload documents, ask questions, get AI-powered insights</div>', unsafe_allow_html=True)

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Configuration")

    # OpenAI API Key input
    openai_api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        help="Get your API key from https://platform.openai.com/api-keys"
    )

    st.markdown("---")

    # Instructions
    st.markdown("### 📖 How to Use")
    st.markdown("""
    1. Enter your OpenAI API key above
    2. Upload your document (PDF, DOCX, TXT)
    3. Ask a question about the document
    4. Click 'Generate Insights'
    5. View and download your results
    """)

    st.markdown("---")

    # Model selection
    model = st.selectbox(
        "AI Model",
        ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
        help="GPT-3.5 is faster and cheaper. GPT-4 is more accurate but slower."
    )

    # Temperature setting
    temperature = st.slider(
        "Creativity Level",
        min_value=0.0,
        max_value=1.0,
        value=0.3,
        step=0.1,
        help="Lower = more focused, Higher = more creative"
    )

    st.markdown("---")

    # Links
    st.markdown("### 🔗 Useful Links")
    st.markdown("[Get OpenAI API Key](https://platform.openai.com/api-keys)")
    st.markdown("[Check API Usage](https://platform.openai.com/usage)")
    st.markdown("[GitHub Repository](https://github.com)")

# Helper Functions
def extract_text_from_pdf(file_bytes):
    """Extract text from PDF file"""
    try:
        if not PDF_AVAILABLE:
            return "PDF support not available. Please install PyPDF2."

        pdf_reader = PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        return f"Error extracting PDF: {str(e)}"

def extract_text_from_docx(file_bytes):
    """Extract text from DOCX file"""
    try:
        if not DOCX_AVAILABLE:
            return "DOCX support not available. Please install python-docx."

        doc = DocxDocument(io.BytesIO(file_bytes))
        text = "\n".join([para.text for para in doc.paragraphs])
        return text.strip()
    except Exception as e:
        return f"Error extracting DOCX: {str(e)}"

def extract_text_from_txt(file_bytes):
    """Extract text from TXT file"""
    try:
        return file_bytes.decode('utf-8', errors='ignore').strip()
    except Exception as e:
        return f"Error extracting TXT: {str(e)}"

def extract_text(uploaded_file):
    """Extract text based on file type"""
    file_bytes = uploaded_file.read()
    file_type = uploaded_file.type

    if file_type == "application/pdf" or uploaded_file.name.endswith('.pdf'):
        return extract_text_from_pdf(file_bytes)
    elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" or uploaded_file.name.endswith('.docx'):
        return extract_text_from_docx(file_bytes)
    elif file_type == "text/plain" or uploaded_file.name.endswith('.txt'):
        return extract_text_from_txt(file_bytes)
    else:
        return "Unsupported file format. Please upload PDF, DOCX, or TXT files."

def generate_insights(document_text, question, api_key, model_name, temp):
    """Generate insights using OpenAI API"""
    try:
        # Set API key
        openai.api_key = api_key

        # Truncate if too long (to stay within token limits)
        max_chars = 12000
        if len(document_text) > max_chars:
            document_text = document_text[:max_chars] + "\n\n[Document truncated for processing...]"

        # Create prompt
        prompt = f"""You are a helpful AI assistant that analyzes documents and provides clear, detailed insights.

Read the following document carefully and answer this question: {question}

Document:
{document_text}

Please provide a comprehensive answer based only on the information in the document. If the document doesn't contain enough information to answer the question, say so clearly."""

        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that provides clear, detailed document analysis."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=temp
        )

        return response.choices[0].message.content

    except openai.error.AuthenticationError:
        return "❌ Invalid API key. Please check your OpenAI API key and try again."
    except openai.error.RateLimitError:
        return "❌ Rate limit exceeded. Please check your API quota or try again later."
    except openai.error.InvalidRequestError as e:
        return f"❌ Invalid request: {str(e)}"
    except Exception as e:
        return f"❌ Error generating insights: {str(e)}"

# Initialize session state
if 'document_text' not in st.session_state:
    st.session_state.document_text = None
if 'insights' not in st.session_state:
    st.session_state.insights = None
if 'filename' not in st.session_state:
    st.session_state.filename = None

# Main content area
st.markdown("## 📤 Upload Your Document")

# File uploader
uploaded_file = st.file_uploader(
    "Choose a file",
    type=['pdf', 'docx', 'txt'],
    help="Upload PDF, Word, or Text files (max 200MB)"
)

if uploaded_file:
    st.success(f"✅ File uploaded: {uploaded_file.name} ({uploaded_file.size / 1024:.2f} KB)")
    st.session_state.filename = uploaded_file.name

    # Extract text button
    if st.button("📖 Extract Text from Document"):
        with st.spinner("Extracting text..."):
            document_text = extract_text(uploaded_file)
            st.session_state.document_text = document_text

            if document_text and not document_text.startswith("Error") and not document_text.startswith("Unsupported"):
                st.success(f"✅ Text extracted successfully! ({len(document_text)} characters)")

                # Show preview
                with st.expander("📄 Preview Extracted Text (first 1000 characters)"):
                    preview_text = document_text[:1000]
                    st.text(preview_text + ("..." if len(document_text) > 1000 else ""))
            else:
                st.error(document_text)

# Question input
if st.session_state.document_text:
    st.markdown("---")
    st.markdown("## ❓ Ask Your Question")

    # Example questions
    with st.expander("💡 Example Questions"):
        st.markdown("""
        - What are the main points in this document?
        - Summarize the key findings
        - What risks are mentioned in the document?
        - List all recommendations
        - What is the conclusion of this document?
        - Identify the main challenges discussed
        """)

    question = st.text_area(
        "Type your question here:",
        height=100,
        placeholder="e.g., What are the main findings in this document?"
    )

    # Generate insights button
    if st.button("🤖 Generate Insights", type="primary"):
        if not openai_api_key:
            st.error("⚠️ Please enter your OpenAI API key in the sidebar.")
        elif not question:
            st.error("⚠️ Please enter a question.")
        else:
            with st.spinner("🤖 AI is analyzing your document... This may take 10-30 seconds."):
                insights = generate_insights(
                    st.session_state.document_text,
                    question,
                    openai_api_key,
                    model,
                    temperature
                )
                st.session_state.insights = insights
                st.session_state.question = question

# Display insights
if st.session_state.insights:
    st.markdown("---")
    st.markdown("## 🎯 Insights")

    # Display in a nice box
    st.markdown(f'<div class="insight-box">{st.session_state.insights}</div>', unsafe_allow_html=True)

    # Download options
    st.markdown("### 💾 Download Results")

    col1, col2 = st.columns(2)

    with col1:
        # Create downloadable text file
        result_text = f"""Document: {st.session_state.filename}
Question: {st.session_state.question}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{'='*80}

INSIGHTS:

{st.session_state.insights}

{'='*80}

Document Text (excerpt):
{st.session_state.document_text[:2000]}...
"""

        st.download_button(
            label="📄 Download as TXT",
            data=result_text,
            file_name=f"{st.session_state.filename}_insights.txt",
            mime="text/plain"
        )

    with col2:
        # Create markdown version
        markdown_text = f"""# Document Insights

**Document:** {st.session_state.filename}  
**Question:** {st.session_state.question}  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## Insights

{st.session_state.insights}

---

*Generated by Document Insights Generator*
"""

        st.download_button(
            label="📝 Download as MD",
            data=markdown_text,
            file_name=f"{st.session_state.filename}_insights.md",
            mime="text/markdown"
        )

    # Option to analyze again
    if st.button("🔄 Analyze Another Document"):
        st.session_state.document_text = None
        st.session_state.insights = None
        st.session_state.filename = None
        st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem 0;'>
    <p>Built with ❤️ using Streamlit and OpenAI</p>
    <p>No data is stored - everything happens in your browser session</p>
</div>
""", unsafe_allow_html=True)
