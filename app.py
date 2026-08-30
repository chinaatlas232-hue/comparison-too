import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="مقارن ملفات الإكسل الذكي", page_icon="📊", layout="wide"
)

# زر المسح اليدوي في القائمة الجانبية (باللون الأحمر)
with st.sidebar:
  st.markdown("### ⚙️ إعدادات التحكم")

  st.markdown(
      """
        <style>
        div.stButton > button:first-child {
            background-color: #ef4444;
            color: white;
            border-radius: 8px;
            border: none;
            font-weight: bold;
        }
        div.stButton > button:first-child:hover {
            background-color: #dc2626;
            color: white;
        }
        </style>
        """,
      unsafe_allow_html=True,
  )

  if st.button("🗑️ مسح الملفات وإعادة ضبط التطبيق", use_container_width=True):
    for key in list(st.session_state.keys()):
      del st.session_state[key]
    st.rerun()

st.markdown(
    """
    <h2 style='text-align: center; color: #4F46E5;'>📊 أداة مقارنة الملفات الذكية</h2>
    """,
    unsafe_allow_html=True,
)

# رفع الملفات مع الحفاظ على حالتها في الذاكرة المؤقتة
col1, col2 = st.columns(2)
with col1:
    uploaded_main = st.file_uploader(
        "📁 ارفع الملف الرئيسي (Master File)",
        type=["xlsx", "xls"],
        key="main_file",
    )
with col2:
    uploaded_new = st.file_uploader(
        "📁 ارفع الملف المراد مقارنته (New File)",
        type=["xlsx", "xls"],
        key="new_file",
    )


@st.cache_data
def load_data(file1, file2):
  df1 = pd.read_excel(file1, sheet_name=0)
  df2 = pd.read_excel(file2, sheet_name=0)
  df1.columns = df1.columns.str.strip()
  df2.columns = df2.columns.str.strip()
  return df1, df2


# المعالجة التلقائية وفحص النتائج فور رفع الملفات
if uploaded_main and uploaded_new:
  try:
    df_main, df_new = load_data(uploaded_main, uploaded_new)

    common_cols = list(set(df_main.columns).intersection(set(df_new.columns)))

    # محاولة جعل الافتراضي يختار "الكود" أو "رقم الهاتف" إن وجد
    default_idx = 0
    for i, col in enumerate(common_cols):
      if "الكود" in str(col) or "هاتف" in str(col) or "phone" in str(col).lower():
        default_idx = i
        break

    # قائمة منسدلة واحدة فقط لتحديد العمود المستهدف للمقارنة (سواء كود أو رقم هاتف)
    selected_col = st.selectbox(
        "🔑 اختر عمود المقارنة الأساسي (الكود أو رقم الهاتف):",
        common_cols,
        index=default_idx,
    )

    def clean_series(series):
      return (
          series.astype(str)
          .str.replace(r"\.0$", "", regex=True)
          .str.strip()
          .fillna("")
          .replace("nan", "")
      )

    main_vals = clean_series(df_main[selected_col])
    new_vals = clean_series(df_new[selected_col])

    main_set = set(main_vals[main_vals != ""])
    new_set = set(new_vals[new_vals != ""])

    st.session_state["count_main"] = len(main_set)
    st.session_state["count_new"] = len(new_set)

    diff_set = main_set.symmetric_difference(new_set)
    st.session_state["diff_count"] = len(diff_set)

    if diff_set:
      st.session_state["diff_df"] = pd.DataFrame(
          list(diff_set), columns=[f"القيم المختلفة لـ ({selected_col})"]
      )
    else:
      st.session_state["diff_df"] = pd.DataFrame(
          columns=[f"القيم المختلفة لـ ({selected_col})"]
      )

  except Exception as e:
    st.error(f"حدث خطأ أثناء معالجة الملفات: {e}")

c_main = st.session_state.get("count_main", 0)
c_new = st.session_state.get("count_new", 0)
c_diff = st.session_state.get("diff_count", 0)

st.markdown("---")

# تحديد لون المربع الثالث بناءً على وجود فرق أو عدمه
if c_diff > 0:
  diff_bg = "linear-gradient(135deg, #ef4444, #b91c1c)"
else:
  diff_bg = "linear-gradient(135deg, #4b5563, #1f2937)"

# تصميم المربعات الثلاثة بالألوان المطلوبة
st.markdown(
    f"""
    <style>
    .metric-card-1 {{ background: linear-gradient(135deg, #10b981, #047857); padding: 20px; border-radius: 12px; color: white; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
    .metric-card-2 {{ background: linear-gradient(135deg, #f97316, #c2410c); padding: 20px; border-radius: 12px; color: white; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
    .metric-card-3 {{ background: {diff_bg}; padding: 20px; border-radius: 12px; color: white; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
    .metric-title {{ font-size: 16px; font-weight: bold; margin-bottom: 8px; }}
    .metric-value {{ font-size: 28px; font-weight: bold; }}
    </style>
    """,
    unsafe_allow_html=True,
)

col1, col2, col3 = st.columns(3)
with col1:
  st.markdown(
      f"""
        <div class="metric-card-1">
            <div class="metric-title">📦 عدد العناصر (الملف الرئيسي)</div>
            <div class="metric-value">{c_main}</div>
        </div>
        """,
      unsafe_allow_html=True,
  )
with col2:
  st.markdown(
      f"""
        <div class="metric-card-2">
            <div class="metric-title">📁 عدد العناصر (ملف المقارنة)</div>
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

# عرض جدول النتائج والاختلافات في أسفل الشاشة بناءً على القائمة الوحيدة
st.markdown("---")
st.subheader("📋 جدول الاختلافات (النتيجة):")
if (
    "diff_df" in st.session_state
    and not st.session_state["diff_df"].empty
):
  st.dataframe(
      st.session_state["diff_df"], use_container_width=True, hide_index=True
  )
else:
  st.info(
      "الرجاء رفع الملفات واختيار العمود المطلوب من القائمة أعلاه لعرض"
      " النتائج."
  )
