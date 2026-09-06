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
FIXED_GOOGLE_SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/1UQG8zRhSiCUPogSZHvWPVgJPCe0OH-1k/edit"
)

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


    # دالة ذكية للتعرف على عمود الكود بالبحث عن قيم تببأ بحرف ورقم (مثل K564 أو E830)
    def get_smart_code_col(df):
      for col in df.columns:
        sample_vals = df[col].astype(str).str.upper()
        if sample_vals.str.contains(r"^[A-Z]\d+", regex=True).any():
          return col
      for kw in [
          "كود",
          "code",
          "id",
          "رقم العميل",
          "الرقم",
          "معرف",
          "رمز",
          "customer",
      ]:
        for col in df.columns:
          if kw in str(col).lower():
            return col
      return df.columns[0]


    code_col_m = get_smart_code_col(df_main)
    code_col_s = get_smart_code_col(df_sub)

    df_m = df_main.copy()
    df_s = df_sub.copy()

    df_m.rename(columns={code_col_m: "unified_id"}, inplace=True)
    df_s.rename(columns={code_col_s: "unified_id"}, inplace=True)


    def clean_id_series(series):
      if series is None:
        return pd.Series([""] * len(series))
      s = (
          series.astype(str)
          .str.replace(r"\.0$", "", regex=True)
          .str.strip()
          .str.upper()
          .fillna("")
      )
      return s.replace(["NAN", "NONE", "NAT", ""], "")


    df_m["clean_id"] = clean_id_series(df_m["unified_id"])
    df_s["clean_id"] = clean_id_series(df_s["unified_id"])

    df_m = df_m[
        (df_m["clean_id"] != "")
        & (df_m["clean_id"] != "NAN")
        & (df_m["clean_id"].notna())
    ]
    df_s = df_s[
        (df_s["clean_id"] != "")
        & (df_s["clean_id"] != "NAN")
        & (df_s["clean_id"].notna())
    ]

    c_main = len(df_m["clean_id"].unique())
    c_sub_file = len(df_s["clean_id"].unique())

    df_m = df_m.drop_duplicates(subset=["clean_id"], keep="last")
    df_s = df_s.drop_duplicates(subset=["clean_id"], keep="last")


    # دالة مطابقة الأعمدة بمرونة عالية
    def find_matching_cols(cols_m, cols_s, keywords):
      matched_pairs = []
      used_s = set()
      for cm in cols_m:
        if cm in ["unified_id", "clean_id"]:
          continue
        cm_low = str(cm).lower()
        if any(kw in cm_low for kw in keywords):
          best_match = None
          for cs in cols_s:
            if cs in ["unified_id", "clean_id"] or cs in used_s:
              continue
            cs_low = str(cs).lower()
            if any(kw in cs_low for kw in keywords):
              best_match = cs
              break
          if not best_match:
            if cm in cols_s and cm not in used_s:
              best_match = cm
          if best_match:
            used_s.add(best_match)
            matched_pairs.append((cm, best_match))

      # إذا لم يجد عبر الكلمات المفتاحية، اربط الأعمدة المتطابقة في الاسم تماماً
      if not matched_pairs:
        common = set(cols_m).intersection(set(cols_s))
        for c in common:
          if c not in ["unified_id", "clean_id"]:
            matched_pairs.append((c, c))

      return matched_pairs


    phone_keywords = ["هاتف", "رقم", "phone", "jawwal", "موبايل", "mobile"]
    city_keywords = ["مدين", "city", "محافظ", "منطق", "area", "province"]
    address_keywords = ["عنوان", "address", "سكن", "استلام", "شارع", "location"]

    phone_pairs = find_matching_cols(df_m.columns, df_s.columns, phone_keywords)
    city_pairs = find_matching_cols(df_m.columns, df_s.columns, city_keywords)
    address_pairs = find_matching_cols(
        df_m.columns, df_s.columns, address_keywords
    )

    # إذا كانت الأعمدة لم تُكتشف بالطريقة التقليدية، قم بربط جميع الأعمدة النصية المشتركة تلقائياً للمقارنة الشاملة
    if not address_pairs and not city_pairs and not phone_pairs:
      all_common = set(df_m.columns).intersection(set(df_s.columns))
      for c in all_common:
        if c not in ["unified_id", "clean_id"]:
          address_pairs.append((c, c))


    def clean_val(series, is_phone=False):
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
        s = (
            s.str.replace(r"\s+", " ", regex=True)
            .str.strip()
            .str.upper()
        )
      return s


    for cm, cs in phone_pairs:
      df_m[f"cl_{cm}"] = clean_val(df_m[cm], is_phone=True)
      df_s[f"cl_{cs}"] = clean_val(df_s[cs], is_phone=True)

    for cm, cs in city_pairs + address_pairs:
      df_m[f"cl_{cm}"] = clean_val(df_m[cm], is_phone=False)
      df_s[f"cl_{cs}"] = clean_val(df_s[cs], is_phone=False)

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

        for cm, cs in phone_pairs:
          if row.get(f"cl_{cm}_x", "") != row.get(f"cl_{cs}_y", ""):
            has_p_diff = True
        for cm, cs in city_pairs:
          if row.get(f"cl_{cm}_x", "") != row.get(f"cl_{cs}_y", ""):
            has_ci_diff = True
        for cm, cs in address_pairs:
          if row.get(f"cl_{cm}_x", "") != row.get(f"cl_{cs}_y", ""):
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
          for cm, cs in phone_pairs:
            record[f"{cm} (الرئيسي - أطلس)"] = row.get(f"{cm}_x", "")
            record[f"{cs} (المقارنة - الفرعي)"] = row.get(f"{cs}_y", "")
          for cm, cs in city_pairs:
            record[f"{cm} (الرئيسي - أطلس)"] = row.get(f"{cm}_x", "")
            record[f"{cs} (المقارنة - الفرعي)"] = row.get(f"{cs}_y", "")
          for cm, cs in address_pairs:
            record[f"{cm} (الرئيسي - أطلس)"] = row.get(f"{cm}_x", "")
            record[f"{cs} (المقارنة - الفرعي)"] = row.get(f"{cs}_y", "")

          record["الحالة"] = "اختلاف " + " و ".join(diff_labels)
          diff_records.append(record)

      elif merge_status == "left_only":
        code_diff_count += 1
        record = {"الكود": idx}
        for cm, cs in phone_pairs + city_pairs + address_pairs:
          record[f"{cm} (الرئيسي - أطلس)"] = row.get(f"{cm}_x", "")
          record[f"{cs} (المقارنة - الفرعي)"] = "غير موجود"
        record["الحالة"] = "موجود في أطلس فقط"
        diff_records.append(record)

      elif merge_status == "right_only":
        code_diff_count += 1
        record = {"الكود": idx}
        for cm, cs in phone_pairs + city_pairs + address_pairs:
          record[f"{cm} (الرئيسي - أطلس)"] = "غير موجود"
          record[f"{cs} (المقارنة - الفرعي)"] = row.get(f"{cs}_y", "")
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

    # خانة توضيحية لمعرفة الأعمدة التي تم اكتشافها لضمان الشفافية التامة
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔍 تقرير فحص الأعمدة المكتشفة")
    st.sidebar.write(f"**عمود الكود بأطلس:** `{code_col_m}`")
    st.sidebar.write(f"**عمود الكود بالفرعي:** `{code_col_s}`")
    st.sidebar.write(f"**أعمدة العناوين المقارنة:** {len(address_pairs)}")

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
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
      df_display.to_excel(writer, index=False, sheet_name="الاختلافات")
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
    cols_to_show = list(df_display.columns)
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
          if any(w in col_name for w in ["هاتف", "رقم", "phone"]):
            cell_style += " background-color: #ffedd5 !important; color: #c2410c;"
          elif any(w in col_name for w in ["مدين", "city", "محافظ"]):
            cell_style += " background-color: #dcfce7 !important; color: #15803d;"
          elif any(w in col_name for w in ["عنوان", "address", "سكن", "استلام"]):
            cell_style += " background-color: #fef9c3 !important; color: #a16207;"

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
      "يرجى التأكد من رفع ملف المقارنة الفرعي (coustmer info 2) في الشريط الجانبي"
      " لتبدأ المقارنة تلقائياً مع ملف أطلس الرئيسي."
  )
