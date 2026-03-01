import streamlit as st
import pandas as pd
from datetime import date, timedelta
import io
import uuid
import database as db
import utils


# ===========================
# 1. 领导管理 & 人员管理
# ===========================
def view_management(title, role_filter):
    st.subheader(title)
    df = db.query_df(f"SELECT 用户ID, 姓名, 密码, 账号状态 FROM 用户信息表 WHERE 系统角色='{role_filter}'")
    with st.expander(f"➕ 添加{title}"):
        c1, c2 = st.columns(2)
        name = c1.text_input("姓名", key=f"name_{role_filter}_mgmt")
        pwd = c2.text_input("密码", "123456", key=f"pwd_{role_filter}_mgmt")
        if st.button("添加", key=f"btn_{role_filter}_mgmt"):
            if name:
                try:
                    db.run_sql("INSERT INTO 用户信息表 (姓名, 密码, 系统角色, 账号状态) VALUES (?, ?, ?, '在职')",
                               (name, pwd, role_filter))
                    st.success("成功");
                    st.rerun()
                except Exception as e:
                    st.error(f"添加失败：{e}")
    if df.empty: return
    df = utils.add_idx(df)
    cfg = {"用户ID": None, "密码": st.column_config.TextColumn("密码"),
           "账号状态": st.column_config.SelectboxColumn("状态", options=["在职", "离职"])}
    ed = st.data_editor(df, column_config=cfg, key=f"ed_{role_filter}_mgmt", hide_index=True)
    if st.button("保存", key=f"save_{role_filter}_mgmt", type="primary"):
        for i, r in ed.iterrows():
            o = df[df['用户ID'] == r['用户ID']].iloc[0]
            if r['密码'] != o['密码'] or r['账号状态'] != o['账号状态']:
                resign_date = None
                if r['账号状态'] == '离职': resign_date = date.today().isoformat()
                db.run_sql("UPDATE 用户信息表 SET 密码=?, 账号状态=?, 离职时间=? WHERE 用户ID=?",
                           (r['密码'], r['账号状态'], resign_date, r['用户ID']))
        st.rerun()


def view_personnel_management():
    st.subheader("人员管理")
    tab1, tab2 = st.tabs(["本部门人员", "公司人员"])

    with tab1:
        role_filter = '本部门作业员'
        df = db.query_df(
            f"SELECT 用户ID, 姓名, 密码, 人员性质, 账号状态 FROM 用户信息表 WHERE 系统角色='{role_filter}'")
        with st.expander(f"➕ 添加本部门人员"):
            c1, c2, c3 = st.columns(3)
            name = c1.text_input("姓名", key="name_local_final")
            pwd = c2.text_input("密码", "123456", key="pwd_local_final")
            prop = c3.selectbox("人员性质", ["在编", "劳务派遣"], key="prop_local_final")
            if st.button("添加", key="btn_local_final"):
                if name:
                    try:
                        leader_dept = st.session_state.user.get('所属部门', '')
                        db.run_sql(
                            "INSERT INTO 用户信息表 (姓名, 密码, 系统角色, 所属部门, 人员性质, 账号状态) VALUES (?, ?, ?, ?, ?, '在职')",
                            (name, pwd, role_filter, leader_dept, prop))
                        st.success("成功");
                        st.rerun()
                    except Exception as e:
                        st.error(f"添加失败：{e}")
        if not df.empty:
            df = utils.add_idx(df)
            cfg = {"用户ID": None, "密码": st.column_config.TextColumn("密码"),
                   "人员性质": st.column_config.SelectboxColumn("性质", options=["在编", "劳务派遣"]),
                   "账号状态": st.column_config.SelectboxColumn("状态", options=["在职", "离职"])}
            ed = st.data_editor(df, column_config=cfg, key="ed_local_final", hide_index=True)
            if st.button("保存修改", key="save_local_final", type="primary"):
                for i, r in ed.iterrows():
                    o = df[df['用户ID'] == r['用户ID']].iloc[0]
                    resign_date = None
                    if r['账号状态'] == '离职' and o['账号状态'] == '在职':
                        resign_date = date.today().isoformat()
                    elif r['账号状态'] == '在职':
                        resign_date = None
                    if r['密码'] != o['密码'] or r['账号状态'] != o['账号状态'] or r['人员性质'] != o['人员性质']:
                        db.run_sql("UPDATE 用户信息表 SET 密码=?, 账号状态=?, 人员性质=?, 离职时间=? WHERE 用户ID=?",
                                   (r['密码'], r['账号状态'], r['人员性质'], resign_date, r['用户ID']))
                st.rerun()

    with tab2:
        role_filter = '公司作业员'
        df = db.query_df(
            f"SELECT 用户ID, 姓名, 密码, 人员性质, 所属公司, 账号状态 FROM 用户信息表 WHERE 系统角色='{role_filter}'")
        with st.expander(f"➕ 添加公司人员"):
            c1, c2, c3, c4 = st.columns(4)
            name = c1.text_input("姓名", key="name_comp_final")
            pwd = c2.text_input("密码", "123456", key="pwd_comp_final")
            prop = c3.selectbox("人员性质", ["", "在编", "劳务派遣"], key="prop_comp_final")
            comp = c4.text_input("所属公司", key="comp_comp_final")
            if st.button("添加", key="btn_comp_final"):
                if name and comp:
                    try:
                        db.run_sql(
                            "INSERT INTO 用户信息表 (姓名, 密码, 系统角色, 所属部门, 所属公司, 人员性质, 账号状态) VALUES (?, ?, ?, '', ?, ?, '在职')",
                            (name, pwd, role_filter, comp, prop))
                        st.success("成功");
                        st.rerun()
                    except Exception as e:
                        st.error(f"添加失败：{e}")
                else:
                    st.warning("请填写姓名和公司")
        if not df.empty:
            df = utils.add_idx(df)
            df['人员性质'] = df['人员性质'].fillna('')
            cfg = {
                "用户ID": None, "密码": st.column_config.TextColumn("密码"),
                "人员性质": st.column_config.SelectboxColumn("性质", options=["", "在编", "劳务派遣"]),
                "所属公司": st.column_config.TextColumn("所属公司"),
                "账号状态": st.column_config.SelectboxColumn("状态", options=["在职", "离职"])
            }
            ed = st.data_editor(df, column_config=cfg, key="ed_comp_final", hide_index=True)
            if st.button("保存修改", key="save_comp_final", type="primary"):
                for i, r in ed.iterrows():
                    o = df[df['用户ID'] == r['用户ID']].iloc[0]
                    resign_date = None
                    if r['账号状态'] == '离职' and o['账号状态'] == '在职': resign_date = date.today().isoformat()
                    if r['密码'] != o['密码'] or r['账号状态'] != o['账号状态'] or r['所属公司'] != o['所属公司'] or r[
                        '人员性质'] != o['人员性质']:
                        db.run_sql(
                            "UPDATE 用户信息表 SET 密码=?, 账号状态=?, 所属公司=?, 人员性质=?, 离职时间=? WHERE 用户ID=?",
                            (r['密码'], r['账号状态'], r['所属公司'], r['人员性质'], resign_date, r['用户ID']))
                st.rerun()


# ===========================
# 2. 通用组件：工作量日志
# ===========================
def show_work_log(pid, filter_company=None):
    """显示项目的工作量透视表"""
    where_clause = f"WHERE T.项目ID = {pid}"
    if filter_company: where_clause += f" AND U.所属公司 = '{filter_company}'"
    try:
        log_sql = f"SELECT R.记录日期, U.姓名 as 作业员, T.子任务名称, R.阶段名称, R.工作量 FROM 工作记录表 R JOIN 用户信息表 U ON R.用户ID = U.用户ID JOIN 子任务表 T ON R.子任务ID = T.子任务ID {where_clause}"
        df_log = db.query_df(log_sql)
        if not df_log.empty:
            df_log['任务_作业员'] = df_log['子任务名称'] + ' (' + df_log['阶段名称'] + ') - ' + df_log['作业员']
            pivot = df_log.pivot_table(index='任务_作业员', columns='记录日期', values='工作量', aggfunc='sum',
                                       fill_value=0)
            pivot = pivot.sort_index(axis=1);
            pivot['合计'] = pivot.sum(axis=1);
            pivot.loc['总计'] = pivot.sum(axis=0)
            styled_pivot = pivot.astype(float).round(1).astype(str).replace('0.0', '-')
            st.dataframe(styled_pivot, use_container_width=True, height=400)
        else:
            st.info("暂无作业员上报记录")
    except:
        pass


