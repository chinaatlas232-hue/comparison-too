import io
import os
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="مقارن ملفات الإكسل الذكي", page_icon="📊", layout="wide"
)

# معالجة استلام الضغط على البطاقات عبر query_params
query_params = st.query_params
if "filter" in query_params:
  st.session_state["active_filter"] = query_params["filter"]

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }
    [data-testid="stSidebar"] {
        background-color: rgba(180, 180, 180, 0.72) !important;
    }
    
    /* تصميم البطاقات الملونة البديلة للأزرار */
    .custom-card {
        border-radius: 8px;
        padding: 12px 8px;
        text-align: center;
        cursor: pointer;
        text-decoration: none !important;
        display: block;
        transition: transform 0.1s ease, box-shadow 0.1s ease;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .custom-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.15);
    }
    
    /* ألوان البطاقات */
    .card-city { background-color: rgba(34, 197, 94, 0.2); border: 1px solid rgba(34, 197, 94, 0.4); color: #15803d; }
    .card-addr { background-color: rgba(234, 179, 8, 0.2); border: 1px solid rgba(234, 179, 8, 0.4); color: #a16207; }
    .card-phone { background-color: rgba(249, 115, 22, 0.2); border: 1px solid rgba(249, 115, 22, 0.4); color: #c2410c; }
    .card-code { background-color: rgba(59, 130, 246, 0.2); border: 1px solid rgba(59, 130, 246, 0.4); color: #1d4ed8; }
    .card-diff { background-color: rgba(239, 68, 68, 0.2); border: 1px solid rgba(239, 68, 68, 0.4); color: #b91c1c; }
    .card-new { background-color: rgba(168, 85, 247, 0.2); border: 1px solid rgba(168, 85, 247, 0.4); color: #7e22ce; }
    .card-main { background-color: rgba(107, 114, 128, 0.2); border: 1px solid rgba(107, 114, 128, 0.4); color: #374151; }

    .card-title {
        font-size: 15px;
        font-weight: bold;
        margin-bottom: 8px;
    }
    .card-value {
        font-size: 18px;
        font-weight: bold;
    }

    /* زر تحميل الإكسل أخضر فاتح */
    div.stDownloadButton > button {
        background-color: rgba(34, 197, 94, 0.2) !important;
        color: #15803d !important;
        border: 1px solid rgba(34, 197, 94, 0.4) !important;
        font-weight: bold !important;
    }
    div.stDownloadButton > button:hover {
        background-color: rgba(34, 197, 94, 0.35) !important;
        color: #166534 !important;
    }
    div.stDownloadButton > button p {
        color: #15803d !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

UPLOAD_DIR = "saved_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

main_file_path = os.path.join(UPLOAD_DIR, "master_file.xlsx")
new_file_path = os.path.join(UPLOAD_DIR, "new_file.xlsx")

with st.sidebar:
  st.markdown("### 📁 إدارة الملفات")

  uploaded_main = st.file_uploader(
      "الملف الرئيسي (Master File)", type=["xlsx", "xls"], key="main_file"
  )
  if uploaded_main is not None:
    with open(main_file_path, "wb") as f:
      f.write(uploaded_main.getbuffer())

  st.markdown("---")

  uploaded_new = st.file_uploader(
      "الملف المراد مقارنته (New File)", type=["xlsx", "xls"], key="new_file"
  )
  if uploaded_new is not None:
    with open(new_file_path, "wb") as f:
      f.write(uploaded_new.getbuffer())

  st.markdown("---")
  st.markdown("### ⚙️ إعدادات التحكم")

  if st.button(
      "🗑️ مسح الملفات وإعادة ضبط التطبيق",
      use_container_width=True,
      type="primary",
  ):
    if os.path.exists(main_file_path):
      os.remove(main_file_path)
    if os.path.exists(new_file_path):
      os.remove(new_file_path)
    for key in list(st.session_state.keys()):
      del st.session_state[key]
    st.query_params.clear()
    st.rerun()

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

# التعامل مع الضغط وتغيير الفلتر
if "filter" in st.query_params:
  selected_f = st.query_params["filter"]
  if st.session_state["active_filter"] != selected_f:
    st.session_state["active_filter"] = selected_f
    st.rerun()


def load_data(file1, file2):
  df1 = pd.read_excel(file1, sheet_name=0)
  df2 = pd.read_excel(file2, sheet_name=0)
  df1.columns = df1.columns.str.strip()
  df2.columns = df2.columns.str.strip()
  return df1, df2


c_main, c_new, c_diff, c_code_diff, c_phone_diff, c_city_diff, c_address_diff = (
    0,
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
            if "هاتف" in str(c)
            or "رقم" in str(c)
            or "phone" in str(c).lower()
        ),
        None,
    )

    city_col = next(
        (
            c
            for c in common_cols
            if "مدين" in str(c)
            or "city" in str(c).lower()
            or "محافظ" in str(c)
        ),
        None,
    )

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

    def clean_series(series):
      if series is None:
        return pd.Series([""] * len(df_main))
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

    df_m["clean_id"] = clean_series(df_m[code_col] if code_col else None)
    df_n["clean_id"] = clean_series(df_n[code_col] if code_col else None)

    df_m["clean_phone"] = clean_series(
        df_m[phone_col] if phone_col and phone_col in df_m.columns else None
    )
    df_n["clean_phone"] = clean_series(
        df_n[phone_col] if phone_col and phone_col in df_n.columns else None
    )

    df_m["clean_city"] = clean_series(
        df_m[city_col] if city_col and city_col in df_m.columns else None
    )
    df_n["clean_city"] = clean_series(
        df_n[city_col] if city_col and city_col in df_n.columns else None
    )

    df_m["clean_addr"] = clean_series(
        df_m[address_col]
        if address_col and address_col in df_m.columns
        else None
    )
    df_n["clean_addr"] = clean_series(
        df_n[address_col]
        if address_col and address_col in df_n.columns
        else None
    )

    c_main = len(df_m["clean_id"].unique())
    c_new = len(df_n["clean_id"].unique())

    dict_main_phone = dict(zip(df_m["clean_id"], df_m["clean_phone"]))
    dict_new_phone = dict(zip(df_n["clean_id"], df_n["clean_phone"]))

    dict_main_city = dict(zip(df_m["clean_id"], df_m["clean_city"]))
    dict_new_city = dict(zip(df_n["clean_id"], df_n["clean_city"]))

    dict_main_addr = dict(zip(df_m["clean_id"], df_m["clean_addr"]))
    dict_new_addr = dict(zip(df_n["clean_id"], df_n["clean_addr"]))

    diff_records = []
    code_diff_count = 0
    phone_diff_count = 0
    city_diff_count = 0
    address_diff_count = 0

    all_ids = set(dict_main_phone.keys()).union(set(dict_new_phone.keys()))

    p_col_name = phone_col if phone_col else "الهاتف"
    ci_col_name = city_col if city_col else "المدينة"
    a_col_name = address_col if address_col else "العنوان"

    for idx in all_ids:
      in_main = idx in dict_main_phone
      in_new = idx in dict_new_phone

      if in_main and in_new:
        p_main = dict_main_phone.get(idx, "")
        p_new = dict_new_phone.get(idx, "")
        ci_main = dict_main_city.get(idx, "")
        ci_new = dict_new_city.get(idx, "")
        a_main = dict_main_addr.get(idx, "")
        a_new = dict_new_addr.get(idx, "")

        has_phone_diff = p_main != p_new
        has_city_diff = ci_main != ci_new
        has_addr_diff = a_main != a_new

        if has_phone_diff or has_city_diff or has_addr_diff:
          if has_phone_diff:
            phone_diff_count += 1
          if has_city_diff:
            city_diff_count += 1
          if has_addr_diff:
            address_diff_count += 1

          diff_labels = []
          if has_phone_diff:
            diff_labels.append("هاتف")
          if has_city_diff:
            diff_labels.append("مدينة")
          if has_addr_diff:
            diff_labels.append("عنوان")

          status_label = "اختلاف " + " و ".join(diff_labels)

          diff_records.append({
              "الكود": idx,
              f"{p_col_name} (الرئيسي)": p_main,
              f"{p_col_name} (المقارنة)": p_new,
              f"{ci_col_name} (الرئيسي)": ci_main,
              f"{ci_col_name} (المقارنة)": ci_new,
              f"{a_col_name} (الرئيسي)": a_main,
              f"{a_col_name} (المقارنة)": a_new,
              "الحالة": status_label,
          })
      elif in_main and not in_new:
        code_diff_count += 1
        diff_records.append({
            "الكود": idx,
            f"{p_col_name} (الرئيسي)": dict_main_phone.get(idx, ""),
            f"{p_col_name} (المقارنة)": "غير موجود",
            f"{ci_col_name} (الرئيسي)": dict_main_city.get(idx, ""),
            f"{ci_col_name} (المقارنة)": "غير موجود",
            f"{a_col_name} (الرئيسي)": dict_main_addr.get(idx, ""),
            f"{a_col_name} (المقارنة)": "غير موجود",
            "الحالة": "موجود في الرئيسي فقط",
        })
      elif not in_main and in_new:
        code_diff_count += 1
        diff_records.append({
            "الكود": idx,
            f"{p_col_name} (الرئيسي)": "غير موجود",
            f"{p_col_name} (المقارنة)": dict_new_phone.get(idx, ""),
            f"{ci_col_name} (الرئيسي)": "غير موجود",
            f"{ci_col_name} (المقارنة)": dict_new_city.get(idx, ""),
            f"{a_col_name} (الرئيسي)": "غير موجود",
            f"{a_col_name} (المقارنة)": dict_new_addr.get(idx, ""),
            "الحالة": "الكود غير موجود بقاعدة البيانات السابقة",
        })

    c_diff = (
        code_diff_count
        + phone_diff_count
        + city_diff_count
        + address_diff_count
    )
    c_code_diff = code_diff_count
    c_phone_diff = phone_diff_count
    c_city_diff = city_diff_count
    c_address_diff = address_diff_count

    diff_df = pd.DataFrame(diff_records)

  except Exception as e:
    st.error(f"حدث خطأ أثناء معالجة الملفات: {e}")

st.markdown(
    """
    <div style="direction: rtl; text-align: right; font-size: 18px; font-weight: bold; margin-bottom: 10px;">
        📌 اضغط على أي بطاقة أدناه لفلترة الجدول فوراً:
    </div>
    """,
    unsafe_allow_html=True,
)

cols = st.columns(7)

with cols[0]:
  st.markdown(
      f"""<a href="?filter=فروقات المدينة" target="_self" class="custom-card" style="background-color: rgba(34, 197, 94, 0.25); border: 1px solid rgba(34, 197, 94, 0.4); color: #15803d;">
        <div style="font-size: 15px; font-weight: bold; margin-bottom: 8px;">🏙️ المدينة</div>
        <div style="font-size: 18px; font-weight: bold;">{c_city_diff}</div>
    </a>""",
      unsafe_allow_html=True,
  )

with cols[1]:
  st.markdown(
      f"""<a href="?filter=فروقات العنوان" target="_self" class="custom-card" style="background-color: rgba(234, 179, 8, 0.25); border: 1px solid rgba(234, 179, 8, 0.4); color: #a16207;">
        <div style="font-size: 15px; font-weight: bold; margin-bottom: 8px;">🏠 العنوان</div>
        <div style="font-size: 18px; font-weight: bold;">{c_address_diff}</div>
    </a>""",
      unsafe_allow_html=True,
  )

with cols[2]:
  st.markdown(
      f"""<a href="?filter=فروقات الهاتف" target="_self" class="custom-card" style="background-color: rgba(249, 115, 22, 0.25); border: 1px solid rgba(249, 115, 22, 0.4); color: #c2410c;">
        <div style="font-size: 15px; font-weight: bold; margin-bottom: 8px;">📞 الهاتف</div>
        <div style="font-size: 18px; font-weight: bold;">{c_phone_diff}</div>
    </a>""",
      unsafe_allow_html=True,
  )

with cols[3]:
  st.markdown(
      f"""<a href="?filter=فروقات الكود" target="_self" class="custom-card" style="background-color: rgba(59, 130, 246, 0.25); border: 1px solid rgba(59, 130, 246, 0.4); color: #1d4ed8;">
        <div style="font-size: 15px; font-weight: bold; margin-bottom: 8px;">🔑 الكود</div>
        <div style="font-size: 18px; font-weight: bold;">{c_code_diff}</div>
    </a>""",
      unsafe_allow_html=True,
  )

with cols[4]:
  st.markdown(
      f"""<a href="?filter=الكل" target="_self" class="custom-card" style="background-color: rgba(239, 68, 68, 0.25); border: 1px solid rgba(239, 68, 68, 0.4); color: #b91c1c;">
        <div style="font-size: 15px; font-weight: bold; margin-bottom: 8px;">⚠️ الإجمالي</div>
        <div style="font-size: 18px; font-weight: bold;">{c_diff}</div>
    </a>""",
      unsafe_allow_html=True,
  )

with cols[5]:
  st.markdown(
      f"""<a href="?filter=المقارنة" target="_self" class="custom-card" style="background-color: rgba(168, 85, 247, 0.25); border: 1px solid rgba(168, 85, 247, 0.4); color: #7e22ce;">
        <div style="font-size: 15px; font-weight: bold; margin-bottom: 8px;">📁 المقارنة</div>
        <div style="font-size: 18px; font-weight: bold;">{c_new}</div>
    </a>""",
      unsafe_allow_html=True,
  )

with cols[6]:
  st.markdown(
      f"""<a href="?filter=الرئيسي" target="_self" class="custom-card" style="background-color: rgba(107, 114, 128, 0.25); border: 1px solid rgba(107, 114, 128, 0.4); color: #374151;">
        <div style="font-size: 15px; font-weight: bold; margin-bottom: 8px;">📦 الرئيسي</div>
        <div style="font-size: 18px; font-weight: bold;">{c_main}</div>
    </a>""",
      unsafe_allow_html=True,
  )

st.markdown(
    f"<div style='text-align: center; margin: 15px 0; font-size: 16px;"
    f" font-weight: bold; color: #4F46E5; direction: rtl;'>الفلتر النشط حالياً:"
    f" <span style='background: #e0e7ff; padding: 6px 16px; border-radius:"
    f" 8px;'>{st.session_state['active_filter']}</span></div>",
    unsafe_allow_html=True,
)

st.markdown("---")

st.markdown(
    """
    <div style="direction: rtl; text-align: right; font-size: 20px; font-weight: bold; margin-bottom: 10px;">
        📋 جدول الاختلافات:
    </div>
    """,
    unsafe_allow_html=True,
)

if not diff_df.empty:
  df_display = diff_df.copy()
  current_filter = st.session_state["active_filter"]

  if current_filter == "فروقات الكود":
    df_display = df_display[
        df_display["الحالة"].str.contains(
            "موجود في الرئيسي فقط|الكود غير موجود بقاعدة البيانات السابقة",
            na=False,
        )
    ]
  elif current_filter == "فروقات الهاتف":
    df_display = df_display[df_display["الحالة"].str.contains("هاتف", na=False)]
  elif current_filter == "فروقات المدينة":
    df_display = df_display[df_display["الحالة"].str.contains("مدينة", na=False)]
  elif current_filter == "فروقات العنوان":
    df_display = df_display[df_display["الحالة"].str.contains("عنوان", na=False)]
  elif current_filter == "الرئيسي":
    df_display = df_display[
        df_display["الحالة"].str.contains("موجود في الرئيسي فقط", na=False)
    ]
  elif current_filter == "المقارنة":
    df_display = df_display[
        df_display["الحالة"].str.contains(
            "الكود غير موجود بقاعدة البيانات السابقة", na=False
        )
    ]

  if not df_display.empty:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
      df_display.to_excel(writer, index=False, sheet_name="الاختلافات")
    excel_data = output.getvalue()

    st.download_button(
        label="📥 تحميل جدول النتائج الحالي بصيغة Excel",
        data=excel_data,
        file_name=f"comparison_results_{current_filter}.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        use_container_width=True,
    )

    rows_html = ""
    for i, (_, row) in enumerate(df_display.iterrows(), 1):
      status_text = str(row["الحالة"]).strip()
      is_diff = "اختلاف" in status_text
      row_bg = "background-color: #faf5ff;" if is_diff else ""

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
