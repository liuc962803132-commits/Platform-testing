import streamlit as st
import datetime

# 默认显示当天的日期
d = st.date_input("请选择日期", datetime.date.today())

st.write("你选择的日期是:", d)
# 输出格式类似于: 2023-10-27
