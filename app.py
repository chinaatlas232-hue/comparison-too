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
    .card-city { background-color: rgba(34, 197, 94, 0.25); border: 1px solid rgba(34, 197, 94, 0.4); color: #15803d; }
    .card-addr { background-color: rgba(234, 179, 8, 0.25); border: 1px solid rgba(234, 179, 8, 0.4); color: #a16207; }
    .card-phone { background-color: rgba(249, 115, 22, 0.25); border: 1px solid rgba(249, 115, 22, 0.4); color: #c2410c; }
    .card-code { background-color: rgba(59, 130, 246, 0.25); border: 1px solid rgba(59, 130, 246, 0.4); color: #1d4ed8; }
    .card-diff { background-color: rgba(239, 68, 68, 0.25); border: 1px solid rgba(239, 68, 68, 0.4); color: #b91c1c; }
    .card-new { background-color: rgba(168, 85, 247, 0.25); border: 1px solid rgba(168, 85, 247, 0.4); color: #7e22ce; }
    .card-main { background-color: rgba(107, 114, 128, 0.25); border: 1px solid rgba(107, 114, 128, 0.4); color: #374151; }

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

if "filter" in st.query_params:
  selected_f = st.query_params["filter"]
  if st.session_state["active_filter"] != selected_f:
    st.session_state["active_filter"] = selected_f
    st.rerun()


@st.cache_data
def load_and_clean_data(file1, file2):
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
    df_main, df_new = load_and_clean_data(active_main, active_new)

    common_cols = list(set(df_main.columns).intersection(set(df_new.columns)))

    code_col = next(
        (c for c in common_cols if "كود" in str(c) or "code" in str(c).lower()),
        None,
    )
    if not code_col:
      code_col = common_cols[0]


    def clean_series(series):
      if series is None:
        return pd.Series([""] * len(series))
      return (
          series.astype(str)
          .str.replace(r"\.0$", "", regex=True)
          .str.strip()
          .fillna("")
          .replace(["nan", "None", "NAT", "nan"], "")
      )


    df_m = df_main.copy()
    df_n = df_new.copy()

    df_m["clean_id"] = clean_series(df_m[code_col])
    df_n["clean_id"] = clean_series(df_n[code_col])

    # تصفية الصقور الفارغة وغير الصالحة
    df_m = df_m[
        (df_m["clean_id"] != "")
        & (df_m["clean_id"].str.lower() != "nan")
        & (df_m["clean_id"].notna())
    ]
    df_n = df_n[
        (df_n["clean_id"] != "")
        & (df_n["clean_id"].str.lower() != "nan")
        & (df_n["clean_id"].notna())
    ]

    c_main = len(df_m["clean_id"].unique())
    c_new = len(df_n["clean_id"].unique())

    # إزالة التكرارات للأمان
    df_m = df_m.drop_duplicates(subset=["clean_id"], keep="last")
    df_n = df_n.drop_duplicates(subset=["clean_id"], keep="last")

    phone_cols = [
        c
        for c in common_cols
        if "هاتف" in str(c) or "رقم" in str(c) or "phone" in str(c).lower()
    ]
    city_cols = [
        c
        for c in common_cols
        if "مدين" in str(c) or "city" in str(c).lower() or "محافظ" in str(c)
    ]
    address_cols = [
        c
        for c in common_cols
        if "عنوان" in str(c)
        or "address" in str(c).lower()
        or "سكن" in str(c)
        or "استلام" in str(c)
    ]

    # تنظيف الأعمدة المعنية مسبقاً لتسريع المقارنة
    for c in phone_cols + city_cols + address_cols:
      df_m[f"cl_{c}"] = clean_series(df_m[c])
      df_n[f"cl_{c}"] = clean_series(df_n[c])

    # دمج البيانات عبر الـ Merge السريع جداً (Vectorized Merge)
    merged = pd.merge(
        df_m,
        df_n,
        on="clean_id",
        how="outer",
        suffixes=("_m", "_n"),
        indicator=True,
    )

    diff_records = []
    code_diff_count = 0
    phone_diff_count = 0
    city_diff_count = 0
    address_diff_count = 0

    for _, row in merged.iterrows():
      idx = row["clean_id"]
      merge_status = row["_merge"]

      if merge_status == "both":
        has_p_diff, has_ci_diff, has_a_diff = False, False, False

        for pc in phone_cols:
          if row.get(f"cl_{pc}_m", "") != row.get(f"cl_{pc}_n", ""):
            has_p_diff = True
        for cic in city_cols:
          if row.get(f"cl_{cic}_m", "") != row.get(f"cl_{cic}_n", ""):
            has_ci_diff = True
        for ac in address_cols:
          if row.get(f"cl_{ac}_m", "") != row.get(f"cl_{ac}_n", ""):
            has_a_diff = True

        if has_p_diff or has_ci_diff or has_a_diff:
          if has_p_diff:
            phone_diff_count += 1
          if has_ci_diff:
            city_diff_count += 1
          if has_a_diff:
            address_diff_count += 1

          diff_labels = []
          if has_p_diff:
            diff_labels.append("هاتف")
          if has_ci_diff:
            diff_labels.append("مدينة")
          if has_a_diff:
            diff_labels.append("عنوان")

          record = {"الكود": idx}
          for pc in phone_cols:
            record[f"{pc} (الرئيسي)"] = row.get(f"{pc}_m", "")
            record[f"{pc} (المقارنة)"] = row.get(f"{pc}_n", "")
          for cic in city_cols:
            record[f"{cic} (الرئيسي)"] = row.get(f"{cic}_m", "")
            record[f"{cic} (المقارنة)"] = row.get(f"{cic}_n", "")
          for ac in address_cols:
            record[f"{ac} (الرئيسي)"] = row.get(f"{ac}_m", "")
            record[f"{ac} (المقارنة)"] = row.get(f"{ac}_n", "")

          record["الحالة"] = "اختلاف " + " و ".join(diff_labels)
          diff_records.append(record)

      elif merge_status == "left_only":
        code_diff_count += 1
        record = {"الكود": idx}
        for pc in phone_cols:
          record[f"{pc} (الرئيسي)"] = row.get(f"{pc}_m", "")
          record[f"{pc} (المقارنة)"] = "غير موجود"
        for cic in city_cols:
          record[f"{cic} (الرئيسي)"] = row.get(f"{cic}_m", "")
          record[f"{cic} (المقارنة)"] = "غير موجود"
        for ac in address_cols:
          record[f"{ac} (الرئيسي)"] = row.get(f"{ac}_m", "")
          record[f"{ac} (المقارنة)"] = "غير موجود"
        record["الحالة"] = "موجود في الرئيسي فقط"
        diff_records.append(record)

      elif merge_status == "right_only":
        code_diff_count += 1
        record = {"الكود": idx}
        for pc in phone_cols:
          record[f"{pc} (الرئيسي)"] = "غير موجود"
          record[f"{pc} (المقارنة)"] = row.get(f"{pc}_n", "")
        for cic in city_cols:
          record[f"{cic} (الرئيسي)"] = "غير موجود"
          record[f"{cic} (المقارنة)"] = row.get(f"{cic}_n", "")
        for ac in address_cols:
          record[f"{ac} (الرئيسي)"] = "غير موجود"
          record[f"{ac} (المقارنة)"] = row.get(f"{ac}_n", "")
        record["الحالة"] = "الكود غير موجود بقاعدة البيانات السابقة"
        diff_records.append(record)

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
      f"""<a href="?filter=فروقات المدينة" target="_self" class="custom-card card-city">
        <div class="card-title">🏙️ المدينة</div>
        <div class="card-value">{c_city_diff}</div>
    </a>""",
      unsafe_allow_html=True,
  )

with cols[1]:
  st.markdown(
      f"""<a href="?filter=فروقات العنوان" target="_self" class="custom-card card-addr">
        <div class="card-title">🏠 العنوان</div>
        <div class="card-value">{c_address_diff}</div>
    </a>""",
      unsafe_allow_html=True,
  )

with cols[2]:
  st.markdown(
      f"""<a href="?filter=فروقات الهاتف" target="_self" class="custom-card card-phone">
        <div class="card-title">📞 الهاتف</div>
        <div class="card-value">{c_phone_diff}</div>
    </a>""",
      unsafe_allow_html=True,
  )

with cols[3]:
  st.markdown(
      f"""<a href="?filter=فروقات الكود" target="_self" class="custom-card card-code">
        <div class="card-title">🔑 الكود</div>
        <div class="card-value">{c_code_diff}</div>
    </a>""",
      unsafe_allow_html=True,
  )

with cols[4]:
  st.markdown(
      f"""<a href="?filter=الكل" target="_self" class="custom-card card-diff">
        <div class="card-title">⚠️ الإجمالي</div>
        <div class="card-value">{c_diff}</div>
    </a>""",
      unsafe_allow_html=True,
  )

with cols[5]:
  st.markdown(
      f"""<a href="?filter=المقارنة" target="_self" class="custom-card card-new">
        <div class="card-title">📁 المقارنة</div>
        <div class="card-value">{c_new}</div>
    </a>""",
      unsafe_allow_html=True,
  )

with cols[6]:
  st.markdown(
      f"""<a href="?filter=الرئيسي" target="_self" class="custom-card card-main">
        <div class="card-title">📦 الرئيسي</div>
        <div class="card-value">{c_main}</div>
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
