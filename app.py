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

# متغيرات افتراضية للنتائج
count_main = 0
count_new = 0
diff_count = 0

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

    common_cols = list(set(df_main.columns).intersection(set(df_new.columns)))
    default_id_idx = common_cols.index("الكود") if "الكود" in common_cols else 0

    id_col = st.selectbox(
        "🔑 اختر عمود الكود المشترك حصراً:", common_cols, index=default_id_idx
    )

    if st.button("🚀 ابدأ المقارنة", use_container_width=True):
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

      st.session_state["count_main"] = len(main_ids)
      st.session_state["count_new"] = len(new_ids)
      st.session_state["diff_count"] = len(main_ids.symmetric_difference(new_ids))

  except Exception as e:
    st.error(f"حدث خطأ أثناء معالجة الملفات: {e}")

# جلب القيم إذا تمت المقارنة
c_main = st.session_state.get("count_main", 0)
c_new = st.session_state.get("count_new", 0)
c_diff = st.session_state.get("diff_count", 0)

st.markdown("---")

# عرض المربعات الثلاثة في أعلى الصفحة بتدرجات لونية جميلة
st.markdown(
    """
    <style>
    .metric-card-1 {
        background: linear-gradient(135deg, #3b82f6, #1d4ed8);
        padding: 20px;
        border-radius: 12px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-card-2 {
        background: linear-gradient(135deg, #8b5cf6, #6d28d9);
        padding: 20px;
        border-radius: 12px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-card-3 {
        background: linear-gradient(135deg, #f59e0b, #d97706);
        padding: 20px;
        border-radius: 12px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-title {
        font-size: 16px;
        font-weight: bold;
        margin-bottom: 8px;
    }
    .metric-value {
        font-size: 28px;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

col1, col2, col3 = st.columns(3)

with col1:
  st.markdown(
      f"""
        <div class="metric-card-1">
            <div class="metric-title">📦 عدد الكودات (الملف الرئيسي)</div>
            <div class="metric-value">{c_main}</div>
        </div>
        """,
      unsafe_allow_html=True,
  )

with col2:
  st.markdown(
      f"""
        <div class="metric-card-2">
            <div class="metric-title">📁 عدد الكودات (ملف المقارنة)</div>
            <div class="metric-value">{c_new}</div>
        </div>
        """,
      unsafe_allow_html=True,
  )

with col3:
  st.markdown(
      f"""
        <div class="metric-card-3">
            <div class="metric-title">⚠️ الفرق الإجمالي</div>
            <div class="metric-value">{c_diff}</div>
        </div>
        """,
      unsafe_allow_html=True,
  )
