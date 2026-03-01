import streamlit as st
import database as db
import utils
import views  # 导入视图层


def main():
    # 1. 初始化数据库
    db.init_db()

    # 2. 页面基础配置
    st.set_page_config("调查监测二分院项目管理系统", layout="wide")

    # 3. 登录与权限控制
    if 'user' not in st.session_state:
        if 'logged_in' not in st.session_state: st.session_state.logged_in = False
        if not st.session_state.logged_in:
            st.title("🔐 系统登录")
            u = st.text_input("账号")
            p = st.text_input("密码", type="password")
            if st.button("登录"):
                user = utils.check_login(u, p)
                if user:
                    st.session_state.user = user
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("账号或密码错误")
    else:
        # 4. 已登录：显示侧边栏和主页面
        user = st.session_state.user
        with st.sidebar:
            st.write(f"👤 当前用户：**{user['姓名']}**")
            if st.button("退出登录"):
                del st.session_state.user
                st.session_state.logged_in = False
                st.rerun()

        # 5. 根据角色生成菜单
        role = user['系统角色']
        menu = ["首页"]
        if role == '总管理账号':
            menu.append("领导管理")
        elif role == '部门领导':
            menu.extend(["人员管理", "项目管理", "请假管理", "人员考勤"])
        elif role == '本部门作业员':
            # 检查是否是项目负责人
            is_leader = db.query_df(
                f"SELECT 1 FROM 项目人员关联表 WHERE 用户ID={user['用户ID']} AND 项目角色 IN ('项目负责人', '技术负责人', '质量负责人')")
            if not is_leader.empty: menu.append("我的任务"); menu.append("人员考勤")
            menu.append("请假管理")
        elif role == '公司作业员':
            is_leader = db.query_df(
                f"SELECT 1 FROM 项目人员关联表 WHERE 用户ID={user['用户ID']} AND 项目角色 IN ('项目负责人', '技术负责人', '质量负责人')")
            if not is_leader.empty: menu.append("我的任务"); menu.append("人员考勤")
            # 检查是否是公司负责人
            is_comp_leader = db.query_df(
                f"SELECT 1 FROM 项目人员关联表 WHERE 用户ID={user['用户ID']} AND 项目角色='公司负责人'")
            if not is_comp_leader.empty: menu.append("公司作业进度")
            menu.append("请假管理")

        choice = st.sidebar.radio("功能菜单", menu)
        st.title(choice)

        # 6. 页面路由分发
        if choice == "首页":
            views.view_home() if role in ['本部门作业员', '公司作业员'] else st.write("欢迎进入管理系统")
        elif choice == "领导管理":
            views.view_management("领导管理", "部门领导")
        elif choice == "人员管理":
            views.view_personnel_management()
        elif choice == "项目管理":
            views.view_projects()
        elif choice == "我的任务":
            views.view_my_project()
        elif choice == "公司作业进度":
            views.view_company_progress()
        elif choice == "请假管理":
            views.view_leave_management()
        elif choice == "人员考勤":
            views.view_attendance()


if __name__ == '__main__':
    main()
