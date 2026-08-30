import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="مقارن ملفات الإكسل الذكي", page_icon="📊", layout="wide"
)

if "active_filter" not in st.session_state:
  st.session_state["active_filter"] = "الكل"

with st.sidebar:
  st.markdown("### ⚙️ إعدادات التحكم")
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
    st.session_state["count_main"] = c_main
    st.session_state["count_new"] = c_new

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

    total_diff = code_diff_count + phone_diff_count + address_diff_count
    st.session_state["diff_count"] = total_diff
    st.session_state["code_diff_count"] = code_diff_count
    st.session_state["phone_diff_count"] = phone_diff_count
    st.session_state["address_diff_count"] = address_diff_count

    diff_df = pd.DataFrame(diff_records)
    st.session_state["diff_df"] = diff_df

  except Exception as e:
    st.error(f"حدث خطأ أثناء معالجة الملفات: {e}")

c_main = st.session_state.get("count_main", 0)
c_new = st.session_state.get("count_new", 0)
c_diff = st.session_state.get("diff_count", 0)
c_code_diff = st.session_state.get("code_diff_count", 0)
c_phone_diff = st.session_state.get("phone_diff_count", 0)
c_address_diff = st.session_state.get("address_diff_count", 0)

st.markdown("---")
st.markdown("### 📌 اضغط على أي بط أدناه لفلترة الجدول فوراً:")

# استخدام أزرار ستريمليت الأصلية الحقيقية (فعالة 100%) موزعة على 6 أعمدة
cols = st.columns(6)

with cols[0]:
  if st.button(
      f"🏠 العنوان\n({c_address_diff})",
      use_container_width=True,
      key="b_addr",
  ):
    st.session_state["active_filter"] = "فروقات العنوان"

with cols[1]:
  if st.button(
      f"📞 الهاتف\n({c_phone_diff})", use_container_width=True, key="b_phone"
  ):
    st.session_state["active_filter"] = "فروقات الهاتف"

with cols[2]:
  if st.button(
      f"🔑 الكود\n({c_code_diff})", use_container_width=True, key="b_code"
  ):
    st.session_state["active_filter"] = "فروقات الكود"

with cols[3]:
  if st.button(f"⚠️ الإجمالي\n({c_diff})", use_container_width=True, key="b_diff"):
    st.session_state["active_filter"] = "الكل"

with cols[4]:
  if st.button(f"📁 المقارنة\n({c_new})", use_container_width=True, key="b_new"):
    st.session_state["active_filter"] = "المقارنة"

with cols[5]:
  if st.button(
      f"📦 الرئيسي\n({c_main})", use_container_width=True, key="b_main"
  ):
    st.session_state["active_filter"] = "الرئيسي"

st.markdown(
    f"<div style='text-align: center; margin: 10px 0; font-weight: bold;"
    f" color: #4F46E5;'>الفلتر النشط حالياً: <span style='background: #e0e7ff;"
    f" padding: 3px 12px; border-radius: 6px;'>"
    f"{st.session_state['active_filter']}</span></div>",
    unsafe_allow_html=True,
)

st.markdown("---")
st.subheader(
    f"📋 جدول الاختلافات (الفلتر النشط: {st.session_state['active_filter']}):"
)

if (
    "diff_df" in st.session_state
    and not st.session_state["diff_df"].empty
):
  df_display = st.session_state["diff_df"].copy()
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