# ===========================
# 3. 考勤管理模块
# ===========================
def view_attendance():
    st.subheader("📅 人员考勤管理")
    uid = st.session_state.user['用户ID']
    role = st.session_state.user['系统角色']

    start_dt, end_dt, filter_project_id, filter_proj_name = None, None, None, None

    if role == '部门领导':
        col_date1, col_date2 = st.columns(2)
        start_dt = col_date1.date_input("开始日期", date.today() - timedelta(days=7))
        end_dt = col_date2.date_input("结束日期", date.today())
        st.info(f"查看时间段：**{start_dt}** 至 **{end_dt}**")
    else:
        st.markdown("#### 选择项目")
        type_col, proj_col = st.columns([1, 3])
        proj_type = type_col.radio("项目状态", ["进行中", "历史项目"], horizontal=True)
        status_filter = "进行中" if proj_type == "进行中" else "已结束"
        leader_projs = db.query_df(
            f"SELECT P.项目ID, P.项目名称, P.项目开始时间, P.项目结束时间 FROM 项目人员关联表 R JOIN 项目信息表 P ON R.项目ID=P.项目ID WHERE R.用户ID={uid} AND R.项目角色 IN ('项目负责人', '技术负责人', '质量负责人') AND P.项目状态 = '{status_filter}'")
        if leader_projs.empty: st.warning(f"您没有负责的{proj_type}项目"); return
        sel_proj = proj_col.selectbox("选择项目", leader_projs['项目ID'], format_func=lambda x:
        leader_projs[leader_projs['项目ID'] == x]['项目名称'].values[0])
        filter_project_id = sel_proj
        filter_proj_name = leader_projs[leader_projs['项目ID'] == sel_proj]['项目名称'].values[0]
        proj_info = leader_projs[leader_projs['项目ID'] == sel_proj].iloc[0]
        start_dt = pd.to_datetime(proj_info['项目开始时间']).date() if pd.notna(
            proj_info['项目开始时间']) else date.today() - timedelta(days=30)
        end_dt = pd.to_datetime(proj_info['项目结束时间']).date() if pd.notna(
            proj_info['项目结束时间']) else date.today()
        st.info(f"项目：**{filter_proj_name}** | 时间：{start_dt} 至 {end_dt}")

    tab_dept, tab_comp = st.tabs(["本部门人员", "公司人员"])

    def render_attendance_tab(target_role):
        show_resigned = st.checkbox("显示离职人员", value=False, key=f"res_{target_role}")
        if role == '部门领导':
            df_users = db.query_df(
                f"SELECT 用户ID, 姓名, 系统角色, 所属公司, 账号状态, 离职时间 FROM 用户信息表 WHERE 系统角色 = '{target_role}' {'OR 账号状态=\'离职\'' if show_resigned else 'AND 账号状态=\'在职\''}")
        else:
            df_users = db.query_df(
                f"SELECT DISTINCT U.用户ID, U.姓名, U.系统角色, U.所属公司, U.账号状态, U.离职时间 FROM 用户信息表 U JOIN 项目人员分配表 A ON U.用户ID = A.用户ID WHERE A.项目ID = {filter_project_id} AND U.系统角色 = '{target_role}' AND (U.账号状态='在职' {'OR U.账号状态=\'离职\'' if show_resigned else ''})")

        if df_users.empty: st.warning(f"暂无{target_role}人员"); return

        user_info_map = df_users.set_index('姓名').to_dict('index')
        selected_ids = df_users['用户ID'].tolist()

        alloc_sql = f"SELECT A.用户ID, P.项目名称, A.开始日期 FROM 项目人员分配表 A JOIN 项目信息表 P ON A.项目ID = P.项目ID WHERE A.用户ID IN ({','.join(map(str, selected_ids))}) ORDER BY A.开始日期 DESC, A.分配ID DESC"
        df_alloc = db.query_df(alloc_sql)

        user_allocs = {}
        for _, r in df_alloc.iterrows():
            u_id = r['用户ID']
            proj = r['项目名称']
            start = r['开始日期']
            if u_id not in user_allocs: user_allocs[u_id] = []
            dt_obj = pd.to_datetime(start).date() if pd.notna(start) else date(2000, 1, 1)
            user_allocs[u_id].append({'date': dt_obj, 'proj': proj})

        record_sql = f"SELECT 用户ID, 日期, 状态 FROM 考勤记录表 WHERE 日期 BETWEEN '{start_dt}' AND '{end_dt}' AND 用户ID IN ({','.join(map(str, selected_ids))})"
        df_records = db.query_df(record_sql)

        data = []
        current = start_dt
        selected_users = df_users['姓名'].tolist()
        today = date.today()

        while current <= end_dt:
            row_data = {'日期': current}
            if current > today:
                for name in selected_users: row_data[name] = ""
            else:
                for name in selected_users:
                    u_info = user_info_map[name]
                    u_id = u_info['用户ID']
                    u_status = u_info['账号状态']
                    u_resign_date = u_info.get('离职时间')

                    if u_status == '离职' and pd.notna(u_resign_date):
                        if current >= pd.to_datetime(u_resign_date).date():
                            row_data[name] = ""
                            continue

                    rec = df_records[(df_records['用户ID'] == u_id) & (df_records['日期'] == current.isoformat())]
                    if not rec.empty:
                        rec_status = rec.iloc[0]['状态']
                        if rec_status not in ['请假', '休息', '路途']:
                            if role == '部门领导':
                                row_data[name] = rec_status
                            else:
                                row_data[name] = rec_status if rec_status == filter_proj_name else ""
                        else:
                            row_data[name] = rec_status
                        continue

                    default_proj = ""
                    if u_id in user_allocs:
                        for alloc in user_allocs[u_id]:
                            if alloc['date'] <= current:
                                default_proj = alloc['proj']
                                break

                    if default_proj:
                        if role == '部门领导':
                            row_data[name] = default_proj
                        else:
                            row_data[name] = default_proj if default_proj == filter_proj_name else ""
                    else:
                        row_data[name] = ""

            data.append(row_data)
            current += timedelta(days=1)

        df_view = pd.DataFrame(data)

        with st.expander("⚙️ 批量调整考勤状态"):
            c1, c2, c3, c4 = st.columns(4)
            adj_users = c1.multiselect("选择人员", selected_users, key=f"adj_u_{target_role}")
            adj_start = c2.date_input("开始", date.today(), max_value=date.today(), key=f"adj_s_{target_role}")
            adj_end = c3.date_input("结束", date.today(), max_value=date.today(), key=f"adj_e_{target_role}")
            new_status = c4.selectbox("调整为", ['休息', '路途', '项目名称'], key=f"adj_st_{target_role}")
            if st.button("执行调整", key=f"btn_adj_{target_role}"):
                if not adj_users:
                    st.warning("请选择人员")
                elif adj_end < adj_start:
                    st.warning("日期错误")
                else:
                    adj_uids = [user_info_map[name]['用户ID'] for name in adj_users]
                    cnt = 0
                    for d in pd.date_range(adj_start, adj_end):
                        d_str = d.strftime('%Y-%m-%d')
                        for u_id in adj_uids:
                            db.run_sql("DELETE FROM 考勤记录表 WHERE 用户ID=? AND 日期=?", (u_id, d_str))
                            if new_status != "项目名称":
                                db.run_sql(
                                    "INSERT INTO 考勤记录表 (用户ID, 日期, 状态, 修改人ID, 修改时间) VALUES (?, ?, ?, ?, datetime('now'))",
                                    (u_id, d_str, new_status, uid))
                            cnt += 1
                    st.success(f"成功调整 {cnt} 条记录");
                    st.rerun()

        st.markdown("#### 考勤明细")
        if not df_view.empty:
            st.dataframe(df_view.set_index('日期'), use_container_width=True)
        else:
            st.info("无数据")

    with tab_dept:
        render_attendance_tab('本部门作业员')
    with tab_comp:
        render_attendance_tab('公司作业员')


