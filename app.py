import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="مقارن ملفات الإكسل الذكي", page_icon="📊", layout="wide"
)

# زر المسح اليدوي في القائمة الجانبية
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
    <h2 style='text-align: center; color: #4F46E5;'>📊 أداة مقارنة الملفات الذكية (فلتر الكود الشامل)</h2>
    """,
    unsafe_allow_html=True,
)

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


if uploaded_main and uploaded_new:
  try:
    df_main, df_new = load_data(uploaded_main, uploaded_new)

    common_cols = list(set(df_main.columns).intersection(set(df_new.columns)))

    # تحديد عمود الكود تلقائياً
    code_col = next(
        (c for c in common_cols if "كود" in str(c) or "code" in str(c).lower()),
        None,
    )
    if not code_col:
      code_col = common_cols[0]

    # تحديد عمود الهاتف تلقائياً
    phone_col = next(
        (
            c
            for c in common_cols
            if "هاتف" in str(c) or "phone" in str(c).lower()
        ),
        None,
    )
    if not phone_col and len(common_cols) > 1:
      phone_col = [c for c in common_cols if c != code_col][0]
    elif not phone_col:
      phone_col = code_col

    st.markdown(
        f"📌 **فلتر الكود النشط حصراً:** الاعتماد على عمود (`{code_col}`) للبحث"
        f" ومقارنة عمود (`{phone_col}`)",
        unsafe_allow_html=True,
    )

    def clean_series(series):
      return (
          series.astype(str)
          .str.replace(r"\.0$", "", regex=True)
          .str.strip()
          .fillna("")
          .replace("nan", "")
          .replace("None", "")
      )

    df_m = df_main.copy()
    df_n = df_new.copy()

    # تنظيف البيانات
    df_m["clean_id"] = clean_series(df_m[code_col])
    df_n["clean_id"] = clean_series(df_n[code_col])

    df_m["clean_val"] = clean_series(df_m[phone_col])
    df_n["clean_val"] = clean_series(df_n[phone_col])

    st.session_state["count_main"] = len(df_m["clean_id"].unique())
    st.session_state["count_new"] = len(df_n["clean_id"].unique())

    # دمج البيانات بناءً على الكود لمعالجة الاختلافات والمفقودات معاً
    merged = pd.merge(
        df_m[["clean_id", "clean_val"]],
        df_n[["clean_id", "clean_val"]],
        on="clean_id",
        how="outer",
        suffixes=("_main", "_new"),
    )

    # تصنيف الاختلافات:
    # 1. كود موجود في الرئيسي وغير موجود في المقارنة
    # 2. كود موجود في المقارنة وغير موجود في الرئيسي
    # 3. كود موجود في الملفين لكن رقم الهاتف مختلف
    diff_mask = (
        merged["clean_val_main"].isna()
        | (merged["clean_val_main"] == "")
        | merged["clean_val_new"].isna()
        | (merged["clean_val_new"] == "")
        | (merged["clean_val_main"] != merged["clean_val_new"])
    )

    diff_rows = merged[diff_mask].copy()

    st.session_state["diff_count"] = len(diff_rows)

    if not diff_rows.empty:
      def get_status(row):
        if pd.isna(row["clean_val_main"]) or row["clean_val_main"] == "":
          return "موجود في المقارنة فقط (غير موجود بالرئيسي)"
        elif pd.isna(row["clean_val_new"]) or row["clean_val_new"] == "":
          return "موجود في الرئيسي فقط (غير موجود بالمقارنة)"
        else:
          return "اختلاف في رقم الهاتف"

      diff_rows["حالة_الاختلاف"] = diff_rows.apply(get_status, axis=1)

      final_result = pd.DataFrame({
          "الكود": diff_rows["clean_id"],
          f"{phone_col} (الرئيسي)": diff_rows["clean_val_main"].fillna(
              "غير متوفر"
          ),
          f"{phone_col} (المقارنة)": diff_rows["clean_val_new"].fillna(
              "غير متوفر"
          ),
          "نوع الاختلاف": diff_rows["حالة_الاختلاف"],
      })
      st.session_state["diff_df"] = final_result
    else:
      st.session_state["diff_df"] = pd.DataFrame(
          columns=["الكود", "الرئيسي", "المقارنة", "نوع الاختلاف"]
      )

  except Exception as e:
    st.error(f"حدث خطأ أثناء معالجة الملفات: {e}")

c_main = st.session_state.get("count_main", 0)
c_new = st.session_state.get("count_new", 0)
c_diff = st.session_state.get("diff_count", 0)

st.markdown("---")

if c_diff > 0:
  diff_bg = "linear-gradient(135deg, #ef4444, #b91c1c)"
else:
  diff_bg = "linear-gradient(135deg, #4b5563, #1f2937)"

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

st.markdown("---")
st.subheader("📋 جدول الاختلافات الشامل (أكواد مختلفة + أكواد غير متطابقة):")
if (
    "diff_df" in st.session_state
    and not st.session_state["diff_df"].empty
):
  st.dataframe(
      st.session_state["diff_df"], use_container_width=True, hide_index=True
  )
else:
  st.info("لا توجد اختلافات مسجلة.")
