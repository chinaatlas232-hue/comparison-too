import os
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="مقارن ملفات الإكسل الذكي", page_icon="📊", layout="wide"
)

# إنشاء مجلد لحفظ الملفات على السيرفر لضمان عدم ضياعها
UPLOAD_DIR = "saved_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

main_file_path = os.path.join(UPLOAD_DIR, "master_file.xlsx")
new_file_path = os.path.join(UPLOAD_DIR, "new_file.xlsx")

with st.sidebar:
  st.markdown("### ⚙️ إعدادات التحكم")

  # تنسيق زر المسح (خلفية حمراء وكتابة بيضاء)
  st.markdown(
      """
        <style>
        div.stButton > button[kind="secondary"] {
            background-color: #ef4444 !important;
            color: white !important;
        }
        div.stButton > button[kind="secondary"] p {
            color: white !important;
        }
        div.stButton > button[kind="secondary"]:hover {
            background-color: #dc2626 !important;
            color: white !important;
        }
        </style>
        """,
      unsafe_allow_html=True,
  )

  if st.button("🗑️ مسح الملفات وإعادة ضبط التطبيق", use_container_width=True):
    if os.path.exists(main_file_path):
      os.remove(main_file_path)
    if os.path.exists(new_file_path):
      os.remove(new_file_path)
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
  if uploaded_main is not None:
    with open(main_file_path, "wb") as f:
      f.write(uploaded_main.getbuffer())

with col2:
  uploaded_new = st.file_uploader(
      "📁 ارفع الملف المراد مقارنته (New File)",
      type=["xlsx", "xls"],
      key="new_file",
  )
  if uploaded_new is not None:
    with open(new_file_path, "wb") as f:
      f.write(uploaded_new.getbuffer())

# التحقق من وجود الملفات المحفوظة على السيرفر
active_main = (
    main_file_path
    if os.path.exists(main_file_path)
    else (uploaded_main if uploaded_main else None)
)
active_new = (
    new_file_path
    if os.path.exists(new_file_path)
    else (uploaded_new if uploaded_new else None)
)

if "active_filter" not in st.session_state:
  st.session_state["active_filter"] = "الكل"


@st.cache_data
def load_data(file1, file2):
  df1 = pd.read_excel(file1, sheet_name=0)
  df2 = pd.read_excel(file2, sheet_name=0)
  df1.columns = df1.columns.str.strip()
  df2.columns = df2.columns.str.strip()
  return df1, df2


# تهيئة المتغيرات الافتراضية
c_main, c_new, c_diff, c_code_diff, c_phone_diff, c_address_diff = (
    0,
    0,
    0,
    0,
    0,
    0,
)
diff_df = pd.DataFrame()

if (
    os.path.exists(main_file_path) and os.path.exists(new_file_path)
) or (active_main and active_new):
  try:
    df_main, df_new = load_data(active_main, active_new)

    common_cols = list(set(df_main.columns).intersection(set(df_new.columns)))

    code_col = next(
        (c for c in common_cols if "كود" in str(c) or "code" in str(c).lower()),
        None,
    )
    if not code_col:
      code_col = common_cols[0]

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

    address_col = next(
        (
            c
            for c in common_cols
            if "عنوان" in str(c)
            or "address" in str(c).lower()
            or "سكن" in str(c)
        ),
        None,
    )
    if not address_col:
      remaining_cols = [
          c for c in common_cols if c != code_col and c != phone_col
      ]
      address_col = remaining_cols[0] if remaining_cols else phone_col

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

    df_m["clean_id"] = clean_series(df_m[code_col])
    df_n["clean_id"] = clean_series(df_n[code_col])

    df_m["clean_phone"] = clean_series(df_m[phone_col])
    df_n["clean_phone"] = clean_series(df_n[phone_col])

    df_m["clean_addr"] = clean_series(df_m[address_col])
    df_n["clean_addr"] = clean_series(df_n[address_col])

    c_main = len(df_m["clean_id"].unique())
    c_new = len(df_n["clean_id"].unique())

    dict_new_phone = dict(zip(df_n["clean_id"], df_n["clean_phone"]))
    dict_main_phone = dict(zip(df_m["clean_id"], df_m["clean_phone"]))
    dict_new_addr = dict(zip(df_n["clean_id"], df_n["clean_addr"]))
    dict_main_addr = dict(zip(df_m["clean_id"], df_m["clean_addr"]))

    diff_records = []
    code_diff_count = 0
    phone_diff_count = 0
    address_diff_count = 0

    all_ids = set(dict_main_phone.keys()).union(set(dict_new_phone.keys()))

    for idx in all_ids:
      in_main = idx in dict_main_phone
      in_new = idx in dict_new_phone

      if in_main and in_new:
        p_main = dict_main_phone[idx]
        p_new = dict_new_phone[idx]
        a_main = dict_main_addr[idx]
        a_new = dict_new_addr[idx]

        has_phone_diff = p_main != p_new
        has_addr_diff = a_main != a_new

        if has_phone_diff or has_addr_diff:
          if has_phone_diff:
            phone_diff_count += 1
          if has_addr_diff:
            address_diff_count += 1

          if has_phone_diff and has_addr_diff:
            status_label = "اختلاف هاتف وعنوان"
          elif has_phone_diff:
            status_label = "اختلاف رقم الهاتف"
          else:
            status_label = "اختلاف العنوان"

          diff_records.append({
              "الكود": idx,
              f"{phone_col} (الرئيسي)": p_main,
              f"{phone_col} (المقارنة)": p_new,
              f"{address_col} (الرئيسي)": a_main,
              f"{address_col} (المقارنة)": a_new,
              "الحالة": status_label,
          })
      elif in_main and not in_new:
        code_diff_count += 1
        diff_records.append({
            "الكود": idx,
            f"{phone_col} (الرئيسي)": dict_main_phone[idx],
            f"{phone_col} (المقارنة)": "غير موجود",
            f"{address_col} (الرئيسي)": dict_main_addr[idx],
            f"{address_col} (المقارنة)": "غير موجود",
            "الحالة": "موجود في الرئيسي فقط",
        })
      elif not in_main and in_new:
        code_diff_count += 1
        diff_records.append({
            "الكود": idx,
            f"{phone_col} (الرئيسي)": "غير موجود",
            f"{phone_col} (المقارنة)": dict_new_phone[idx],
            f"{address_col} (الرئيسي)": "غير موجود",
            f"{address_col} (المقارنة)": dict_new_addr[idx],
            "الحالة": "موجود في المقارنة فقط",
        })

    c_diff = code_diff_count + phone_diff_count + address_diff_count
    c_code_diff = code_diff_count
    c_phone_diff = phone_diff_count
    c_address_diff = address_diff_count

    diff_df = pd.DataFrame(diff_records)

  except Exception as e:
    st.error(f"حدث خطأ أثناء معالجة الملفات: {e}")

