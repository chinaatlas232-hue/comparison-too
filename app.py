import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="مقارن ملفات الإكسل الذكي", page_icon="📊", layout="wide"
)

st.markdown(
    """
    <h2 style='text-align: center; color: #4F46E5;'>📊 أداة الاستعلام والمقارنة السريعة</h2>
    """,
    unsafe_allow_html=True,
)

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

    st.markdown("---")

    # فلتر واحد فقط لاختيار العمود المشترك (الكود)
    common_cols = list(set(df_main.columns).intersection(set(df_new.columns)))
    default_id_idx = common_cols.index("الكود") if "الكود" in common_cols else 0

    id_col = st.selectbox(
        "🔑 اختر عمود الكود المشترك:", common_cols, index=default_id_idx
    )

    if st.button("🚀 تجهيز البيانات للبحث السريع", use_container_width=True):
      def find_best_col(df, keywords):
        for col in df.columns:
          for kw in keywords:
            if kw in str(col).lower():
              return col
        return df.columns[1]

      phone_main = find_best_col(df_main, ["هاتف", "phone", "جوال", "رقم"])
      addr_main = find_best_col(
          df_main, ["عنوان", "address", "استلام", "البضاعة", "مكان"]
      )

      phone_new = (
          phone_main if phone_main in df_new.columns else df_new.columns[1]
      )
      addr_new = addr_main if addr_main in df_new.columns else df_new.columns[2]

      m_df = df_main[[id_col, phone_main, addr_main]].copy()
      n_df = df_new[[id_col, phone_new, addr_new]].copy()

      m_df.columns = ["id", "phone", "address"]
      n_df.columns = ["id", "phone", "address"]

      def clean_series(series):
        return (
            series.astype(str)
            .str.replace(r"\.0$", "", regex=True)
            .str.strip()
            .fillna("")
            .replace("nan", "")
        )

      m_df["id"] = clean_series(m_df["id"])
      n_df["id"] = clean_series(n_df["id"])
      m_df["phone"] = clean_series(m_df["phone"])
      n_df["phone"] = clean_series(n_df["phone"])
      m_df["address"] = clean_series(m_df["address"])
      n_df["address"] = clean_series(n_df["address"])

      # دمج الملفات وحفظها في الذاكرة المؤقتة للاستعلام الفوري
      st.session_state["merged_data"] = pd.merge(
          m_df, n_df, on="id", how="inner", suffixes=("_main", "_new")
      )
      st.success(
          "تم تجهيز البيانات بنجاح! يمكنك الآن البحث عن أي كود أو رقم هاتف أدناه."
      )

    # صندوق الاستعلام الفوري (البحث عن عنصر واحد وعرض نتيجته حصرياً)
    if "merged_data" in st.session_state:
      st.markdown("---")
      query = st.text_input(
          "🔍 أدخل الكود أو رقم الهاتف للبحث الفوري عنه:",
          placeholder="مثال: E824 أو رقم الهاتف...",
      )

      if query:
        data = st.session_state["merged_data"]
        # البحث في الكود أو الهاتف
        result = data[
            data["id"].str.contains(query, case=False, na=False)
            | data["phone_main"].str.contains(query, case=False, na=False)
            | data["phone_new"].str.contains(query, case=False, na=False)
        ]

        if not result.empty:
          for _, row in result.iterrows():
            st.info(f"📌 **نتيجة البحث للكود:** {row['id']}")

            col_p1, col_p2 = st.columns(2)
            with col_p1:
              st.markdown(
                  "**📞 الهاتف (الرئيسي):** "
                  f"`{row['phone_main'] or 'فارغ'}`"
              )
            with col_p2:
              phone_match_color = (
                  "🟢 متطابق"
                  if row["phone_main"] == row["phone_new"]
                  else "🔴 يوجد اختلاف"
              )
              st.markdown(
                  "**📞 الهاتف (الجديد):** "
                  f"`{row['phone_new'] or 'فارغ'}` ({phone_match_color})"
              )

            col_a1, col_a2 = st.columns(2)
            with col_a1:
              st.markdown(
                  "**📍 العنوان (الرئيسي):** "
                  f"{row['address_main'] or 'فارغ'}"
              )
            with col_a2:
              addr_match_color = (
                  "🟢 متطابق"
                  if row["address_main"] == row["address_new"]
                  else "🔴 يوجد اختلاف"
              )
              st.markdown(
                  "**📍 العنوان (الجديد):** "
                  f"{row['address_new'] or 'فارغ'} ({addr_match_color})"
              )
            st.markdown("---")
        else:
          st.warning("⚠️ لم يتم العثور على أي مطابقة بهذا الكود أو رقم الهاتف.")

  except Exception as e:
    st.error(f"حدث خطأ أثناء معالجة الملفات: {e}")