# ===========================
# 4. 项目管理模块
# ===========================
# ===========================
# 4. 项目管理模块 (完整修正版)
# ===========================
def view_projects():
    st.subheader("项目管理")
    # 初始化 Session State
    if 'pid' not in st.session_state: st.session_state.pid = None
    if 'show_allocation' not in st.session_state: st.session_state.show_allocation = False

    # --- 1. 人员分配页面 ---
    if st.session_state.show_allocation:
        if st.button("⬅️ 返回项目列表"): st.session_state.show_allocation = False; st.rerun()
        st.markdown("#### 👥 项目人员分配")

        all_staff = db.query_df(
            "SELECT 用户ID, 姓名, 所属公司 FROM 用户信息表 WHERE 系统角色 IN ('本部门作业员', '公司作业员') AND 账号状态='在职' ORDER BY 姓名")
        all_projects = db.query_df(
            "SELECT 项目ID, 项目名称 FROM 项目信息表 WHERE 项目状态 = '进行中' ORDER BY 项目名称")

        if all_staff.empty or all_projects.empty:
            if all_projects.empty:
                st.warning("当前没有正在进行的项目，无法分配人员。")
            else:
                st.warning("缺少人员")
            return

        assigned = db.query_df(
            "SELECT A.分配ID, A.用户ID, U.姓名, U.所属公司, P.项目名称, A.开始日期 FROM 项目人员分配表 A JOIN 用户信息表 U ON A.用户ID = U.用户ID JOIN 项目信息表 P ON A.项目ID = P.项目ID ORDER BY A.分配ID DESC")

        project_list = all_projects['项目名称'].tolist()
        project_options = project_list + ["其他"]
        project_map = {row['项目名称']: row['项目ID'] for _, row in all_projects.iterrows()}

        base_data = []
        for _, staff_row in all_staff.iterrows():
            u_id = staff_row['用户ID']
            name = staff_row['姓名']
            company = staff_row['所属公司']

            user_records = assigned[assigned['用户ID'] == u_id]
            latest_rec = user_records.iloc[0] if not user_records.empty else None

            if latest_rec is not None:
                proj_name = latest_rec['项目名称']
                start_date = latest_rec['开始日期']
                s_dt = pd.to_datetime(start_date).date() if pd.notna(start_date) else date.today()
                days = (date.today() - s_dt).days + 1 if s_dt <= date.today() else 0
            else:
                proj_name = "其他"
                start_date = None
                days = 0

            base_data.append({'用户ID': u_id, '姓名': name, '所属公司': company, '项目名称': proj_name,
                              '指派时间': pd.to_datetime(start_date).date() if pd.notna(start_date) else None,
                              '已参与天数': days})

        df_edit = pd.DataFrame(base_data)
        st.info("📌 操作说明：修改项目或时间后点击保存。系统将自动清理冲突的旧记录。")

        cfg = {"用户ID": None, "姓名": st.column_config.TextColumn("姓名", disabled=True),
               "所属公司": st.column_config.TextColumn("公司", disabled=True),
               "项目名称": st.column_config.SelectboxColumn("项目名称", options=project_options, required=True),
               "指派时间": st.column_config.DateColumn("指派时间", format="YYYY-MM-DD"),
               "已参与天数": st.column_config.NumberColumn("已参与天数", disabled=True)}
        ed = st.data_editor(utils.add_idx(df_edit), column_config=cfg, hide_index=True, key="alloc_editor",
                            use_container_width=True)

        if st.button("保存分配", type="primary"):
            cnt_add, cnt_del = 0, 0
            conn = db.get_conn()
            cursor = conn.cursor()
            try:
                for _, r in ed.iterrows():
                    u_id = r['用户ID']
                    proj_name = r['项目名称']
                    assign_date = r.get('指派时间')
                    if pd.isna(assign_date) or assign_date is None: assign_date = date.today()
                    assign_date_str = utils.date_to_str(assign_date)

                    if proj_name == "其他":
                        cursor.execute(
                            "DELETE FROM 项目人员分配表 WHERE 用户ID=? AND (开始日期 IS NULL OR 开始日期 >= ?)",
                            (u_id, date.today().isoformat()))
                        cnt_del += 1
                    elif proj_name in project_map:
                        pid = project_map[proj_name]
                        cursor.execute("DELETE FROM 项目人员分配表 WHERE 用户ID=? AND 开始日期 > ?",
                                       (u_id, assign_date_str))
                        cursor.execute(
                            "INSERT OR REPLACE INTO 项目人员分配表 (项目ID, 用户ID, 开始日期) VALUES (?, ?, ?)",
                            (pid, u_id, assign_date_str))
                        cnt_add += 1

                conn.commit()
                st.success(f"✅ 保存成功！新增/修改 {cnt_add} 条，清理冲突 {cnt_del} 条。")
                st.balloons()
                st.rerun()
            except Exception as e:
                conn.rollback()
                st.error(f"保存失败: {e}")
            finally:
                conn.close()

    # --- 2. 项目详情管理页面 (负责人设置) ---
    elif st.session_state.pid:
        pid = st.session_state.pid
        info = db.query_df(f"SELECT 项目名称 FROM 项目信息表 WHERE 项目ID={pid}").iloc[0]
        if st.button("⬅️ 返回"): st.session_state.pid = None; st.rerun()
        st.write(f"#### {info['项目名称']}")
        tab1, tab2 = st.tabs(["三大负责人", "公司负责人"])
        with tab1:
            curr = db.query_df(
                f"SELECT 项目角色, 用户ID FROM 项目人员关联表 WHERE 项目ID={pid} AND 项目角色 LIKE '%负责人'")
            curr_map = {r['项目角色']: r['用户ID'] for _, r in curr.iterrows()}
            # 修复：只筛选本部门作业员
            staff = db.query_df(
                f"SELECT DISTINCT U.用户ID, U.姓名 FROM 项目人员分配表 A JOIN 用户信息表 U ON A.用户ID = U.用户ID WHERE A.项目ID = {pid} AND U.账号状态='在职' AND U.系统角色 = '本部门作业员'")

            names_list = [""] + list(staff['姓名'])
            if not staff.empty:
                with st.form("role_form"):
                    c1, c2, c3 = st.columns(3)

                    def get_curr_name(role_key):
                        uid = curr_map.get(role_key)
                        if uid: return staff[staff['用户ID'] == uid].iloc[0]['姓名'] if not staff[
                            staff['用户ID'] == uid].empty else ""
                        return ""

                    def get_idx(name):
                        return names_list.index(name) if name in names_list else 0

                    r1 = c1.selectbox("项目负责人", names_list, index=get_idx(get_curr_name('项目负责人')))
                    r2 = c2.selectbox("技术负责人", names_list, index=get_idx(get_curr_name('技术负责人')))
                    r3 = c3.selectbox("质量负责人", names_list, index=get_idx(get_curr_name('质量负责人')))
                    if st.form_submit_button("保存负责人设置"):
                        db.run_sql(
                            f"DELETE FROM 项目人员关联表 WHERE 项目ID={pid} AND 项目角色 IN ('项目负责人','技术负责人','质量负责人')")
                        s_map = {r['姓名']: r['用户ID'] for _, r in staff.iterrows()}
                        if r1: db.run_sql("INSERT INTO 项目人员关联表 (项目ID, 项目角色, 用户ID) VALUES (?, ?, ?)",
                                          (pid, '项目负责人', s_map[r1]))
                        if r2: db.run_sql("INSERT INTO 项目人员关联表 (项目ID, 项目角色, 用户ID) VALUES (?, ?, ?)",
                                          (pid, '技术负责人', s_map[r2]))
                        if r3: db.run_sql("INSERT INTO 项目人员关联表 (项目ID, 项目角色, 用户ID) VALUES (?, ?, ?)",
                                          (pid, '质量负责人', s_map[r3]))
                        st.success("已更新");
                        st.rerun()
            else:
                st.warning("该项目暂未分配本部门人员，无法设置负责人。")
            st.divider();
            st.markdown("##### 📊 项目工作量日志");
            show_work_log(pid)

        with tab2:
            st.markdown("#### 指定公司负责人")
            st.caption("仅显示已分配到此项目的公司，且只能选择该公司的人员。")
            df_proj_users = db.query_df(
                f"SELECT DISTINCT U.用户ID, U.姓名, U.所属公司 FROM 用户信息表 U JOIN 项目人员分配表 A ON U.用户ID = A.用户ID WHERE A.项目ID = {pid} AND U.系统角色 = '公司作业员'")
            if df_proj_users.empty:
                st.info("该项目暂未分配公司人员，请先在‘项目人员分配’中添加人员。")
            else:
                companies_in_proj = df_proj_users['所属公司'].unique().tolist()
                df_current_leads = db.query_df(
                    f"SELECT U.所属公司, U.姓名 FROM 项目人员关联表 R JOIN 用户信息表 U ON R.用户ID = U.用户ID WHERE R.项目ID={pid} AND R.项目角色='公司负责人'")
                current_lead_map = {r['所属公司']: r['姓名'] for _, r in df_current_leads.iterrows()}
                grid_data = []
                for comp in companies_in_proj: grid_data.append(
                    {'所属公司': comp, '公司负责人': current_lead_map.get(comp, "")})
                df_grid = pd.DataFrame(grid_data)
                all_proj_user_names = sorted(df_proj_users['姓名'].unique().tolist())
                cfg = {"所属公司": st.column_config.TextColumn("所属公司", disabled=True),
                       "公司负责人": st.column_config.SelectboxColumn("负责人", options=[""] + all_proj_user_names,
                                                                      required=False)}
                ed_grid = st.data_editor(df_grid, column_config=cfg, hide_index=True, key=f"comp_lead_editor_{pid}")
                if st.button("保存公司负责人设置", type="primary"):
                    saved_cnt = 0
                    db.run_sql(f"DELETE FROM 项目人员关联表 WHERE 项目ID={pid} AND 项目角色='公司负责人'")
                    name_info_map = {r['姓名']: {'id': r['用户ID'], 'comp': r['所属公司']} for _, r in
                                     df_proj_users.iterrows()}
                    for _, row in ed_grid.iterrows():
                        comp_name = row['所属公司'];
                        selected_user = row['公司负责人']
                        if selected_user and selected_user in name_info_map:
                            user_info = name_info_map[selected_user]
                            if user_info['comp'] == comp_name:
                                db.run_sql(
                                    "INSERT INTO 项目人员关联表 (项目ID, 项目角色, 用户ID) VALUES (?, '公司负责人', ?)",
                                    (pid, user_info['id']));
                                saved_cnt += 1
                            else:
                                st.warning(f"⚠️ {comp_name} 的负责人设置无效：{selected_user} 不属于该公司，已忽略。")
                    if saved_cnt > 0:
                        st.success(f"✅ 成功保存 {saved_cnt} 位公司负责人设置！"); st.balloons(); st.rerun()
                    else:
                        st.info("未做更改或设置无效。")

    # --- 3. 项目列表管理页面 (主页) ---
    else:
        user_role = st.session_state.user['系统角色']
        df_all = db.query_df("SELECT 项目ID, 项目名称, 项目状态, 项目开始时间, 项目结束时间 FROM 项目信息表")

        if 'proj_editor_key' not in st.session_state: st.session_state.proj_editor_key = "proj_list_active_v1"

        if user_role == '部门领导':
            tab_active, tab_history = st.tabs(["活跃项目", "历史项目"])

            with tab_active:
                # --- 删除确认弹窗逻辑 ---
                if st.session_state.get('confirm_delete_ids'):
                    st.error("⚠️ **危险操作确认**")
                    st.warning(
                        "您正在尝试删除以下项目，此操作**不可恢复**！相关考勤记录将被冻结保留，但项目数据将被彻底清除。")
                    del_names = st.session_state.get('confirm_delete_names', [])
                    for n in del_names: st.write(f"- {n}")

                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("❌ 确认永久删除", type="primary", key="confirm_del_btn"):
                            conn = db.get_conn()
                            cursor = conn.cursor()
                            try:
                                for del_id in st.session_state.confirm_delete_ids:
                                    # 冻结考勤逻辑
                                    cursor.execute(f"SELECT 项目名称 FROM 项目信息表 WHERE 项目ID={del_id}")
                                    p_row = cursor.fetchone()
                                    if p_row:
                                        p_name = p_row[0]
                                    else:
                                        p_name = "未知项目"

                                    cursor.execute(f"SELECT 用户ID, 开始日期 FROM 项目人员分配表 WHERE 项目ID={del_id}")
                                    allocs = cursor.fetchall()

                                    for u_id, s_date in allocs:
                                        if s_date is None: continue
                                        start_d = pd.to_datetime(s_date).date()
                                        end_d = date.today()
                                        current_d = start_d
                                        while current_d <= end_d:
                                            d_str = current_d.isoformat()
                                            cursor.execute(
                                                "INSERT OR IGNORE INTO 考勤记录表 (用户ID, 日期, 状态) VALUES (?, ?, ?)",
                                                (u_id, d_str, p_name))
                                            current_d += timedelta(days=1)

                                    # 级联删除
                                    cursor.execute(f"SELECT 子任务ID FROM 子任务表 WHERE 项目ID={del_id}")
                                    t_ids = [r[0] for r in cursor.fetchall()]
                                    if t_ids:
                                        cursor.execute(
                                            f"DELETE FROM 工作记录表 WHERE 子任务ID IN ({','.join(map(str, t_ids))})")
                                        cursor.execute(
                                            f"DELETE FROM 任务阶段进度表 WHERE 子任务ID IN ({','.join(map(str, t_ids))})")
                                    cursor.execute(f"DELETE FROM 子任务表 WHERE 项目ID={del_id}")
                                    cursor.execute(f"DELETE FROM 项目人员分配表 WHERE 项目ID={del_id}")
                                    cursor.execute(f"DELETE FROM 项目人员关联表 WHERE 项目ID={del_id}")
                                    cursor.execute(f"DELETE FROM 项目信息表 WHERE 项目ID={del_id}")

                                conn.commit()
                                st.success("项目已彻底删除，历史考勤已保留。")
                                del st.session_state.confirm_delete_ids
                                del st.session_state.confirm_delete_names
                                st.session_state.proj_editor_key = f"proj_list_active_{uuid.uuid4()}"
                                st.rerun()
                            except Exception as e:
                                conn.rollback()
                                st.error(f"删除失败: {e}")
                            finally:
                                conn.close()

                    with c2:
                        if st.button("取消", key="cancel_del_btn"):
                            del st.session_state.confirm_delete_ids
                            del st.session_state.confirm_delete_names
                            st.session_state.proj_editor_key = f"proj_list_active_{uuid.uuid4()}"
                            st.rerun()

                else:
                    # --- 正常列表显示与保存逻辑 ---
                    df = df_all[df_all['项目状态'].isin(['进行中', '暂停', '未开始'])].copy()

                    with st.expander("➕ 新建项目"):
                        n = st.text_input("项目名称", key="new_proj_name_input")
                        if st.button("创建项目", key="create_proj_btn"):
                            if n:
                                try:
                                    db.run_sql("INSERT INTO 项目信息表 (项目名称, 项目状态) VALUES (?, '未开始')",
                                               (n,));
                                    st.success("创建成功");
                                    st.session_state.proj_editor_key = f"proj_list_active_{uuid.uuid4()}"
                                    st.rerun()
                                except:
                                    st.error("项目名称已存在")

                    # 预处理日期显示
                    for col in ['项目开始时间', '项目结束时间']:
                        if col in df.columns: df[col] = pd.to_datetime(df[col], errors='coerce').dt.date
                    df = utils.add_idx(df)

                    cfg = {
                        "项目ID": None, "序号": None,
                        "项目名称": st.column_config.TextColumn("项目名称", required=True),
                        "项目状态": st.column_config.SelectboxColumn("状态",
                                                                     options=["未开始", "进行中", "已结束", "暂停"]),
                        "项目开始时间": st.column_config.DateColumn("开始时间"),
                        "项目结束时间": st.column_config.DateColumn("结束时间")
                    }

                    st.info("📌 提示：在表格中直接修改或删除行，最后点击‘保存所有更改’。")
                    ed = st.data_editor(df, column_config=cfg, key=st.session_state.proj_editor_key, hide_index=True,
                                        num_rows="dynamic")

                    if st.button("保存所有更改", type="primary", key="save_proj_active"):
                        current_ids = set(df['项目ID'])
                        new_ids = set(ed['项目ID'].dropna())
                        deleted_ids = current_ids - new_ids

                        # 1. 处理删除
                        if deleted_ids:
                            del_names = df[df['项目ID'].isin(deleted_ids)]['项目名称'].tolist()
                            st.session_state.confirm_delete_ids = list(deleted_ids)
                            st.session_state.confirm_delete_names = del_names
                            st.rerun()
                        else:
                            # 2. 处理新增和更新
                            conn = db.get_conn()
                            cursor = conn.cursor()
                            update_cnt = 0
                            try:
                                # 遍历编辑后的每一行
                                for _, r in ed.iterrows():
                                    pid = r.get('项目ID')
                                    p_name = r.get('项目名称')
                                    p_status = r.get('项目状态')
                                    # 使用增强版 date_to_str 进行转换
                                    p_start = utils.date_to_str(r.get('项目开始时间'))
                                    p_end = utils.date_to_str(r.get('项目结束时间'))

                                    if pd.isna(pid):
                                        # 新增项目
                                        if pd.notna(p_name):
                                            cursor.execute(
                                                "INSERT INTO 项目信息表 (项目名称, 项目状态, 项目开始时间, 项目结束时间) VALUES (?, ?, ?, ?)",
                                                (p_name, p_status, p_start, p_end))
                                            update_cnt += 1
                                    else:
                                        # 更新项目 - 强制更新所有字段
                                        cursor.execute(
                                            "UPDATE 项目信息表 SET 项目名称=?, 项目状态=?, 项目开始时间=?, 项目结束时间=? WHERE 项目ID=?",
                                            (p_name, p_status, p_start, p_end, int(pid)))
                                        update_cnt += 1

                                conn.commit()
                                st.success(f"保存成功！共更新/新增 {update_cnt} 条记录。")
                                # 强制刷新表格key
                                st.session_state.proj_editor_key = f"proj_list_active_{uuid.uuid4()}"
                                st.rerun()
                            except Exception as e:
                                conn.rollback()
                                st.error(f"保存失败: {e}")
                            finally:
                                conn.close()

                    st.divider()
                    if st.button("👥 人员分配",
                                 key="btn_alloc_active"): st.session_state.show_allocation = True; st.rerun()

                    st.markdown("#### 项目详情管理")
                    valid_proj_ids = ed['项目ID'].dropna().tolist()
                    if valid_proj_ids:
                        sel = st.selectbox("选择项目进入管理", valid_proj_ids,
                                           format_func=lambda x: ed[ed['项目ID'] == x]['项目名称'].values[0],
                                           key="sel_active")
                        if st.button("进入管理", type="primary",
                                     key="enter_active"): st.session_state.pid = sel; st.rerun()
                    else:
                        st.info("列表中暂无有效项目")

            with tab_history:
                df = df_all[df_all['项目状态'] == '已结束']
                if df.empty:
                    st.info("暂无历史项目")
                else:
                    for col in ['项目开始时间', '项目结束时间']:
                        if col in df.columns: df[col] = pd.to_datetime(df[col], errors='coerce').dt.date
                    st.dataframe(utils.add_idx(df), hide_index=True, use_container_width=True)
        else:
            # --- 其他角色视图 ---
            df = df_all
            with st.expander("➕ 新建项目"):
                n = st.text_input("名称")
                if st.button("创建"):
                    if n:
                        try:
                            db.run_sql("INSERT INTO 项目信息表 (项目名称, 项目状态) VALUES (?, '未开始')",
                                       (n,)); st.success("成功"); st.rerun()
                        except:
                            st.error("重名")
            if df.empty: return
            for col in ['项目开始时间', '项目结束时间']:
                if col in df.columns: df[col] = pd.to_datetime(df[col], errors='coerce').dt.date
            df = utils.add_idx(df)
            cfg = {"项目ID": None, "序号": None, "项目名称": st.column_config.TextColumn("项目名称", disabled=True),
                   "项目状态": st.column_config.SelectboxColumn("状态", options=["未开始", "进行中", "已结束", "暂停"]),
                   "项目开始时间": st.column_config.DateColumn("开始时间"),
                   "项目结束时间": st.column_config.DateColumn("结束时间")}
            ed = st.data_editor(df, column_config=cfg, key="proj_list", hide_index=True)
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("保存项目状态及时间", type="primary"):
                    for _, r in ed.iterrows():
                        o = df[df['项目ID'] == r['项目ID']].iloc[0]
                        if r['项目状态'] != o['项目状态']: db.run_sql("UPDATE 项目信息表 SET 项目状态=? WHERE 项目ID=?",
                                                                      (r['项目状态'], r['项目ID']))
                        if utils.date_to_str(r.get('项目开始时间')) != utils.date_to_str(
                            o.get('项目开始时间')): db.run_sql("UPDATE 项目信息表 SET 项目开始时间=? WHERE 项目ID=?",
                                                               (utils.date_to_str(r.get('项目开始时间')), r['项目ID']))
                        if utils.date_to_str(r.get('项目结束时间')) != utils.date_to_str(
                            o.get('项目结束时间')): db.run_sql("UPDATE 项目信息表 SET 项目结束时间=? WHERE 项目ID=?",
                                                               (utils.date_to_str(r.get('项目结束时间')), r['项目ID']))
                    st.success("保存成功");
                    st.rerun()
            with col_btn2:
                if st.button("👥 人员分配", type="secondary"): st.session_state.show_allocation = True; st.rerun()
            st.divider()
            sel = st.selectbox("选择项目进入管理", df['项目ID'],
                               format_func=lambda x: df[df['项目ID'] == x]['项目名称'].values[0])
            if st.button("进入管理", type="primary"): st.session_state.pid = sel; st.rerun()


