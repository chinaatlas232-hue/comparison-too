import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="مقارن ملفات الإكسل الذكي", page_icon="📊", layout="wide"
)

# زر المسح اليدوي في القائمة الجانبية
with st.sidebar:
  st.markdown("### ⚙️ إعدادات التحكم")
  if st.button("🗑️ مسح الملفات وإعادة ضبط التطبيق", use_container_width=True):
    for key in list(st.session_state.keys()):
      del st.session_state[key]
    st.rerun()

st.markdown(
    """
    <h2 style='text-align: center; color: #4F46E5;'>📊 أداة مقارنة الأكواد البسيطة</h2>
    """,
    unsafe_allow_html=True,
)

col1, col2 = st.columns(2)
with col1:
    uploaded_main = st.file_uploader(
        "📁 ارفع الملف الرئيسي (Master File)", type=["xlsx", "xls"]
    )
with col2:
    uploaded_new = st.file_uploader(
        "📁 ارفع الملف المراد مقارنته (New File)", type=["xlsx", "xls"]
    )


@st.cache_data
def load_data(file1, file2):
  df1 = pd.read_excel(file1, sheet_name=0)
  df2 = pd.read_excel(file2, sheet_name=0)
  df1.columns = df1.columns.str.strip()
  df2.columns = df2.columns.str.strip()
  return df1, df2


if uploaded_main and uploaded_new:
  try:
    df_main, df_new = load_data(uploaded_main, uploaded_new)

    st.markdown("---")

    # استخراج الأعمدة المشتركة واختيار عمود الكود
    common_cols = list(set(df_main.columns).intersection(set(df_new.columns)))
    default_id_idx = common_cols.index("الكود") if "الكود" in common_cols else 0

    id_col = st.selectbox(
        "🔑 اختر عمود الكود المشترك حصراً:", common_cols, index=default_id_idx
    )

    if st.button("🚀 ابدأ المقارنة وعرض المربعات", use_container_width=True):
      def clean_series(series):
        return (
            series.astype(str)
            .str.replace(r"\.0$", "", regex=True)
            .str.strip()
            .fillna("")
            .replace("nan", "")
        )

      main_ids = set(clean_series(df_main[id_col]))
      new_ids = set(clean_series(df_new[id_col]))

      main_ids.discard("")
      new_ids.discard("")

      count_main = len(main_ids)
      count_new = len(new_ids)
      diff_count = len(main_ids.symmetric_difference(new_ids))

      st.markdown("---")

      # عرض المربعات الثلاثة فقط بدقة
      m1, m2, m3 = st.columns(3)
      m1.metric("📦 عدد الكودات (الملف الرئيسي)", count_main)
      m2.metric("📁 عدد الكودات (ملف المقارنة)", count_new)
      m3.metric("⚠️ الفرق الإجمالي", diff_count)

  except Exception as e:
    st.error(f"حدث خطأ أثناء معالجة الملفات: {e}")
