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
    st.subheader("⚙️ اختر الأعمدة المطابقة لملفاتك:")

    common_cols = list(set(df_main.columns).intersection(set(df_new.columns)))

    col_a, col_b, col_c = st.columns(3)

    with col_a:
      id_col = st.selectbox("🔑 عمود الكود المشترك:", common_cols)

    with col_b:
      # عرض أعمدة الملفات لتختار عمود الهاتف بحرية
      phone_col = st.selectbox("📞 عمود الهاتف:", list(df_main.columns))

    with col_c:
      # عرض أعمدة الملفات لتختار عمود العنوان بحرية
      addr_col = st.selectbox("📍 عمود العنوان:", list(df_main.columns))

    if st.button("🚀 ابدأ المقارنة والتحليل الفوري", use_container_width=True):
      # استخدام الأعمدة المحددة من المستخدم
      m_df = df_main[[id_col, phone_col, addr_col]].copy()
      
      # محاولة إيجاد نفس أسماء الأعمدة أو مطابقتها في الملف الجديد
      n_phone_col = phone_col if phone_col in df_new.columns else df_new.columns[1]
      n_addr_col = addr_col if addr_col in df_new.columns else df_new.columns[2]
      
      n_df = df_new[[id_col, n_phone_col, n_addr_col]].copy()

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
      st.subheader("🔍 جدول الاختلافات (مع شريط بحث واحد):")

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

        search_query = st.text_input(
            "🔎 ابحث هنا (بالكود، الهاتف، أو العنوان):"
        )
        if search_query:
          mask = display_diff.astype(str).apply(
              lambda x: x.str.contains(search_query, case=False, na=False)
          ).any(axis=1)
          display_diff = display_diff[mask]

        st.dataframe(display_diff, use_container_width=True)

        csv = display_diff.to_csv(index=False).encode("utf-8-sig")
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