# ===========================
# 5. 我的任务模块
# ===========================
def view_my_project():
    uid = st.session_state.user['用户ID']
    projs_active = db.query_df(
        f"SELECT P.项目ID, P.项目名称 FROM 项目信息表 P JOIN 项目人员关联表 R ON P.项目ID=R.项目ID WHERE R.用户ID={uid} AND P.项目状态 = '进行中'")
    projs_paused = db.query_df(
        f"SELECT P.项目ID, P.项目名称 FROM 项目信息表 P JOIN 项目人员关联表 R ON P.项目ID=R.项目ID WHERE R.用户ID={uid} AND P.项目状态 = '暂停'")
    projs_ended = db.query_df(
        f"SELECT P.项目ID, P.项目名称 FROM 项目信息表 P JOIN 项目人员关联表 R ON P.项目ID=R.项目ID WHERE R.用户ID={uid} AND P.项目状态 = '已结束'")

    if projs_active.empty and projs_paused.empty and projs_ended.empty: st.info("无负责项目"); return

    tab_names = []
    if not projs_active.empty: tab_names.append("进行中")
    if not projs_paused.empty: tab_names.append("暂停")
    if not projs_ended.empty: tab_names.append("历史项目（已结束）")
    tabs = st.tabs(tab_names)
    current_idx = 0

    def show_project_tasks(df_projs, tab_idx, is_history=False):
        if df_projs.empty: return
        with tabs[tab_idx]:
            if is_history: st.info("以下为已结束的历史项目，仅供查看")
            pid = st.selectbox("项目", df_projs['项目ID'],
                               format_func=lambda x: df_projs[df_projs['项目ID'] == x]['项目名称'].values[0],
                               key=f"proj_sel_{tab_idx}")
            if 'upload_key' not in st.session_state: st.session_state.upload_key = 0

            if not is_history:
                with st.expander("📥 Excel导入子任务"):
                    buf = io.BytesIO()
                    pd.DataFrame({'子任务名称': [], '工作量': []}).to_excel(buf, index=False)
                    st.download_button("下载模板", buf.getvalue(), "template.xlsx")
                    f = st.file_uploader("上传", type='xlsx', key=f"uploader_{st.session_state.upload_key}_{tab_idx}")
                    if f:
                        imp = pd.read_excel(f);
                        cnt = 0
                        for _, r in imp.iterrows():
                            if pd.notna(r['子任务名称']):
                                db.run_sql("INSERT INTO 子任务表 (项目ID, 子任务名称, 工作量) VALUES (?, ?, ?)",
                                           (pid, str(r['子任务名称']), float(r.get('工作量', 0))));
                                cnt += 1
                        if cnt > 0: st.success(f"导入 {cnt} 条"); st.session_state.upload_key += 1; st.rerun()

            sql = f"SELECT T.子任务ID, T.子任务名称, T.工作量, P1.姓名 AS 生产_人, S1.开始时间 AS 生产_起, S1.预计结束时间 AS 生产_止, COALESCE(W1.done, 0) AS 生产_已完成, P2.姓名 AS 一查_人, S2.开始时间 AS 一查_起, S2.预计结束时间 AS 一查_止, COALESCE(W2.done, 0) AS 一查_已完成, P3.姓名 AS 二查_人, S3.开始时间 AS 二查_起, S3.预计结束时间 AS 二查_止, COALESCE(W3.done, 0) AS 二查_已完成, Stat.总任务工作量, COALESCE(Stat.总完成工作量, 0) AS 总完成工作量 FROM 子任务表 T LEFT JOIN 任务阶段进度表 S1 ON T.子任务ID=S1.子任务ID AND S1.阶段名称='生产' LEFT JOIN (SELECT 子任务ID, 阶段名称, SUM(工作量) as done FROM 工作记录表 GROUP BY 子任务ID, 阶段名称) W1 ON T.子任务ID=W1.子任务ID AND W1.阶段名称='生产' LEFT JOIN 用户信息表 P1 ON S1.作业人员ID=P1.用户ID LEFT JOIN 任务阶段进度表 S2 ON T.子任务ID=S2.子任务ID AND S2.阶段名称='一查' LEFT JOIN (SELECT 子任务ID, 阶段名称, SUM(工作量) as done FROM 工作记录表 GROUP BY 子任务ID, 阶段名称) W2 ON T.子任务ID=W2.子任务ID AND W2.阶段名称='一查' LEFT JOIN 用户信息表 P2 ON S2.作业人员ID=P2.用户ID LEFT JOIN 任务阶段进度表 S3 ON T.子任务ID=S3.子任务ID AND S3.阶段名称='二查' LEFT JOIN (SELECT 子任务ID, 阶段名称, SUM(工作量) as done FROM 工作记录表 GROUP BY 子任务ID, 阶段名称) W3 ON T.子任务ID=W3.子任务ID AND W3.阶段名称='二查' LEFT JOIN 用户信息表 P3 ON S3.作业人员ID=P3.用户ID JOIN (SELECT 项目ID, 子任务名称, SUM(工作量) as 总任务工作量, (SELECT COALESCE(SUM(r.工作量), 0) FROM 工作记录表 r JOIN 子任务表 t2 ON r.子任务ID=t2.子任务ID WHERE t2.子任务名称=子任务表.子任务名称 AND t2.项目ID=子任务表.项目ID) as 总完成工作量 FROM 子任务表 WHERE 项目ID={pid} GROUP BY 子任务名称) Stat ON T.子任务名称 = Stat.子任务名称 WHERE T.项目ID={pid}"
            df = db.query_df(sql)

            if df.empty:
                st.info("暂无任务")
                df = pd.DataFrame(
                    columns=['子任务ID', '子任务名称', '工作量', '生产_人', '生产_起', '生产_止', '生产_已完成',
                             '一查_人', '一查_起', '一查_止', '一查_已完成', '二查_人', '二查_起', '二查_止',
                             '二查_已完成', '总完成工作量'])

            numeric_cols = ['工作量', '生产_已完成', '一查_已完成', '二查_已完成', '总完成工作量']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
                else:
                    df[col] = 0.0
            if '总任务工作量' in df.columns:
                total_work = df['总任务工作量'].values;
                df = df.drop(columns=['总任务工作量'])
            else:
                total_work = df['工作量'].values
            df['总进度'] = [utils.calc_progress_str(df.loc[i, '总完成工作量'], total_work[i]) for i in range(len(df))]
            for p in ['生产', '一查', '二查']:
                done = df[f'{p}_已完成'].values;
                total = df['工作量'].values;
                progress_list = []
                for i in range(len(df)):
                    if total[i] > 0:
                        progress_list.append(f"{(done[i] / total[i] * 100):.1f}%")
                    else:
                        progress_list.append("0.0%")
                df[f'{p}_进度'] = progress_list
            for c in df.columns:
                if '起' in c or '止' in c: df[c] = pd.to_datetime(df[c], errors='coerce').dt.date

            assigned_staff = db.query_df(
                f"SELECT U.用户ID, U.姓名 FROM 项目人员分配表 A JOIN 用户信息表 U ON A.用户ID = U.用户ID WHERE A.项目ID = {pid} AND U.账号状态='在职'")
            s_map = {r['姓名']: r['用户ID'] for _, r in assigned_staff.iterrows()} if not assigned_staff.empty else {}

            disabled_cols = is_history
            cfg = {
                "子任务ID": None, "序号": None,
                "子任务名称": st.column_config.TextColumn("子任务名称", disabled=disabled_cols),
                "工作量": st.column_config.NumberColumn("单人定额", min_value=0.0, format="%.1f",
                                                        disabled=disabled_cols),
                "总完成工作量": st.column_config.NumberColumn("总完成量", disabled=True, format="%.1f"),
                "总进度": st.column_config.TextColumn("总进度", disabled=True),
                "生产_人": st.column_config.SelectboxColumn("生产-人", options=list(s_map.keys()),
                                                            disabled=disabled_cols),
                "生产_起": st.column_config.DateColumn("起", disabled=disabled_cols),
                "生产_止": st.column_config.DateColumn("止", disabled=disabled_cols),
                "生产_已完成": st.column_config.NumberColumn("已完成", format="%.1f", disabled=disabled_cols),
                "生产_进度": st.column_config.TextColumn("进度", disabled=True),
                "一查_人": st.column_config.SelectboxColumn("一查-人", options=list(s_map.keys()),
                                                            disabled=disabled_cols),
                "一查_起": st.column_config.DateColumn("起", disabled=disabled_cols),
                "一查_止": st.column_config.DateColumn("止", disabled=disabled_cols),
                "一查_已完成": st.column_config.NumberColumn("已完成", format="%.1f", disabled=disabled_cols),
                "一查_进度": st.column_config.TextColumn("进度", disabled=True),
                "二查_人": st.column_config.SelectboxColumn("二查-人", options=list(s_map.keys()),
                                                            disabled=disabled_cols),
                "二查_起": st.column_config.DateColumn("起", disabled=disabled_cols),
                "二查_止": st.column_config.DateColumn("止", disabled=disabled_cols),
                "二查_已完成": st.column_config.NumberColumn("已完成", format="%.1f", disabled=disabled_cols),
                "二查_进度": st.column_config.TextColumn("进度", disabled=True)
            }

            if is_history:
                st.dataframe(utils.add_idx(df), column_config=cfg, hide_index=True, use_container_width=True)
            else:
                ed = st.data_editor(utils.add_idx(df), column_config=cfg, key=f"task_full_{tab_idx}", hide_index=True,
                                    num_rows="dynamic")
                if st.button("保存所有修改", type="primary", key=f"save_task_{tab_idx}"):
                    orig_ids = set(df['子任务ID'].dropna()) if '子任务ID' in df.columns else set()
                    edit_ids = set(ed['子任务ID'].dropna()) if '子任务ID' in ed.columns else set()
                    del_ids = orig_ids - edit_ids
                    for did in del_ids:
                        db.run_sql(f"DELETE FROM 任务阶段进度表 WHERE 子任务ID={did}");
                        db.run_sql(f"DELETE FROM 工作记录表 WHERE 子任务ID={did}");
                        db.run_sql(f"DELETE FROM 子任务表 WHERE 子任务ID={did}")
                    orig_done_map = {}
                    if not df.empty and '子任务ID' in df.columns:
                        for i, row in df.iterrows():
                            if pd.notna(row['子任务ID']): orig_done_map[row['子任务ID']] = row
                    for _, r in ed.iterrows():
                        if pd.isna(r.get('子任务名称')) or str(r.get('子任务名称', '')).strip() == '': continue
                        if pd.isna(r.get('子任务ID')):
                            task_name = str(r['子任务名称']).strip();
                            task_workload = float(r.get('工作量', 0) or 0)
                            db.run_sql("INSERT INTO 子任务表 (项目ID, 子任务名称, 工作量) VALUES (?, ?, ?)",
                                       (pid, task_name, task_workload))
                            new_tid = db.query_df("SELECT last_insert_rowid() as id").iloc[0]['id']
                            for p in ['生产', '一查', '二查']:
                                u_name = r.get(f'{p}_人');
                                done_val = float(r.get(f'{p}_已完成', 0) or 0)
                                if pd.notna(u_name) and u_name in s_map:
                                    new_uid = s_map[u_name]
                                    db.run_sql(
                                        "INSERT INTO 任务阶段进度表 (子任务ID, 阶段名称, 作业人员ID, 开始时间, 预计结束时间) VALUES (?, ?, ?, ?, ?)",
                                        (new_tid, p, new_uid, utils.date_to_str(r.get(f'{p}_起')),
                                         utils.date_to_str(r.get(f'{p}_止'))))
                                    if done_val > 0: db.run_sql(
                                        "INSERT INTO 工作记录表 (用户ID, 子任务ID, 阶段名称, 记录日期, 工作量, 备注) VALUES (?, ?, ?, ?, ?, ?)",
                                        (new_uid, new_tid, p, date.today(), done_val, "负责人新增"))
                            st.success(f"新增任务: {task_name}");
                            continue
                        tid = int(r['子任务ID'])
                        db.run_sql("UPDATE 子任务表 SET 子任务名称=?, 工作量=? WHERE 子任务ID=?",
                                   (r['子任务名称'], float(r.get('工作量', 0) or 0), tid))
                        for p in ['生产', '一查', '二查']:
                            u_name = r.get(f'{p}_人');
                            new_done = float(r.get(f'{p}_已完成', 0.0) or 0.0);
                            old_done = float(orig_done_map.get(tid, {}).get(f'{p}_已完成', 0.0) or 0.0)
                            db.run_sql(f"DELETE FROM 任务阶段进度表 WHERE 子任务ID={tid} AND 阶段名称='{p}'")
                            if pd.notna(u_name) and u_name in s_map:
                                new_uid = s_map[u_name]
                                db.run_sql(
                                    "INSERT INTO 任务阶段进度表 (子任务ID, 阶段名称, 作业人员ID, 开始时间, 预计结束时间) VALUES (?, ?, ?, ?, ?)",
                                    (tid, p, new_uid, utils.date_to_str(r.get(f'{p}_起')),
                                     utils.date_to_str(r.get(f'{p}_止'))))
                                if new_done != old_done:
                                    db.run_sql(f"DELETE FROM 工作记录表 WHERE 子任务ID={tid} AND 阶段名称='{p}'")
                                    if new_done > 0: db.run_sql(
                                        "INSERT INTO 工作记录表 (用户ID, 子任务ID, 阶段名称, 记录日期, 工作量, 备注) VALUES (?, ?, ?, ?, ?, ?)",
                                        (new_uid, tid, p, date.today(), new_done, "负责人修正"))
                    st.success("保存成功");
                    st.rerun()
            st.divider();
            st.markdown("##### 📊 项目工作量日志");
            show_work_log(pid)

    idx = 0
    if not projs_active.empty: show_project_tasks(projs_active, idx, is_history=False); idx += 1
    if not projs_paused.empty: show_project_tasks(projs_paused, idx, is_history=False); idx += 1
    if not projs_ended.empty: show_project_tasks(projs_ended, idx, is_history=True)


