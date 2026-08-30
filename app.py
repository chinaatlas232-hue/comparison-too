import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="مقارن ملفات الإكسل الذكي", page_icon="📊", layout="wide"
)

st.markdown(
    """
    <h2 style='text-align: center; color: #4F46E5;'>📊 أداة مقارنة بيانات العناوين وأرقام الهواتف الذكية</h2>
    """,
    unsafe_allow_html=True,
)

# رفع الملفات
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
    st.subheader("⚙️ إعدادات الأعمدة الأساسية للمقارنة")

    col_a, col_b, col_c = st.columns(3)

    common_cols = list(set(df_main.columns).intersection(set(df_new.columns)))

    with col_a:
      default_id_idx = (
          common_cols.index("الكود") if "الكود" in common_cols else 0
      )
      id_col = st.selectbox(
          "🔑 العمود المعرّف المشترك:",
          common_cols,
          index=default_id_idx,
          key="id_col_select",
      )

    with col_b:
      p_main = st.selectbox(
          "📞 عمود الهاتف (الرئيسي):",
          list(df_main.columns),
          index=0,
          key="p_main_select",
      )
      p_new = st.selectbox(
          "📞 عمود الهاتف (الجديد):",
          list(df_new.columns),
          index=0,
          key="p_new_select",
      )

    with col_c:
      a_main = st.selectbox(
          "📍 عمود العنوان (الرئيسي):",
          list(df_main.columns),
          index=0,
          key="a_main_select",
      )
      a_new = st.selectbox(
          "📍 عمود العنوان (الجديد):",
          list(df_new.columns),
          index=0,
          key="a_new_select",
      )

    if st.button("🚀 ابدأ المقارنة والتحليل", use_container_width=True):
      m_df = df_main[[id_col, p_main, a_main]].copy()
      n_df = df_new[[id_col, p_new, a_new]].copy()

      m_df.columns = ["id", "phone", "address"]
      n_df.columns = ["id", "phone", "address"]

      m_df["id"] = m_df["id"].astype(str).str.strip()
      n_df["id"] = n_df["id"].astype(str).str.strip()
      m_df["phone"] = m_df["phone"].astype(str).str.strip().fillna("")
      n_df["phone"] = n_df["phone"].astype(str).str.strip().fillna("")
      m_df["address"] = m_df["address"].astype(str).str.strip().fillna("")
      n_df["address"] = n_df["address"].astype(str).str.strip().fillna("")

      merged = pd.merge(
          m_df, n_df, on="id", how="inner", suffixes=("_main", "_new")
      )

      total_common = len(merged)

      merged["phone_diff"] = merged["phone_main"] != merged["phone_new"]
      merged["address_diff"] = merged["address_main"] != merged["address_new"]

      diff_df = merged[merged["phone_diff"] | merged["address_diff"]].copy()
      matched_count = total_common - len(diff_df)

      st.success("تمت المقارنة بنجاح!")

      col1, col2, col3 = st.columns(3)
      col1.metric("📦 إجمالي السجلات المشتركة", total_common)
      col2.metric("✅ السجلات المتطابقة تماماً", matched_count)
      col3.metric("⚠️ السجلات التي بها اختلافات", len(diff_df))

      st.markdown("---")
      st.subheader("🔍 جدول الاختلافات مع فلتر بحث واحد:")

      if len(diff_df) > 0:
        display_diff = diff_df[
            ["id", "phone_main", "phone_new", "address_main", "address_new"]
        ].copy()
        display_diff.columns = [
            "الكود المشترك",
            "الهاتف (الرئيسي)",
            "الهاتف (الجديد)",
            "العنوان (الرئيسي)",
            "العنوان (الجديد)",
        ]

        # فلتر بحث واحد فقط يبحث في جميع الأعمدة المعروضة
        search_query = st.text_input(
            "🔎 ابحث برقم الكود، الهاتف، أو العنوان:",
            "",
            placeholder="اكتب هنا للبحث الفوري...",
        )

        if search_query:
          mask = display_diff.astype(str).apply(
              lambda x: x.str.contains(search_query, case=False, na=False)
          ).any(axis=1)
          display_diff = display_diff[mask]

        st.dataframe(display_diff, use_container_width=True)

        csv = display_diff.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="📥 تحميل تقارير الاختلافات المصفاة كملف CSV",
            data=csv,
            file_name="filtered_differences_report.csv",
            mime="text/csv",
        )
      else:
        st.info("لا توجد أي اختلافات بين الملفين، جميع البيانات مطابقة تماماً!")

  except Exception as e:
    st.error(f"حدث خطأ أثناء معالجة الملفات: {e}")
