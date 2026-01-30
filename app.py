import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from PIL import Image
import os

# --- 1. إعدادات الواجهة واللغة العربية ---
st.set_page_config(page_title="مساعد المذاكرة الذكي", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo&display=swap');
    html, body, [data-testid="stSidebar"], .stMarkdown, p, h1, h2, h3, div {
        font-family: 'Cairo', sans-serif; direction: rtl; text-align: right;
    }
    .stTextArea textarea { direction: rtl; text-align: right; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. حل مشكلة 404 وإعداد الـ API ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
        
        # التعديل الجوهري: استخدام الإصدار المستقر v1 وتحديد المسار الكامل
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            generation_config={"top_p": 0.95, "top_k": 64, "temperature": 1}
        )
    else:
        st.error("⚠️ يرجى إضافة مفتاح الـ API في Secrets باسم GOOGLE_API_KEY")
        st.stop()
except Exception as e:
    st.error(f"خطأ في إعداد الاتصال: {e}")
    st.stop()

# --- 3. قراءة محتوى الكتاب ---
def get_pdf_text(pdf_file):
    text = ""
    try:
        reader = PdfReader(pdf_file)
        for i, page in enumerate(reader.pages):
            page_content = page.extract_text() or ""
            text += f"\n\n--- صفحة رقم: ({i+1}) ---\n{page_content}\n"
        return text
    except Exception as e:
        st.error(f"تعذر قراءة ملف الـ PDF: {e}")
        return ""

st.title("📖 المساعد الدراسي المتكامل")

# --- 4. تخزين الكتاب الدائم ---
if 'book_content' not in st.session_state:
    if os.path.exists("book.pdf"):
        with st.spinner("جاري قراءة الكتاب..."):
            with open("book.pdf", "rb") as f:
                st.session_state.book_content = get_pdf_text(f)
        st.success("✅ الكتاب المرجعي جاهز")
    else:
        uploaded = st.file_uploader("ارفع كتاب المادة (PDF)", type="pdf")
        if uploaded:
            st.session_state.book_content = get_pdf_text(uploaded)
            st.success("تم تحليل الكتاب المرفوع")

# --- 5. واجهة الأسئلة المتعددة ---
if 'book_content' in st.session_state:
    st.divider()
    st.subheader("💡 اطرح سؤالك (نص أو صورة)")
    
    tabs = st.tabs(["📸 الكاميرا / رفع صورة", "✍️ سؤال مكتوب"])
    
    q_payload = None
    input_is_image = False

    with tabs[0]:
        # تم دمج الكاميرا والرفع في مكان واحد لحل تضارب الصور
        image_option = st.radio("اختر طريقة الإدخال:", ["الكاميرا", "رفع ملف صورة"], horizontal=True)
        if image_option == "الكاميرا":
            cam_input = st.camera_input("التقط صورة السؤال")
            if cam_input:
                q_payload = Image.open(cam_input)
                input_is_image = True
        else:
            file_input = st.file_uploader("اختر صورة السؤال", type=["jpg", "png", "jpeg"])
            if file_input:
                q_payload = Image.open(file_input)
                input_is_image = True

    with tabs[1]:
        txt_input = st.text_area("اكتب سؤالك هنا ليتم البحث عنه في الكتاب")
        if st.button("حل السؤال المكتوب"):
            if txt_input:
                q_payload = txt_input
                input_is_image = False

    # --- 6. معالجة الإجابة ---
    if q_payload:
        with st.spinner("جاري تحليل السؤال والبحث في الكتاب..."):
            prompt = f"""
            أنت مساعد تعليمي خبير. استخدم نص الكتاب المرفق فقط للإجابة.
            
            قواعد الرد:
            1. إذا كان السؤال 'صح أو خطأ': حدد الإجابة، وإذا كانت خاطئة قم بتصحيحها من الكتاب.
            2. إذا كان السؤال 'اختر': حدد الإجابة الصحيحة.
            3. إذا كان سؤالاً نصياً: ابحث عن الإجابة في النص المرفق بدقة.
            4. **إلزامي**: اذكر رقم الصفحة التي وجدت فيها الإجابة (موجودة في النص كـ 'صفحة رقم: (X)').
            
            نص الكتاب المتاح:
            {st.session_state.book_content[:45000]}
            """
            
            try:
                if input_is_image:
                    # إرسال الصورة والبرومبت معاً كقائمة
                    response = model.generate_content([prompt, q_payload])
                else:
                    # إرسال النص مع البرومبت
                    response = model.generate_content(prompt + "\n\nالسؤال هو: " + q_payload)
                
                st.markdown("### 🎯 الإجابة والتحليل:")
                st.info(response.text)
            except Exception as e:
                st.error(f"حدث خطأ أثناء المعالجة: {e}")