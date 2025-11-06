import streamlit as st
import PyPDF2
import fitz
import io
import google.generativeai as genai

try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except Exception as e:
    st.error("API key error!.")
    st.stop()

# --- KROK 2: Interfejs użytkownika ---
st.set_page_config(layout="wide")
st.title("🤖 AI PDF note maker")

uploaded_files = st.file_uploader(
    "Choose PDF files...",
    type="pdf",
    accept_multiple_files=True
)

if uploaded_files:
    st.success(f"Loaded {len(uploaded_files)} files. Click generate to proceed.")

    if st.button("Generate 🚀"):

        with st.spinner("1/3: Merging files..."):
            merger = PyPDF2.PdfMerger()
            for pdf_file in uploaded_files:
                merger.append(io.BytesIO(pdf_file.getvalue()))

            merged_pdf_bytes = io.BytesIO()
            merger.write(merged_pdf_bytes)
            merger.close()

        with st.spinner("2/3. Extracting text..."):
            merged_pdf_document = fitz.open(stream=merged_pdf_bytes.getvalue(), filetype="pdf")
            text = ""
            for page_num in range(len(merged_pdf_document)):
                page = merged_pdf_document.load_page(page_num)
                text += page.get_text()

            merged_pdf_document.close()
            st.session_state['text'] = text

        with st.spinner("3/3. AI analize text..."):
            try:
                model = genai.GenerativeModel('gemini-flash-latest')

                prompt = """
                                    Jesteś ekspertem akademickim i asystentem nauki. 
                                    Twoim zadaniem jest przeanalizowanie poniższego tekstu, który pochodzi z połączonych 
                                    prezentacji na studia. Wyciągnij z niego ABSOLUTNIE najważniejsze 
                                    pojęcia, definicje, kluczowe daty i teorie. 

                                    Zasady:
                                    1. Skup się tylko na kluczowych informacjach potrzebnych do egzaminu.
                                    2. Pomiń informacje poboczne, przykłady i "wypełniacze".
                                    3. Sformatuj odpowiedź używając Markdown.
                                    4. Użyj nagłówków (##) dla głównych tematów i list wypunktowanych (*) dla pojęć.

                                    Oto tekst z prezentacji:
                                    """

                tekst_z_pdf = st.session_state.get('text', 'blank')

                if len(tekst_z_pdf) > 100:
                    pelny_prompt = prompt + "\n\n" + tekst_z_pdf
                    response = model.generate_content(pelny_prompt)

                    if response.parts:
                        result_ai = response.text
                        st.session_state['result_ai'] = result_ai
                        st.success("Ready!")
                    else:
                        st.error(
                            "AI generating error.")

                else:
                    st.error("AI need more text!")

            except Exception as e:
                st.error(f"AI communication error: {e}")

if 'result_ai' in st.session_state:
    st.markdown("---")
    st.subheader("🤖 AI generated notes:")
    st.markdown(st.session_state['result_ai'])