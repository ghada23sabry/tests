import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from PIL import Image
import io

# --- إعدادات الصفحة ---
st.set_page_config(page_title="المساعد الدراسي الذكي", page_icon="📖", layout="wide")

# تصميم واجهة المستخدم بلغة CSS بسيطة لتحسين المظهر على الموبايل
st.markdown("""
    <style>
    .main { text-align: right; direction: rtl; }
    .stButton>button { width: 100%; border-radius: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- إعداد الذكاء الاصطناعي ---
def setup_gemini(api_key):
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-1.5-flash')

# --- وظيفة معالجة الكتاب ---
def process_pdf(file):
    reader = PdfReader(file)
    full_text = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            full_text.append(f"--- بداية الصفحة ({i+1}) ---\n{text}\n--- نهاية الصفحة ({i+1}) ---")
    return "\n".join(full_text)

# --- واجهة التطبيق ---
st.title("📖 مساعد الامتحانات الذكي")
st.info("ارفع كتابك بصيغة PDF، ثم صور أي سؤال وسأعطيك الإجابة ورقم الصفحة.")

# الجانب الجانبي للإعدادات
with st.sidebar:
    st.header("⚙️ الإعدادات")
    api_key = st.text_input("أدخل Google API Key:", type="password")
    st.markdown("[احصل على مفتاح مجاني من هنا](https://aistudio.google.com/)")

if not api_key:
    st.warning("رجاءً أدخل مفتاح API في القائمة الجانبية للبدء.")
    st.stop()

model = setup_gemini(api_key)

# الخطوة 1: رفع الكتاب
uploaded_book = st.file_uploader("1️⃣ ارفع كتاب المادة (PDF)", type="pdf")

if uploaded_book:
    # حفظ نص الكتاب في "جلسة العمل" لسرعة الاستجابة
    if 'book_content' not in st.session_state:
        with st.spinner("جاري تحليل محتوى الكتاب... انتظر لحظة"):
            st.session_state.book_content = process_pdf(uploaded_book)
            st.success("تم حفظ الكتاب في الذاكرة!")

    st.divider()

    # الخطوة 2: تصوير السؤال
    st.subheader("2️⃣ صور السؤال (اختياري أو صح/خطأ)")
    captured_image = st.camera_input("التقط صورة للسؤال")

    if captured_image:
        img = Image.open(captured_image)
        
        with st.spinner("جاري قراءة السؤال والبحث في الكتاب..."):
            # صياغة الطلب (Prompt) بعناية لضمان الدقة
            prompt = f"""
            أنت خبير تعليمي. أمامك نص كتاب مدرسي وصورة لسؤال.
            المطلوب منك:
            1. قراءة السؤال من الصورة المرفقة.
            2. البحث عن الإجابة الصحيحة من نص الكتاب المرفق فقط.
            3. إذا كان السؤال اختيار من متعدد، حدد الاختيار الصحيح مع التبرير.
            4. إذا كان صح أو خطأ، أجب مع ذكر السبب.
            5. **هام جداً**: اذكر رقم الصفحة التي وجدت فيها الإجابة بناءً على علامات "بداية الصفحة (X)" الموجودة في النص.

            نص الكتاب المرفق:
            {st.session_state.book_content}
            """
            
            try:
                # إرسال الصورة والنص للموديل
                response = model.generate_content([prompt, img])
                
                # عرض النتيجة
                st.markdown("### ✨ الإجابة النموذجية:")
                st.success(response.text)
                
            except Exception as e:
                st.error(f"حدث خطأ أثناء التحليل: {e}")

# تذييل الصفحة
st.markdown("---")
st.caption("تم التطوير لمساعدتك في المذاكرة • استخدم الذكاء الاصطناعي بمسؤولية.")