st.markdown("---")
st.markdown("### 📌 اضغط على أي بطاقة أدناه لفلترة الجدول فوراً:")

# تنسيق الأزرار (خط بحجم 16px بدون خلفيات ملونة للمربعات)
st.markdown(
    """
    <style>
    div.stButton > button:not([kind="secondary"]) {
        background-color: transparent !important;
        border: 1px solid rgba(49, 51, 63, 0.2) !important;
        font-size: 16px !important;
        font-weight: bold !important;
    }
    div.stButton > button:not([kind="secondary"]) p {
        font-size: 16px !important;
        font-weight: bold !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

cols = st.columns(6)

with cols[0]:
  if st.button(
      f"🏠 العنوان\n\n{c_address_diff}",
      use_container_width=True,
      key="click_addr",
  ):
    st.session_state["active_filter"] = "فروقات العنوان"

with cols[1]:
  if st.button(
      f"📞 الهاتف\n\n{c_phone_diff}", use_container_width=True, key="click_phone"
  ):
    st.session_state["active_filter"] = "فروقات الهاتف"

with cols[2]:
  if st.button(
      f"🔑 الكود\n\n{c_code_diff}", use_container_width=True, key="click_code"
  ):
    st.session_state["active_filter"] = "فروقات الكود"

with cols[3]:
  if st.button(
      f"⚠️ الإجمالي\n\n{c_diff}", use_container_width=True, key="click_diff"
  ):
    st.session_state["active_filter"] = "الكل"

with cols[4]:
  if st.button(
      f"📁 المقارنة\n\n{c_new}", use_container_width=True, key="click_new"
  ):
    st.session_state["active_filter"] = "المقارنة"

with cols[5]:
  if st.button(
      f"📦 الرئيسي\n\n{c_main}", use_container_width=True, key="click_main"
  ):
    st.session_state["active_filter"] = "الرئيسي"

st.markdown(
    f"<div style='text-align: center; margin: 15px 0; font-size: 16px;"
    f" font-weight: bold; color: #4F46E5;'>الفلتر النشط حالياً: <span"
    f" style='background: #e0e7ff; padding: 6px 16px; border-radius: 8px;'>"
    f"{st.session_state['active_filter']}</span></div>",
    unsafe_allow_html=True,
)

st.markdown("---")
st.subheader(
    f"📋 جدول الاختلافات (الفلتر النشط: {st.session_state['active_filter']}):"
)

if not diff_df.empty:
  df_display = diff_df.copy()
  current_filter = st.session_state["active_filter"]

  if current_filter == "فروقات الكود":
    df_display = df_display[
        df_display["الحالة"].str.contains("فقط", na=False)
    ]
  elif current_filter == "فروقات الهاتف":
    df_display = df_display[
        df_display["الحالة"].str.contains("الهاتف|هاتف وعنوان", na=False)
    ]
  elif current_filter == "فروقات العنوان":
    df_display = df_display[
        df_display["الحالة"].str.contains("العنوان|هاتف وعنوان", na=False)
    ]
  elif current_filter == "الرئيسي":
    df_display = df_display[
        df_display["الحالة"].str.contains("موجود في الرئيسي فقط", na=False)
    ]
  elif current_filter == "المقارنة":
    df_display = df_display[
        df_display["الحالة"].str.contains("موجود في المقارنة فقط", na=False)
    ]

  if not df_display.empty:
    rows_html = ""
    for i, (_, row) in enumerate(df_display.iterrows(), 1):
      status_text = str(row["الحالة"]).strip()
      is_phone_diff = "الهاتف" in status_text or "العنوان" in status_text
      row_bg = "background-color: #faf5ff;" if is_phone_diff else ""

      cells_html = (
          f'<td style="padding: 10px; text-align: center; border-bottom: 1px'
          f' solid #e5e7eb; font-size: 14px; {row_bg} font-weight:'
          f' bold;">{i}</td>'
      )
      for val in row:
        cells_html += f'<td style="padding: 10px; text-align: center; border-bottom: 1px solid #e5e7eb; font-size: 14px; {row_bg}">{val}</td>'

      rows_html += f"<tr>{cells_html}</tr>"

    columns_list = ["التسلسل"] + list(df_display.columns)
    headers_html = "".join(
        f'<th style="background-color: #4f46e5; color: white; padding: 12px; text-align: center; font-size: 14px;">{col}</th>'
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
    st.info("لا توجد بيانات مطابقة لهذا الفلتر.")
else:
  st.info("لا توجد اختلافات بين الملفين أو لم يتم رفع الملفات بعد.")
