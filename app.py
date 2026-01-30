import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from PIL import Image
import os

# --- 1. إعدادات الصفحة والـ API ---
st.set_page_config(page_title="مساعد المذاكرة", layout="wide")

# جلب الـ API Key من "Secrets" ليكون مخفياً ومحفوظاً للكل
# إذا كنتِ تشغلينه محلياً، سيبحث عنه في ملف secrets.toml
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=API_KEY)
    # استخدام الإصدار الأحدث المستقر
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("لم يتم العثور على API Key. يرجى إعداده في Streamlit Secrets.")
    st.stop()

# --- 2. وظيفة تحميل الكتاب (من الملف المرفق أو المرفوع) ---
def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for i, page in enumerate(pdf_reader.pages):
            text += f"\n--- صفحة ({i+1}) ---\n" + (page.extract_text() or "")
    return text

# --- 3. واجهة المستخدم ---
st.title("📚 مساعدك الدراسي الذكي")

# خيار حفظ الكتاب: سنحاول البحث عن ملف اسمه 'book.pdf' في ملفات المشروع أولاً
if os.path.exists("book.pdf"):
    if 'book_content' not in st.session_state:
        with st.open("book.pdf", "rb") as f:
            st.session_state.book_content = get_pdf_text([f])
    st.success("✅ تم تحميل الكتاب الأساسي (المحفوظ)")
else:
    uploaded_file = st.file_uploader("ارفع كتاب المادة (PDF) - سيتم مسحه عند تحديث الصفحة", type="pdf")
    if uploaded_file:
        st.session_state.book_content = get_pdf_text([uploaded_file])
        st.success("تم رفع الكتاب مؤقتاً.")

# --- 4. إدخال السؤال بـ 3 طرق ---
if 'book_content' in st.session_state:
    st.divider()
    st.subheader("❓ اسأل سؤالك")
    
    tab1, tab2, tab3 = st.tabs(["📸 تصوير بالكاميرا", "🖼️ رفع صورة", "✍️ كتابة نص"])
    
    input_data = None
    
    with tab1:
        cam_image = st.camera_input("التقط صورة للسؤال")
        if cam_image: input_data = Image.open(cam_image)
            
    with tab2:
        up_image = st.file_uploader("اختر صورة من الموبايل", type=["jpg", "png", "jpeg"])
        if up_image: input_data = Image.open(up_image)
            
    with tab3:
        query_text = st.text_area("اكتب سؤالك هنا...")
        if st.button("حل السؤال المكتوب"):
            input_data = query_text

    # --- 5. معالجة الإجابة ---
    if input_data:
        with st.spinner("جاري استخراج الحل من الكتاب..."):
            prompt = f"""
            أنت مساعد دراسي. استخدم نص الكتاب المرفق للإجابة على السؤال بدقة.
            اذكر الإجابة ورقم الصفحة.
            
            نص الكتاب:
            {st.session_state.book_content[:50000]} 
            """
            
            try:
                # التحقق إذا كان المدخل نصاً أو صورة
                content = [prompt, input_data] if not isinstance(input_data, str) else [prompt + "\nالسؤال: " + input_data]
                response = model.generate_content(content)
                st.markdown("### 🎯 الإجابة:")
                st.info(response.text)
            except Exception as e:
                st.error(f"حدث خطأ: {e}")