# ===========================
# 6. 公司进度 & 首页 & 请假
# ===========================
def view_company_progress():
    uid = st.session_state.user['用户ID'];
    user_info = st.session_state.user;
    comp_name = user_info.get('所属公司', '')
    st.write(f"🏢 当前公司：**{comp_name}**")
    projs = db.query_df(
        f"SELECT P.项目ID, P.项目名称 FROM 项目信息表 P JOIN 项目人员关联表 R ON P.项目ID=R.项目ID WHERE R.用户ID={uid} AND R.项目角色='公司负责人' AND P.项目状态 IN ('进行中', '暂停')")
    if projs.empty: st.warning("您暂无负责的项目"); return
    pid = st.selectbox("选择项目", projs['项目ID'],
                       format_func=lambda x: projs[projs['项目ID'] == x]['项目名称'].values[0])
    st.subheader("公司人员工作进度")
    progress_sql = f"SELECT U.姓名 as 作业员, T.子任务名称, S.阶段名称, T.工作量 as 任务总量, COALESCE(R.done, 0) as 已完成, (T.工作量 - COALESCE(R.done, 0)) as 剩余 FROM 任务阶段进度表 S JOIN 子任务表 T ON S.子任务ID = T.子任务ID JOIN 用户信息表 U ON S.作业人员ID = U.用户ID LEFT JOIN (SELECT 子任务ID, 阶段名称, SUM(工作量) as done FROM 工作记录表 GROUP BY 子任务ID, 阶段名称) R ON S.子任务ID = R.子任务ID AND S.阶段名称 = R.阶段名称 WHERE T.项目ID = {pid} AND U.所属公司 = '{comp_name}'"
    df_progress = db.query_df(progress_sql)
    if not df_progress.empty:
        df_progress['任务总量'] = pd.to_numeric(df_progress['任务总量'], errors='coerce').fillna(0)
        df_progress['已完成'] = pd.to_numeric(df_progress['已完成'], errors='coerce').fillna(0)
        df_progress['进度'] = df_progress.apply(lambda x: utils.calc_progress_str(x['已完成'], x['任务总量']), axis=1)
        st.dataframe(utils.add_idx(df_progress), hide_index=True, use_container_width=True)
    else:
        st.info("该公司暂无人员在项目中分配任务")
    st.divider();
    st.subheader("每日工作量日志");
    show_work_log(pid, filter_company=comp_name)


