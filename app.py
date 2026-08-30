import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="مقارن ملفات الإكسل الذكي", page_icon="📊", layout="wide"
)

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

    # قائمة واحدة لاختيار عمود الكود المشترك
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

      # استخراج وتنظيف الأكواد من الملفين حصراً
      main_ids = set(clean_series(df_main[id_col]))
      new_ids = set(clean_series(df_new[id_col]))

      # إزالة القيم الفارغة إن وجدت
      main_ids.discard("")
      new_ids.discard("")

      count_main = len(main_ids)
      count_new = len(new_ids)

      # حساب الفرق (مثلاً عدد الأكواد المختلفة أو الغير متطابقة)
      # يمكنك اختيار الفرق المطلق أو الأكواد الموجودة في الرئيسي وليست في الجديد أو العكس
      diff_count = len(main_ids.symmetric_difference(new_ids))

      st.markdown("---")

      # عرض 3 مربعات واضحة فقط بدون أي نتائج تفصيلية بالأسفل
      m1, m2, m3 = st.columns(3)
      m1.metric("📦 عدد الكودات (الملف الرئيسي)", count_main)
      m2.metric("📁 عدد الكودات (ملف المقارنة)", count_new)
      m3.metric("⚠️ الفرق الإجمالي", diff_count)

  except Exception as e:
    st.error(f"حدث خطأ أثناء معالجة الملفات: {e}")
