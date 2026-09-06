import io
import os
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="قاعدة بيانات عملاء أطلس", page_icon="📊", layout="wide"
)

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
    .custom-card {
        border-radius: 10px !important;
        padding: 14px 10px !important;
        text-align: center !important;
        cursor: pointer !important;
        text-decoration: none !important;
        display: block !important;
        transition: transform 0.15s ease, box-shadow 0.15s ease !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.08) !important;
    }
    .custom-card:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 6px 12px rgba(0,0,0,0.15) !important;
    }
    .card-city { background-color: #dcfce7 !important; border: 1px solid #22c55e !important; color: #15803d !important; }
    .card-addr { background-color: #fef9c3 !important; border: 1px solid #eab308 !important; color: #a16207 !important; }
    .card-phone { background-color: #ffedd5 !important; border: 1px solid #f97316 !important; color: #c2410c !important; }
    .card-code { background-color: #dbeafe !important; border: 1px solid #3b82f6 !important; color: #1d4ed8 !important; }
    .card-diff { background-color: #fee2e2 !important; border: 1px solid #ef4444 !important; color: #b91c1c !important; }
    .card-new { background-color: #f3e8ff !important; border: 1px solid #a855f7 !important; color: #7e22ce !important; }
    .card-main { background-color: #f3f4f6 !important; border: 1px solid #6b7280 !important; color: #374151 !important; }

    .card-title {
        font-size: 14px !important;
        font-weight: bold !important;
        margin-bottom: 6px !important;
    }
    .card-value {
        font-size: 18px !important;
        font-weight: bold !important;
    }
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

sub_file_path = os.path.join(UPLOAD_DIR, "coustmer info 2.xlsx")
FIXED_GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1UQG8zRhSiCUPogSZHvWPVgJPCe0OH-1k/edit"

with st.sidebar:
  st.markdown("### 📁 إدارة الملفات والروابط")

  uploaded_sub = st.file_uploader(
      "ملف المقارنة الفرعي (coustmer info 2)",
      type=["xlsx", "xls"],
  )
  if uploaded_sub is not None:
    if os.path.exists(sub_file_path):
      os.remove(sub_file_path)
    with open(sub_file_path, "wb") as f:
      f.write(uploaded_sub.getbuffer())

  st.markdown("---")
  st.info(
      "🔗 تم اعتماد 'قاعدة بيانات عملاء أطلس' (Google Sheets) كملف رئيسي"
      " للمقارنة بنجاح."
  )

  st.markdown("---")
  st.markdown("### ⚙️ إعدادات التحكم")

  if st.button(
      "🗑️ مسح الملفات وإعادة ضبط التطبيق",
      use_container_width=True,
      type="primary",
  ):
    if os.path.exists(sub_file_path):
      os.remove(sub_file_path)
    for key in list(st.session_state.keys()):
      del st.session_state[key]
    st.query_params.clear()
    st.rerun()

active_sub = (
    sub_file_path
    if os.path.exists(sub_file_path)
    else (uploaded_sub if uploaded_sub else None)
)

if "active_filter" not in st.session_state:
  st.session_state["active_filter"] = "الكل"

if "filter" in st.query_params:
  selected_f = st.query_params["filter"]
  if st.session_state["active_filter"] != selected_f:
    st.session_state["active_filter"] = selected_f
    st.rerun()


def load_google_sheet(url):
  try:
    if "docs.google.com/spreadsheets" in url:
      if "/edit" in url:
        export_url = url.split("/edit")[0] + "/export?format=xlsx"
      else:
        export_url = url + "/export?format=xlsx"
      df = pd.read_excel(export_url, sheet_name=0)
      df.columns = df.columns.astype(str).str.strip()
      return df
    return None
  except Exception as e:
    st.sidebar.error(f"تعذر جلب البيانات من Google Sheet: {e}")
    return None


c_main, c_sub_file, c_diff, c_code_diff, c_phone_diff, c_city_diff, (
    c_address_diff
) = (0, 0, 0, 0, 0, 0, 0)
diff_df = pd.DataFrame()

df_main = load_google_sheet(FIXED_GOOGLE_SHEET_URL)

if df_main is not None and active_sub is not None:
  try:
    df_sub = pd.read_excel(active_sub, sheet_name=0)
    df_sub.columns = df_sub.columns.astype(str).str.strip()
    df_main.columns = df_main.columns.astype(str).str.strip()

    common_cols = list(set(df_main.columns).intersection(set(df_sub.columns)))

    if not common_cols:
      st.error(
          "⚠️ لا توجد أعمدة مشتركة مطابقة بين الملف الرئيسي والملف الفرعي!"
          " يرجى التحقق من أسماء الأعمدة."
      )
    else:
      code_col = next(
          (
              c
              for c in common_cols
              if "كود" in str(c) or "code" in str(c).lower()
          ),
          None,
      )
      if not code_col:
        code_col = common_cols[0]

      def clean_series(series, is_phone=False):
        if series is None:
          return pd.Series([""] * len(series))
        s = (
            series.astype(str)
            .str.replace(r"\.0$", "", regex=True)
            .str.strip()
            .fillna("")
        )
        s = s.replace(["nan", "None", "NAT", "nat", ""], "")
        if is_phone:
          s = s.str.replace(r"\D", "", regex=True)
          s = s.str.replace(r"^00", "", regex=True)
        else:
          s = s.str.replace(r"\s+", " ", regex=True).str.strip()
        return s

      df_m = df_main.copy()
      df_s = df_sub.copy()

      df_m["clean_id"] = clean_series(df_m[code_col])
      df_s["clean_id"] = clean_series(df_s[code_col])

      df_m = df_m[
          (df_m["clean_id"] != "")
          & (df_m["clean_id"].str.lower() != "nan")
          & (df_m["clean_id"].notna())
      ]
      df_s = df_s[
          (df_s["clean_id"] != "")
          & (df_s["clean_id"].str.lower() != "nan")
          & (df_s["clean_id"].notna())
      ]

      c_main = len(df_m["clean_id"].unique())
      c_sub_file = len(df_s["clean_id"].unique())

      df_m = df_m.drop_duplicates(subset=["clean_id"], keep="last")
      df_s = df_s.drop_duplicates(subset=["clean_id"], keep="last")

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

      for c in phone_cols:
        df_m[f"cl_{c}"] = clean_series(df_m[c], is_phone=True)
        df_s[f"cl_{c}"] = clean_series(df_s[c], is_phone=True)

      for c in city_cols + address_cols:
        df_m[f"cl_{c}"] = clean_series(df_m[c], is_phone=False)
        df_s[f"cl_{c}"] = clean_series(df_s[c], is_phone=False)

      merged = pd.merge(
          df_m,
          df_s,
          on="clean_id",
          how="outer",
          suffixes=("_m", "_s"),
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
            if row.get(f"cl_{pc}_m", "") != row.get(f"cl_{pc}_s", ""):
              has_p_diff = True
          for cic in city_cols:
            if row.get(f"cl_{cic}_m", "") != row.get(f"cl_{cic}_s", ""):
              has_ci_diff = True
          for ac in address_cols:
            if row.get(f"cl_{ac}_m", "") != row.get(f"cl_{ac}_s", ""):
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
              record[f"{pc} (الرئيسي - أطلس)"] = row.get(f"{pc}_m", "")
              record[f"{pc} (المقارنة - الفرعي)"] = row.get(f"{pc}_s", "")
              record[f"cl_{pc}_m"] = row.get(f"cl_{pc}_m", "")
              record[f"cl_{pc}_s"] = row.get(f"cl_{pc}_s", "")
            for cic in city_cols:
              record[f"{cic} (الرئيسي - أطلس)"] = row.get(f"{cic}_m", "")
              record[f"{cic} (المقارنة - الفرعي)"] = row.get(f"{cic}_s", "")
              record[f"cl_{cic}_m"] = row.get(f"cl_{cic}_m", "")
              record[f"cl_{cic}_s"] = row.get(f"cl_{cic}_s", "")
            for ac in address_cols:
              record[f"{ac} (الرئيسي - أطلس)"] = row.get(f"{ac}_m", "")
              record[f"{ac} (المقارنة - الفرعي)"] = row.get(f"{ac}_s", "")
              record[f"cl_{ac}_m"] = row.get(f"cl_{ac}_m", "")
              record[f"cl_{ac}_s"] = row.get(f"cl_{ac}_s", "")

            record["الحالة"] = "اختلاف " + " و ".join(diff_labels)
            diff_records.append(record)

        elif merge_status == "left_only":
          code_diff_count += 1
          record = {"الكود": idx}
          for pc in phone_cols:
            record[f"{pc} (الرئيسي - أطلس)"] = row.get(f"{pc}_m", "")
            record[f"{pc} (المقارنة - الفرعي)"] = "غير موجود"
          for cic in city_cols:
            record[f"{cic} (الرئيسي - أطلس)"] = row.get(f"{cic}_m", "")
            record[f"{cic} (المقارنة - الفرعي)"] = "غير موجود"
          for ac in address_cols:
            record[f"{ac} (الرئيسي - أطلس)"] = row.get(f"{ac}_m", "")
            record[f"{ac} (المقارنة - الفرعي)"] = "غير موجود"
          record["الحالة"] = "موجود في أطلس فقط"
          diff_records.append(record)

        elif merge_status == "right_only":
          code_diff_count += 1
          record = {"الكود": idx}
          for pc in phone_cols:
            record[f"{pc} (الرئيسي - أطلس)"] = "غير موجود"
            record[f"{pc} (المقارنة - الفرعي)"] = row.get(f"{pc}_s", "")
          for cic in city_cols:
            record[f"{cic} (الرئيسي - أطلس)"] = "غير موجود"
            record[f"{cic} (المقارنة - الفرعي)"] = row.get(f"{cic}_s", "")
          for ac in address_cols:
            record[f"{ac} (الرئيسي - أطلس)"] = "غير موجود"
            record[f"{ac} (المقارنة - الفرعي)"] = row.get(f"{cic}_s", "")
          record["الحالة"] = "موجود في الملف الفرعي فقط (غير موجود بأطلس)"
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
      f"""<a href="?filter=الفرعي" target="_self" class="custom-card card-new">
        <div class="card-title">📁 الفرعي</div>
        <div class="card-value">{c_sub_file}</div>
    </a>""",
      unsafe_allow_html=True,
  )

with cols[6]:
  st.markdown(
      f"""<a href="?filter=أطلس الرئيسي" target="_self" class="custom-card card-main">
        <div class="card-title">📦 أطلس</div>
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
            "موجود في أطلس فقط|موجود في الملف الفرعي فقط", na=False
        )
    ]
  elif current_filter == "فروقات الهاتف":
    df_display = df_display[df_display["الحالة"].str.contains("هاتف", na=False)]
  elif current_filter == "فروقات المدينة":
    df_display = df_display[df_display["الحالة"].str.contains("مدينة", na=False)]
  elif current_filter == "فروقات العنوان":
    df_display = df_display[df_display["الحالة"].str.contains("عنوان", na=False)]
  elif current_filter == "أطلس الرئيسي":
    df_display = df_display[
        df_display["الحالة"].str.contains("موجود في أطلس فقط", na=False)
    ]
  elif current_filter == "الفرعي":
    df_display = df_display[
        df_display["الحالة"].str.contains(
            "موجود في الملف الفرعي فقط", na=False
        )
    ]

  if not df_display.empty:
    cols_to_show = [
        c for c in df_display.columns if not c.startswith("cl_")
    ]
    df_to_export = df_display[cols_to_show]

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
      df_to_export.to_excel(writer, index=False, sheet_name="الاختلافات")
    excel_data = output.getvalue()

    st.download_button(
        label="📥 تحميل جدول النتائج الحالي بصيغة Excel",
        data=excel_data,
        file_name=f"atlas_comparison_results_{current_filter}.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        use_container_width=True,
    )

    rows_html = ""
    for i, (_, row) in enumerate(df_display.iterrows(), 1):
      status_text = str(row["الحالة"]).strip()
      cells_html = f'<td style="padding: 10px; text-align: center; border-bottom: 1px solid #e5e7eb; font-size: 14px; font-weight: bold;">{i}</td>'

      for col_name in cols_to_show:
        val = row[col_name]
        cell_style = (
            "padding: 10px; text-align: center; border-bottom: 1px solid"
            " #e5e7eb; font-size: 14px;"
        )

        if col_name == "الحالة":
          cell_style += " background-color: #fee2e2 !important; color: #b91c1c; font-weight: bold;"
        elif col_name == "الكود":
          if (
              "موجود في أطلس فقط" in status_text
              or "موجود في الملف الفرعي فقط" in status_text
          ):
            cell_style += " background-color: #dbeafe !important; color: #1d4ed8; font-weight: bold;"
        else:
          if "(الرئيسي - أطلس)" in col_name:
            base_name = col_name.replace(" (الرئيسي - أطلس)", "").strip()
            val_m = row.get(f"cl_{base_name}_m", "")
            val_s = row.get(f"cl_{base_name}_s", "")
            if val_m != val_s:
              if any(w in col_name for w in ["هاتف", "رقم", "phone"]):
                cell_style += " background-color: #ffedd5 !important; color: #c2410c; font-weight: bold;"
              elif any(w in col_name for w in ["مدين", "city", "محافظ"]):
                cell_style += " background-color: #dcfce7 !important; color: #15803d; font-weight: bold;"
              elif any(w in col_name for w in ["عنوان", "address", "سكن", "استلام"]):
                cell_style += " background-color: #fef9c3 !important; color: #a16207; font-weight: bold;"

          elif "(المقارنة - الفرعي)" in col_name:
            base_name = col_name.replace(" (المقارنة - الفرعي)", "").strip()
            val_m = row.get(f"cl_{base_name}_m", "")
            val_s = row.get(f"cl_{base_name}_s", "")
            if val_m != val_s:
              if any(w in col_name for w in ["هاتف", "رقم", "phone"]):
                cell_style += " background-color: #ffedd5 !important; color: #c2410c; font-weight: bold;"
              elif any(w in col_name for w in ["مدين", "city", "محافظ"]):
                cell_style += " background-color: #dcfce7 !important; color: #15803d; font-weight: bold;"
              elif any(w in col_name for w in ["عنوان", "address", "سكن", "استلام"]):
                cell_style += " background-color: #fef9c3 !important; color: #a16207; font-weight: bold;"

        cells_html += f'<td style="{cell_style}">{val}</td>'

      rows_html += f"<tr>{cells_html}</tr>"

    columns_list = ["التسلسل"] + cols_to_show
    headers_html = "".join(
        f'<th style="background-color: #4f46e5; color: white; padding: 12px; text-align: center; font-size: 14px;">{col}</th>'
        for col in columns_list
    )

    final_table = f"""
        <style>
        table {{
            width: 100%;
            border-collapse: collapse;
            direction: rtl;
            font-family: sans-serif;
        }}
        th, td {{
            border: 1px solid #d1d5db;
        }}
        </style>
        <table>
            <thead><tr>{headers_html}</tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
        """

    st.markdown(final_table, unsafe_allow_html=True)
  else:
    st.info("لا توجد بيانات مطابقة لهذا الفلتر.")
else:
  st.info(
      "يرجى رفع ملف المقارنة الفرعي (coustmer info 2) في الشريط الجانبي، حيث"
      " تم جلب قاعدة بيانات عملاء أطلس كملف رئيسي تلقائياً."
  )
