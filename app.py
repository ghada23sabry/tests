import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from PIL import Image
import os

# --- 1. إعدادات الصفحة (استخدام الفاصلة الإنجليزية الكود بالكامل إنجليزي) ---
st.set_page_config(page_title="مساعد المذاكرة الذكي", layout="wide")

# تحسين مظهر الواجهة
st.markdown("""
    <style>
    .main { text-align: right; direction: rtl; }
    div[data-testid="stExpander"] div { text-align: right; direction: rtl; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إعداد الذكاء الاصطناعي (API Key) ---
# سيتم جلب المفتاح من Secrets في Streamlit Cloud
try:
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        api_key = None
        
    if api_key:
        genai.configure(api_key=api_key)
        # استخدام موديل Gemini 1.5 Flash الأسرع والأفضل للصور
        model = genai.GenerativeModel('gemini-1.5-flash')
    else:
        st.warning("⚠️ لم يتم العثور على مفتاح API في الإعدادات (Secrets).")
        st.stop()
except Exception as e:
    st.error(f"خطأ في إعداد API: {e}")
    st.stop()

# --- 3. وظيفة معالجة الـ PDF واستخراج النص ---
def get_pdf_text(pdf_file):
    text = ""
    try:
        pdf_reader = PdfReader(pdf_file)
        for i, page in enumerate(pdf_reader.pages):
            page_content = page.extract_text() or ""
            # إضافة رقم الصفحة بوضوح ليراه الذكاء الاصطناعي
            text += f"\n\n--- رقم الصفحة: ({i+1}) ---\n{page_content}\n"
        return text
    except Exception as e:
        st.error(f"خطأ في قراءة ملف PDF: {e}")
        return ""

# --- 4. إدارة تحميل الكتاب (تلقائي أو يدوي) ---
st.title("📖 مساعد المادة الذكي")

# محاولة تحميل الكتاب الدائم من السيرفر (GitHub)
if 'book_content' not in st.session_state:
    if os.path.exists("book.pdf"):
        with st.spinner("جاري قراءة الكتاب المحفوظ (book.pdf)..."):
            with open("book.pdf", "rb") as f:
                st.session_state.book_content = get_pdf_text(f)
        st.success("✅ تم تحميل الكتاب الأساسي بنجاح.")
    else:
        st.info("💡 لم يتم العثور على ملف 'book.pdf'. يمكنك رفعه الآن.")
        uploaded_file = st.file_uploader("ارفع ملف الكتاب (PDF)", type="pdf")
        if uploaded_file:
            st.session_state.book_content = get_pdf_text(uploaded_file)
            st.success("تم رفع ومعالجة الكتاب بنجاح!")

# --- 5. واجهة طرح الأسئلة ---
if 'book_content' in st.session_state:
    st.divider()
    st.subheader("❓ اسأل عن أي شيء في الكتاب")
    
    # تبويبات لخيارات الإدخال المختلفة
    tab1, tab2, tab3 = st.tabs(["📸 تصوير سؤال", "🖼️ رفع صورة", "✍️ سؤال نصي"])
    
    user_input = None
    input_type = None

    with tab1:
        cam_img = st.camera_input("التقط صورة واضحة للسؤال")
        if cam_img:
            user_input = Image.open(cam_img)
            input_type = "image"

    with tab2:
        up_img = st.file_uploader("اختر صورة من استوديو الموبايل", type=["jpg", "png", "jpeg"])
        if up_img:
            user_input = Image.open(up_img)
            input_type = "image"

    with tab3:
        txt_query = st.text_area("اكتب سؤالك هنا بالتفصيل...")
        if st.button("إرسال السؤال النصي"):
            if txt_query:
                user_input = txt_query
                input_type = "text"

    # --- 6. معالجة الإجابة باستخدام Gemini ---
    if user_input:
        with st.spinner("جاري البحث عن الحل في الكتاب..."):
            # تجهيز التعليمات (Prompt)
            prompt = f"""
            بناءً على نص الكتاب المرفق أدناه فقط، أجب على السؤال التالي بدقة. 
            إذا كان السؤال في الصورة، فقم بتحليل الصورة أولاً.
            بعد الإجابة، اذكر بوضوح رقم الصفحة التي وجدت فيها الحل.
            
            نص الكتاب المتاح:
            {st.session_state.book_content[:40000]} 
            """
            
            try:
                if input_type == "image":
                    response = model.generate_content([prompt, user_input])
                else:
                    response = model.generate_content(prompt + "\n\nالسؤال هو: " + user_input)
                
                st.markdown("### ✨ الإجابة ورقم الصفحة:")
                st.info(response.text)
            except Exception as e:
                st.error(f"حدث خطأ أثناء التواصل مع الذكاء الاصطناعي: {e}")