def view_home():
    uid = st.session_state.user['用户ID'];
    today_str = date.today().isoformat()
    leave_status = db.query_df(
        f"SELECT 1 FROM 请假申请表 WHERE 申请人ID={uid} AND 状态='已批准' AND 开始日期 <= '{today_str}' AND 结束日期 >= '{today_str}'")
    is_on_leave = not leave_status.empty
    if is_on_leave: st.info("📅 **今日考勤状态：请假**")
    st.subheader("📋 我的任务看板")
    tasks_sql_active = f"SELECT T.子任务ID, P.项目名称, T.子任务名称, S.阶段名称, P.项目状态, Stat.总任务工作量 as 总工作量, COALESCE(Stat.总完成工作量, 0) as 已完成, (Stat.总任务工作量 - COALESCE(Stat.总完成工作量, 0)) as 剩余工作量 FROM 任务阶段进度表 S JOIN 子任务表 T ON S.子任务ID = T.子任务ID JOIN 项目信息表 P ON T.项目ID = P.项目ID JOIN (SELECT 项目ID, 子任务名称, SUM(工作量) as 总任务工作量, (SELECT COALESCE(SUM(r.工作量), 0) FROM 工作记录表 r JOIN 子任务表 t2 ON r.子任务ID=t2.子任务ID WHERE t2.子任务名称=子任务表.子任务名称 AND t2.项目ID=子任务表.项目ID) as 总完成工作量 FROM 子任务表 GROUP BY 项目ID, 子任务名称) Stat ON T.子任务名称 = Stat.子任务名称 AND T.项目ID = Stat.项目ID WHERE S.作业人员ID = {uid} AND P.项目状态 IN ('进行中', '暂停')"
    df_tasks_active = db.query_df(tasks_sql_active)
    if not df_tasks_active.empty:
        df_tasks_active['总工作量'] = pd.to_numeric(df_tasks_active['总工作量'], errors='coerce').fillna(0);
        df_tasks_active['已完成'] = pd.to_numeric(df_tasks_active['已完成'], errors='coerce').fillna(0);
        df_tasks_active['剩余工作量'] = pd.to_numeric(df_tasks_active['剩余工作量'], errors='coerce').fillna(0)
        df_tasks_active['进度'] = df_tasks_active.apply(lambda x: utils.calc_progress_str(x['已完成'], x['总工作量']),
                                                        axis=1)
        st.dataframe(utils.add_idx(df_tasks_active), column_config={"子任务ID": None}, hide_index=True,
                     use_container_width=True)
    else:
        st.info("暂无分配任务")
    st.divider();
    st.subheader("📝 工作量上报")
    if is_on_leave:
        st.warning("您当前处于请假状态，无需上报工作量。")
    elif df_tasks_active.empty:
        st.warning("无进行中的任务可上报")
    else:
        tasks_opts = {}
        for _, r in df_tasks_active.iterrows(): tasks_opts[f"{r['项目名称']} - {r['子任务名称']} ({r['阶段名称']})"] = (
        r['子任务ID'], r['阶段名称'], r.get('剩余工作量', 0) or 0)
        sel_key = st.selectbox("选择任务", list(tasks_opts.keys()), key="task_sel_home")
        tid, phase, remaining = tasks_opts[sel_key]
        st.info(f"📌 当前任务剩余工作量: **{remaining:.1f}**")
        with st.form("log"):
            dt = st.date_input("日期", date.today(), max_value=date.today());
            amt = st.number_input("工作量", 0.0, step=0.5);
            note = st.text_input("备注")
            if st.form_submit_button("提交", type="primary"):
                if amt > remaining:
                    st.error(f"❌ 上报失败：输入工作量 ({amt}) 超过剩余工作量 ({remaining:.1f})！")
                elif amt <= 0:
                    st.warning("请输入大于0的工作量")
                else:
                    dt_str = str(dt)
                    db.run_sql("DELETE FROM 工作记录表 WHERE 用户ID=? AND 子任务ID=? AND 阶段名称=? AND 记录日期=?",
                               (uid, tid, phase, dt_str))
                    db.run_sql(
                        "INSERT INTO 工作记录表 (用户ID, 子任务ID, 阶段名称, 记录日期, 工作量, 备注) VALUES (?, ?, ?, ?, ?, ?)",
                        (uid, tid, phase, dt_str, amt, note))
                    st.success(f"提交成功：已更新 {dt_str} 的工作量");
                    st.rerun()


