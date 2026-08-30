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
    <h2 style='text-align: center; color: #4F46E5;'>📊 أداة مقارنة الملفات الذكية (المطابقة الدقيقة)</h2>
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
        f"📌 **فلتر الكود النشط:** البحث والمقارنة عبر عمود (`{code_col}`)",
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

    # تنظيف البيانات بدقة
    df_m["clean_id"] = clean_series(df_m[code_col])
    df_n["clean_id"] = clean_series(df_n[code_col])

    df_m["clean_val"] = clean_series(df_m[phone_col])
    df_n["clean_val"] = clean_series(df_n[phone_col])

    c_main = len(df_m["clean_id"].unique())
    c_new = len(df_n["clean_id"].unique())
    st.session_state["count_main"] = c_main
    st.session_state["count_new"] = c_new

    # حساب الفرق الإجمالي بين عددي الملفين
    st.session_state["diff_count"] = abs(c_main - c_new)

    # بناء قواميس البحث
    dict_new = dict(zip(df_n["clean_id"], df_n["clean_val"]))
    dict_main = dict(zip(df_m["clean_id"], df_m["clean_val"]))

    diff_records = []
    phone_diff_count = 0  # عداد فروقات أرقام الهواتف

    # فحص الكودات في الرئيسي ومقارنتها بالمقارنة
    for idx, val in dict_main.items():
      if idx in dict_new:
        if val != dict_new[idx]:
          phone_diff_count += 1
          diff_records.append({
              "الكود": idx,
              f"{phone_col} (الرئيسي)": val,
              f"{phone_col} (المقارنة)": dict_new[idx],
              "الحالة": "اختلاف رقم الهاتف",
          })
      else:
        diff_records.append({
            "الكود": idx,
            f"{phone_col} (الرئيسي)": val,
            f"{phone_col} (المقارنة)": "غير موجود",
            "الحالة": "موجود في الرئيسي فقط",
        })

    # فحص الكودات الموجودة في المقارنة وليست في الرئيسي
    for idx, val in dict_new.items():
      if idx not in dict_main:
        diff_records.append({
            "الكود": idx,
            f"{phone_col} (الرئيسي)": "غير موجود",
            f"{phone_col} (المقارنة)": val,
            "الحالة": "موجود في المقارنة فقط",
        })

    st.session_state["phone_diff_count"] = phone_diff_count
    diff_df = pd.DataFrame(diff_records)

    # تطبيق التنسيق مباشرة كـ HTML لضمان اللون الأحمر والخط العريض وحجم 14 للكود
    if not diff_df.empty and "الكود" in diff_df.columns:
      diff_df["الكود"] = diff_df["الكود"].apply(
          lambda x: (
              f"<span style='color: #dc2626; font-weight: bold; font-size:"
              f" 14px;'>{x}</span>"
          )
      )

    st.session_state["diff_df"] = diff_df

  except Exception as e:
    st.error(f"حدث خطأ أثناء معالجة الملفات: {e}")

c_main = st.session_state.get("count_main", 0)
c_new = st.session_state.get("count_new", 0)
c_diff = st.session_state.get("diff_count", 0)
c_phone_diff = st.session_state.get("phone_diff_count", 0)

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
    .metric-card-4 {{ background: linear-gradient(135deg, #f472b6, #db2777); padding: 20px; border-radius: 12px; color: white; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
    .metric-title {{ font-size: 15px; font-weight: bold; margin-bottom: 8px; }}
    .metric-value {{ font-size: 26px; font-weight: bold; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# عرض 4 مربعات متناسقة بعرض الشاشة
col1, col2, col3, col4 = st.columns(4)
with col1:
  st.markdown(
      f"""
        <div class="metric-card-1">
            <div class="metric-title">📦 عناصر الرئيسي</div>
            <div class="metric-value">{c_main}</div>
        </div>
        """,
      unsafe_allow_html=True,
  )
with col2:
  st.markdown(
      f"""
        <div class="metric-card-2">
            <div class="metric-title">📁 عناصر المقارنة</div>
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
with col4:
  st.markdown(
      f"""
        <div class="metric-card-4">
            <div class="metric-title">📞 فروقات رقم الهاتف</div>
            <div class="metric-value">{c_phone_diff}</div>
        </div>
        """,
      unsafe_allow_html=True,
  )

st.markdown("---")
st.subheader("📋 جدول الاختلافات المطابقة بناءً على الكود:")

if (
    "diff_df" in st.session_state
    and not st.session_state["diff_df"].empty
):
  df_display = st.session_state["diff_df"].copy()

  # بناء الهيكل اليدوي للجدول مع إضافة عمود التسلسل كأول عمود
  rows_html = ""
  for i, (_, row) in enumerate(df_display.iterrows(), 1):
    is_phone_diff = str(row["الحالة"]).strip() == "اختلاف رقم الهاتف"
    row_bg = "background-color: #fdf2f8;" if is_phone_diff else ""

    # دمج عمود التسلسل مع بقية الأعمدة
    cells_html = (
        f'<td style="padding: 10px; text-align: center; border-bottom: 1px'
        f' solid #e5e7eb; font-size: 14px; {row_bg} font-weight:'
        f' bold;">{i}</td>'
    )
    for val in row:
      cells_html += f'<td style="padding: 10px; text-align: center; border-bottom: 1px solid #e5e7eb; font-size: 14px; {row_bg}">{val}</td>'

    rows_html += f"<tr>{cells_html}</tr>"

  # تجهيز أسماء الأعمدة مع إضافة عمود "التسلسل"
  columns_list = ["التسلسل"] + list(df_display.columns)
  headers_html = "".join(
      f'<th style="background-color: #2563eb; color: white; padding: 12px; text-align: center; font-size: 15px;">{col}</th>'
      for col in columns_list
  )

  final_table = f"""
    <table style="width: 100%; border-collapse: collapse; direction: rtl; font-family: sans-serif;">
        <thead><tr>{headers_html}</tr></thead>
        <tbody>{rows_html}</tbody>
    </table>
    """

  st.markdown(final_table, unsafe_allow_html=True)
else:
  st.info("لا توجد اختلافات بين الملفين.")
