import pandas as pd
import streamlit as st

st.set_page_config(page_title="مقارن ملفات الإكسل", layout="wide")

st.title("📊 أداة مقارنة بيانات العناوين وأرقام الهواتف")

uploaded_main = st.file_uploader("📁 ارفع الملف الرئيسي (Master File)", type=["xlsx", "xls"])
uploaded_new = st.file_uploader("📁 ارفع الملف المراد مقارنته (New File)", type=["xlsx", "xls"])

if uploaded_main and uploaded_new:
    @st.cache_data
    def load_data(file1, file2):
        df1 = pd.read_excel(file1)
        df2 = pd.read_excel(file2)
        df1.columns = df1.columns.astype(str).str.strip()
        df2.columns = df2.columns.astype(str).str.strip()
        return df1, df2

    df_main, df_new = load_data(uploaded_main, uploaded_new)
    
    st.markdown("## ⚙️ إعدادات المقارنة")
    
    all_columns = sorted(list(set(df_main.columns) | set(df_new.columns)))
    
    id_col = st.selectbox("🔑 اختر العمود المعرّف المشترك:", all_columns, key="id_column")
    phone_col = st.selectbox("📞 اختر عمود رقم الهاتف:", all_columns, key="phone_column")
    address_col = st.selectbox("📍 اختر عمود العنوان:", all_columns, key="address_column")
    
    if st.button("🚀 ابدأ المقارنة والتحليل"):
        try:
            # دمج الملفين بناءً على المعرف المشترك
            df_comp = pd.merge(df_main, df_new, on=id_col, suffixes=('_الرئيسي', '_الجديد'))
            
            p_main = f"{phone_col}_الرئيسي"
            p_new = f"{phone_col}_الجديد"
            a_main = f"{address_col}_الرئيسي"
            a_new = f"{address_col}_الجديد"
            
            # التحقق من وجود الأعمدة بعد الدمج وإيجاد الاختلافات
            if p_main in df_comp.columns and p_new in df_comp.columns:
                df_comp['اختلاف_الهاتف'] = df_comp[p_main].astype(str).str.strip() != df_comp[p_new].astype(str).str.strip()
            else:
                df_comp['اختلاف_الهاتف'] = False
                
            if a_main in df_comp.columns and a_new in df_comp.columns:
                df_comp['اختلاف_العنوان'] = df_comp[a_main].astype(str).str.strip() != df_comp[a_new].astype(str).str.strip()
            else:
                df_comp['اختلاف_العنوان'] = False
                
            df_comp['يوجد_اختلاف'] = df_comp['اختلاف_الهاتف'] | df_comp['اختلاف_العنوان']
            
            total_records = len(df_comp)
            diff_df = df_comp[df_comp['يوجد_اختلاف']]
            diff_count = len(diff_df)
            match_count = total_records - diff_count
            
            st.success("تمت المقارنة بنجاح!")
            
            # المربعات الإحصائية العلوية
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("📦 إجمالي السجلات المشتركة", total_records)
            with c2:
                st.metric("✅ السجلات المتطابقة تماماً", match_count)
            with c3:
                st.metric("⚠️ السجلات التي بها اختلافات", diff_count)
            
            st.markdown("---")
            
            # جدول واضح يظهر التغييرات بوضوح (القديم مقابل الجديد)
            st.subheader("🔍 جدول الاختلافات بين الملفين:")
            if diff_count > 0:
                # تنظيم الأعمدة المعروضة لتكون واضحة (المعرف، الهاتف القديم والجديد، العنوان القديم والجديد)
                display_columns = [id_col]
                if p_main in df_comp.columns: display_columns.extend([p_main, p_new])
                if a_main in df_comp.columns: display_columns.extend([a_main, a_new])
                
                st.dataframe(diff_df[display_columns], use_container_width=True)
            else:
                st.info("لا توجد أي اختلافات بين الملفين، جميع البيانات مطابقة تماماً!")
                
        except Exception as e:
            st.error(f"حدث خطأ أثناء المعالجة: {e}")