def view_leave_management():
    uid = st.session_state.user['用户ID'];
    role = st.session_state.user['系统角色']
    can_approve_all = (role == '部门领导')
    is_leader = db.query_df(
        f"SELECT 项目ID FROM 项目人员关联表 WHERE 用户ID={uid} AND 项目角色 IN ('项目负责人', '技术负责人', '质量负责人')")
    can_approve_project = not is_leader.empty
    tab_names = []
    if role != '部门领导': tab_names.extend(["我的请假", "申请请假"])
    if can_approve_all or can_approve_project: tab_names.append("审批请假")
    tabs = st.tabs(tab_names)
    current_tab_index = 0
    if "我的请假" in tab_names:
        with tabs[current_tab_index]:
            st.subheader("我的请假记录")
            df_my_leave = db.query_df(
                f"SELECT L.请假ID, L.开始日期, L.结束日期, L.状态, L.申请时间, U.姓名 as 审批人 FROM 请假申请表 L LEFT JOIN 用户信息表 U ON L.审批人ID = U.用户ID WHERE L.申请人ID = {uid} ORDER BY L.申请时间 DESC")
            if not df_my_leave.empty:
                st.dataframe(utils.add_idx(df_my_leave), hide_index=True, use_container_width=True)
            else:
                st.info("暂无请假记录")
            current_tab_index += 1
    if "申请请假" in tab_names:
        with tabs[current_tab_index]:
            st.subheader("提交请假申请")
            with st.form("leave_form"):
                c1, c2 = st.columns(2);
                start_dt = c1.date_input("开始日期", date.today());
                end_dt = c2.date_input("结束日期", date.today())
                if st.form_submit_button("提交申请", type="primary"):
                    if end_dt < start_dt:
                        st.error("结束日期不能早于开始日期")
                    else:
                        overlap = db.query_df(
                            f"SELECT 1 FROM 请假申请表 WHERE 申请人ID={uid} AND 状态 IN ('待审批', '已批准') AND ((开始日期 <= '{start_dt}' AND 结束日期 >= '{start_dt}') OR (开始日期 <= '{end_dt}' AND 结束日期 >= '{end_dt}') OR (开始日期 >= '{start_dt}' AND 结束日期 <= '{end_dt}'))")
                        if not overlap.empty:
                            st.error("该时间段内已有待审批或已批准的请假申请，请检查日期")
                        else:
                            db.run_sql("INSERT INTO 请假申请表 (申请人ID, 开始日期, 结束日期) VALUES (?, ?, ?)",
                                       (uid, str(start_dt), str(end_dt))); st.success(
                                "申请已提交，请等待审批"); st.rerun()
        current_tab_index += 1
    if "审批请假" in tab_names:
        with tabs[current_tab_index]:
            st.subheader("审批请假")
            sql_base = f"SELECT L.请假ID, L.申请人ID, U.姓名 as 申请人, U.系统角色 as 申请人角色, L.开始日期, L.结束日期, L.申请时间 FROM 请假申请表 L JOIN 用户信息表 U ON L.申请人ID = U.用户ID WHERE L.状态 = '待审批'"
            if can_approve_all:
                df_pending = db.query_df(sql_base)
            elif can_approve_project:
                project_ids = ",".join([str(x) for x in is_leader['项目ID'].tolist()])
                df_pending = db.query_df(
                    sql_base + f" AND L.申请人ID IN (SELECT DISTINCT S.作业人员ID FROM 任务阶段进度表 S JOIN 子任务表 T ON S.子任务ID = T.子任务ID WHERE T.项目ID IN ({project_ids})) AND U.系统角色 IN ('本部门作业员', '公司作业员')")
            else:
                df_pending = pd.DataFrame()
            if not df_pending.empty:
                st.info(f"共有 {len(df_pending)} 条待审批申请")
                for _, row in df_pending.iterrows():
                    c1, c2, c3 = st.columns([3, 1, 1])
                    c1.write(f"**{row['申请人']}** ({row['申请人角色']})");
                    c1.write(f"📅 {row['开始日期']} 至 {row['结束日期']}")
                    if row['申请人ID'] == uid:
                        c3.warning("本人申请")
                    else:
                        btn_col1, btn_col2 = st.columns(2);
                        key_approve = f"approve_{row['请假ID']}";
                        key_reject = f"reject_{row['请假ID']}"
                        if btn_col1.button("批准", key=key_approve, type="primary"):
                            db.run_sql(
                                "UPDATE 请假申请表 SET 状态='已批准', 审批人ID=?, 审批时间=datetime('now') WHERE 请假ID=?",
                                (uid, row['请假ID']))
                            start = pd.to_datetime(row['开始日期']);
                            end = pd.to_datetime(row['结束日期'])
                            conn = db.get_conn();
                            cursor = conn.cursor()
                            current_date = start
                            while current_date <= end:
                                d_str = current_date.strftime('%Y-%m-%d')
                                cursor.execute("DELETE FROM 考勤记录表 WHERE 用户ID=? AND 日期=?",
                                               (row['申请人ID'], d_str))
                                cursor.execute(
                                    "INSERT INTO 考勤记录表 (用户ID, 日期, 状态, 修改人ID) VALUES (?, ?, '请假', ?)",
                                    (row['申请人ID'], d_str, uid))
                                current_date += timedelta(days=1)
                            conn.commit();
                            conn.close()
                            st.success(f"已批准 {row['申请人']} 的请假，并已更新考勤记录");
                            st.rerun()
                        if btn_col2.button("驳回", key=key_reject):
                            db.run_sql(
                                "UPDATE 请假申请表 SET 状态='已驳回', 审批人ID=?, 审批时间=datetime('now') WHERE 请假ID=?",
                                (uid, row['请假ID']))
                            st.warning(f"已驳回 {row['申请人']} 的请假");
                            st.rerun()
                    st.divider()
            else:
                st.info("暂无待审批的请假申请")
