import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="مقارن ملفات الإكسل الذكي", page_icon="📊", layout="wide"
)

st.markdown(
    """
    <h2 style='text-align: center; color: #4F46E5;'>📊 أداة مقارنة البيانات بناءً على الكود حصراً</h2>
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

    # قائمة منسدلة واحدة فقط لاختيار عمود الكود المشترك
    common_cols = list(set(df_main.columns).intersection(set(df_new.columns)))
    default_id_idx = common_cols.index("الكود") if "الكود" in common_cols else 0

    id_col = st.selectbox(
        "🔑 اختر عمود الكود المشترك حصراً:", common_cols, index=default_id_idx
    )

    if st.button("🚀 ابدأ المقارنة وعرض الاختلافات فوراً", use_container_width=True):
      # البحث التلقائي الذكي عن أعمدة الهاتف والعنوان في الملفين
      def find_best_col(df, keywords):
        for col in df.columns:
          for kw in keywords:
            if kw in str(col).lower():
              return col
        return df.columns[1] if len(df.columns) > 1 else df.columns[0]

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

      # الدمج والمقارنة بناءً على عمود الكود المختار حصراً
      merged = pd.merge(
          m_df, n_df, on="id", how="inner", suffixes=("_main", "_new")
      )
      total_common = len(merged)

      merged["phone_diff"] = merged["phone_main"] != merged["phone_new"]
      merged["address_diff"] = merged["address_main"] != merged["address_new"]

      diff_df = merged[merged["phone_diff"] | merged["address_diff"]].copy()
      matched_count = total_common - len(diff_df)

      st.success("تمت المقارنة بنجاح بناءً على عمود الكود حصراً!")

      col1, col2, col3 = st.columns(3)
      col1.metric("📦 إجمالي الأكواد المشتركة", total_common)
      col2.metric("✅ الأكواد المتطابقة تماماً", matched_count)
      col3.metric("⚠️ الأكواد التي بها اختلافات", len(diff_df))

      st.markdown("---")

      if len(diff_df) > 0:
        st.subheader("📋 قائمة السجلات المختلفة بين الملفين:")
        for _, row in diff_df.iterrows():
          st.info(f"📌 **الكود:** `{row['id']}`")

          c1, c2 = st.columns(2)
          with c1:
            st.markdown(f"**📞 الهاتف (الرئيسي):** `{row['phone_main'] or 'فارغ'}`")
            p_stat = (
                "🟢 متطابق"
                if row["phone_main"] == row["phone_new"]
                else "🔴 مختلف"
            )
            st.markdown(
                f"**📞 الهاتف (الجديد):** `{row['phone_new'] or 'فارغ'}` ({p_stat})"
            )
          with c2:
            st.markdown(
                f"**📍 العنوان (الرئيسي):** {row['address_main'] or 'فارغ'}"
            )
            a_stat = (
                "🟢 متطابق"
                if row['address_main'] == row['address_new']
                else "🔴 مختلف"
            )
            st.markdown(
                f"**📍 العنوان (الجديد):** {row['address_new'] or 'فارغ'} ({a_stat})"
            )
          st.markdown("---")

        csv = diff_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="📥 تحميل تقرير الاختلافات كملف CSV",
            data=csv,
            file_name="differences_report.csv",
            mime="text/csv",
        )
      else:
        st.info("لا توجد أي اختلافات بين الملفين، جميع البيانات مطابقة تماماً!")

  except Exception as e:
    st.error(f"حدث خطأ أثناء معالجة الملفات: {e}")
