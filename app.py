import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from PIL import Image
import os

# --- 1. إعدادات الصفحة ودعم اللغة العربية ---
st.set_page_config(page_title="مساعد المذاكرة الذكي", layout="wide")

# تنسيق الواجهة لتدعم RTL (من اليمين لليسار) والخطوط العربية
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo&display=swap');
    html, body, [data-testid="stSidebar"], .stMarkdown, p, h1, h2, h3, div {
        font-family: 'Cairo', sans-serif;
        direction: rtl;
        text-align: right;
    }
    .stTextArea textarea { direction: rtl; text-align: right; }
    .stButton>button { width: 100%; border-radius: 10px; background-color: #4CAF50; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إعداد الذكاء الاصطناعي (API Key) ---
try:
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
        # استخدام المسار الكامل للموديل لتجنب خطأ 404
        model = genai.GenerativeModel(model_name='models/gemini-1.5-flash')
    else:
        st.error("⚠️ لم يتم العثور على مفتاح API في الإعدادات (Secrets). يرجى إضافته باسم GOOGLE_API_KEY")
        st.stop()
except Exception as e:
    st.error(f"خطأ في إعداد API: {e}")
    st.stop()

# --- 3. وظيفة استخراج النص العربي من الكتاب ---
def get_pdf_content(pdf_file):
    text_content = ""
    try:
        reader = PdfReader(pdf_file)
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            # إضافة علامات صفحات واضحة للبحث
            text_content += f"\n\n--- رقم الصفحة الأساسي: ({i+1}) ---\n{page_text}\n"
        return text_content
    except Exception as e:
        st.error(f"خطأ في قراءة الـ PDF: {e}")
        return ""

# --- 4. إدارة محتوى الكتاب (حفظ دائم) ---
st.title("📚 مساعدك الدراسي الذكي")
st.write("حل الأسئلة، تصحيح الإجابات، وتحديد مكان المعلومة في الكتاب.")

if 'book_data' not in st.session_state:
    # محاولة البحث عن الكتاب المرفوع مسبقاً على GitHub
    if os.path.exists("book.pdf"):
        with st.spinner("جاري تحميل الكتاب المحفوظ (book.pdf)..."):
            with open("book.pdf", "rb") as f:
                st.session_state.book_data = get_pdf_content(f)
        st.success("✅ تم تحميل الكتاب المرجعي بنجاح.")
    else:
        st.info("💡 ارفعي ملف باسم 'book.pdf' على GitHub ليكون متاحاً دائماً.")
        uploaded_file = st.file_uploader("أو ارفعي الكتاب الآن يدوياً", type="pdf")
        if uploaded_file:
            st.session_state.book_data = get_pdf_content(uploaded_file)
            st.success("تم تحليل الكتاب المرفوع!")

# --- 5. واجهة طرح الأسئلة (3 طرق) ---
if 'book_data' in st.session_state:
    st.divider()
    st.subheader("📝 اسأل سؤالك")
    
    tabs = st.tabs(["📸 تصوير بالكاميرا", "🖼️ رفع صورة", "✍️ كتابة سؤال"])
    
    query_payload = None
    is_visual = False

    with tabs[0]:
        cam_img = st.camera_input("التقط صورة واضحة للسؤال من كتابك")
        if cam_img:
            query_payload = Image.open(cam_img)
            is_visual = True

    with tabs[1]:
        up_img = st.file_uploader("اختر صورة السؤال من الموبايل", type=["jpg", "png", "jpeg"])
        if up_img:
            query_payload = Image.open(up_img)
            is_visual = True

    with tabs[2]:
        txt_query = st.text_area("اكتب سؤالك هنا (مثال: هل العبارة كذا صحيحة؟ أو اكتب السؤال ليتم حله)")
        if st.button("حل السؤال المكتوب"):
            if txt_query:
                query_payload = txt_query
                is_visual = False

    # --- 6. المعالجة والرد النهائي ---
    if query_payload:
        with st.spinner("جاري فحص المنهج واستخراج الإجابة..."):
            # تعليمات صارمة للموديل لضمان الدقة المطلوبة
            prompt_instructions = f"""
            أنت مساعد تعليمي متخصص في المناهج العربية. استخدم النص المرفق من الكتاب فقط للإجابة.
            
            مهمتك كالتالي:
            1. إذا كان السؤال (صح أو خطأ): حدد هل العبارة صحيحة أم خاطئة. إذا كانت خاطئة، يجب أن تصححها بناءً على الكتاب.
            2. إذا كان السؤال (اختياري): حدد الاختيار الصحيح مع شرح بسيط للسبب.
            3. إذا كان سؤالاً مقالياً: أجب عليه بدقة واختصار.
            4. **شرط إلزامي**: ابحث عن رقم الصفحة التي وردت فيها المعلومة واذكره بوضوح (مثال: 'موجود في الصفحة رقم 12'). استخدم علامات 'رقم الصفحة الأساسي: (X)' الموجودة في النص لتحديدها.
            
            محتوى الكتاب المدرسي:
            {st.session_state.book_data[:45000]}
            """
            
            try:
                if is_visual:
                    # إرسال الصورة مع التعليمات
                    response = model.generate_content([prompt_instructions, query_payload])
                else:
                    # إرسال النص مع التعليمات
                    response = model.generate_content(prompt_instructions + "\n\nالسؤال المطلوب حله هو: " + query_payload)
                
                st.markdown("### 🎯 الإجابة النموذجية:")
                st.info(response.text)
            except Exception as e:
                st.error(f"حدث خطأ أثناء المعالجة: {e}")