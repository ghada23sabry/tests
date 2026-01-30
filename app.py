import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from PIL import Image
import os

# إعداد الصفحة
st.set_page_config(page_title="مساعد المذاكرة الذكي", layout="wide")

# دعم العربية في الواجهة
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo&display=swap');
    html, body, [data-testid="stSidebar"], .stMarkdown, p, h1, h2, h3 {
        font-family: 'Cairo', sans-serif; direction: rtl; text-align: right;
    }
    .stTextArea textarea { direction: rtl; text-align: right; }
    </style>
    """, unsafe_allow_html=True)

# إعداد الموديل بحل مشكلة الـ 404
try:
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        # هنا الحل: نحدد الموديل بالمسار الكامل
        model = genai.GenerativeModel(model_name='models/gemini-1.5-flash')
    else:
        st.error("⚠️ يرجى إضافة مفتاح الـ API في Secrets")
        st.stop()
except Exception as e:
    st.error(f"خطأ في الإعداد: {e}")
    st.stop()

# قراءة الكتاب العربي
def get_pdf_text(pdf_file):
    text = ""
    reader = PdfReader(pdf_file)
    for i, page in enumerate(reader.pages):
        content = page.extract_text() or ""
        text += f"\n\n--- صفحة رقم ({i+1}) ---\n{content}\n"
    return text

st.title("📖 مساعدك الدراسي الذكي")

# إدارة ملف الكتاب
if 'book_content' not in st.session_state:
    if os.path.exists("book.pdf"):
        with st.spinner("جاري تحميل المنهج..."):
            with open("book.pdf", "rb") as f:
                st.session_state.book_content = get_pdf_text(f)
        st.success("✅ الكتاب جاهز للبحث")
    else:
        uploaded = st.file_uploader("ارفع كتاب المادة PDF", type="pdf")
        if uploaded:
            st.session_state.book_content = get_pdf_text(uploaded)
            st.success("تم الرفع بنجاح")

# طرح الأسئلة
if 'book_content' in st.session_state:
    tab1, tab2 = st.tabs(["📸 تصوير/رفع صورة", "✍️ كتابة سؤال"])
    
    q_data = None
    is_img = False

    with tab1:
        img_input = st.camera_input("صور السؤال") or st.file_uploader("رفع صورة", type=["jpg", "png"])
        if img_input:
            q_data = Image.open(img_input)
            is_img = True
    
    with tab2:
        txt_input = st.text_area("اكتب سؤالك (صح/غلط، اختر، أو سؤال عادي)")
        if st.button("حل الآن"):
            q_data = txt_input
            is_img = False

    if q_data:
        with st.spinner("جاري استخراج الإجابة من الكتاب..."):
            prompt = f"""
            أنت مساعد تعليمي دقيق. استخدم نص الكتاب المرفق فقط.
            1. حل السؤال المرفق.
            2. في 'صح وغلط': إذا كانت خطأ، اذكر التصحيح من الكتاب.
            3. اذكر رقم الصفحة (موجود في النص كـ 'صفحة رقم (X)').
            
            نص الكتاب:
            {st.session_state.book_content[:40000]}
            """
            try:
                content = [prompt, q_data] if is_img else prompt + "\nالسؤال: " + q_data
                response = model.generate_content(content)
                st.info(response.text)
            except Exception as e:
                st.error(f"حدث خطأ: {e}")