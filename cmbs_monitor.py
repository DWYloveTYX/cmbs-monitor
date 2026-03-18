import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import requests
import os

# ---------------------- 1. 页面基础配置 ----------------------
st.set_page_config(
    page_title="CMBS危机监测系统（全功能版）",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------- 2. 核心配置：替换成你自己的美联储API Key！！！ ----------------------
FRED_API_KEY = "b8d055d2eb463ab907a4e5304d163855" 

# ---------------------- 3. 历史数据文件路径（保存在桌面，永久不丢失） ----------------------
DESKTOP_PATH = os.path.join(os.path.expanduser("~"), "Desktop")
HISTORY_DATA_FILE = os.path.join(DESKTOP_PATH, "cmbs_history_data.csv")

# ---------------------- 4. 初始化：加载/创建历史数据文件 ----------------------
# 默认初始历史数据（你报告里的真实数据）
DEFAULT_INDICATORS = [
    {
        "id": 1,
        "name": "CMBS底层贷款DSCR<1.2占比",
        "priority": "第一优先级：先行指标",
        "category": "先行指标",
        "core_logic": "衡量租金现金流能否覆盖还款，占比过高意味着违约风险上升",
        "unit": "%",
        "yellow_threshold": 30.0,
        "orange_threshold": 40.0,
        "red_threshold": 50.0,
        "direction": "up",
        "data_source": "Trepp月度CMBS监测报告（手动更新）",
        "update_type": "manual",
        "initial_history": [28.5, 29.2, 30.1, 31.5, 32.1]
    },
    {
        "id": 2,
        "name": "美国商业地产NOI同比增速",
        "priority": "第一优先级：先行指标",
        "category": "先行指标",
        "core_logic": "商业地产核心经营性现金流，持续下滑直接击穿安全垫",
        "unit": "%",
        "yellow_threshold": -5.0,
        "orange_threshold": -10.0,
        "red_threshold": -15.0,
        "direction": "down",
        "data_source": "RCA、美联储金融稳定报告（手动更新）",
        "update_type": "manual",
        "initial_history": [-6.2, -7.1, -7.8, -8.0, -8.3]
    },
    {
        "id": 3,
        "name": "商业地产到期债务再融资成功率",
        "priority": "第一优先级：先行指标",
        "category": "先行指标",
        "core_logic": "CMBS本金偿还90%依赖再融资，成功率过低意味着批量违约",
        "unit": "%",
        "yellow_threshold": 80.0,
        "orange_threshold": 70.0,
        "red_threshold": 60.0,
        "direction": "down",
        "data_source": "美国抵押贷款银行家协会（MBA）（手动更新）",
        "update_type": "manual",
        "initial_history": [75.3, 72.1, 70.5, 69.2, 68.2]
    },
    {
        "id": 4,
        "name": "CMBS BBB级夹层档OAS利差",
        "priority": "第二优先级：同步放大指标",
        "category": "同步放大指标",
        "core_logic": "嵌套杠杆风险的核心定价，利差飙升意味着融资性现金流断裂",
        "unit": "BP",
        "yellow_threshold": 500,
        "orange_threshold": 1000,
        "red_threshold": 1500,
        "direction": "up",
        "data_source": "ICE美银CMBS指数（手动更新）",
        "update_type": "manual",
        "initial_history": [720, 785, 850, 920, 987]
    },
    {
        "id": 5,
        "name": "美国银行超额准备金余额同比增速",
        "priority": "第三优先级：传染确认指标",
        "category": "传染确认指标",
        "core_logic": "银行应对挤兑的安全垫，持续下滑意味着现金流紧张",
        "unit": "%",
        "yellow_threshold": -5.0,
        "orange_threshold": -10.0,
        "red_threshold": -20.0,
        "direction": "down",
        "data_source": "美联储H.8报告（自动更新）",
        "update_type": "auto",
        "fred_code": "EXCSRESNS",
        "initial_history": [-8.2, -9.5, -10.1, -10.8, -11.4]
    },
    {
        "id": 6,
        "name": "10年期美债收益率",
        "priority": "核心催化剂",
        "category": "核心催化剂",
        "core_logic": "CMBS危机的核心催化剂，既是定价锚也是美债信用风向标",
        "unit": "%",
        "yellow_threshold": 4.0,
        "orange_threshold": 4.5,
        "red_threshold": 5.0,
        "direction": "up",
        "data_source": "美联储FRED（自动更新）",
        "update_type": "auto",
        "fred_code": "GS10",
        "initial_history": [3.92, 3.98, 4.05, 4.15, 4.26]
    },
    {
        "id": 7,
        "name": "FRA-OIS利差",
        "priority": "第三优先级：传染确认指标",
        "category": "传染确认指标",
        "core_logic": "全球银行间美元借贷风险溢价，利差飙升意味着流动性危机",
        "unit": "BP",
        "yellow_threshold": 50,
        "orange_threshold": 100,
        "red_threshold": 200,
        "direction": "up",
        "data_source": "美联储FRED（自动更新）",
        "update_type": "auto",
        "fred_code": "FRIOIS",
        "initial_history": [32.5, 35.2, 40.1, 45.3, 48.7]
    },
    {
        "id": 8,
        "name": "VIX恐慌指数",
        "priority": "第四优先级：危机确认指标",
        "category": "危机确认指标",
        "core_logic": "全市场恐慌情绪指标，突破80意味着极端恐慌",
        "unit": "",
        "yellow_threshold": 30,
        "orange_threshold": 50,
        "red_threshold": 80,
        "direction": "up",
        "data_source": "美联储FRED（自动更新）",
        "update_type": "auto",
        "fred_code": "VIXCLS",
        "initial_history": [19.2, 20.5, 21.3, 22.1, 22.7]
    }
]

# 加载或创建历史数据
def load_history_data():
    if os.path.exists(HISTORY_DATA_FILE):
        # 如果文件存在，读取CSV
        df = pd.read_csv(HISTORY_DATA_FILE)
        return df
    else:
        # 如果文件不存在，用默认数据创建
        data_rows = []
        for ind in DEFAULT_INDICATORS:
            # 生成初始历史时间点（近5期）
            base_date = datetime.now()
            for i, val in enumerate(ind["initial_history"]):
                # 手动更新指标用月度间隔，自动更新用周期间隔
                if ind["update_type"] == "manual":
                    date = (base_date - timedelta(days=(4-i)*30)).strftime("%Y-%m")
                else:
                    date = (base_date - timedelta(days=(4-i)*7)).strftime("%Y-%m-%d")
                data_rows.append({
                    "indicator_id": ind["id"],
                    "indicator_name": ind["name"],
                    "date": date,
                    "value": val
                })
        df = pd.DataFrame(data_rows)
        
        return df

# 初始化session_state
if "history_df" not in st.session_state:
    st.session_state.history_df = load_history_data()
if "indicators" not in st.session_state:
    st.session_state.indicators = DEFAULT_INDICATORS

# ---------------------- 5. 美联储API自动获取函数 ----------------------
@st.cache_data(ttl=3600)  # 缓存1小时
def get_fred_data(series_id, limit=5):
    """从美联储FRED获取单个指标的最新数据"""
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={FRED_API_KEY}&file_type=json&sort_order=desc&limit={limit}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        observations = data["observations"][::-1]
        history = []
        for obs in observations:
            if obs["value"] != ".":
                history.append(float(obs["value"]))
            else:
                history.append(0.0)
        current = history[-1] if history else 0.0
        return current, history
    except Exception as e:
        st.warning(f"自动获取{series_id}失败，使用备用数据：{str(e)}")
        # 找默认数据里的备用值
        for ind in DEFAULT_INDICATORS:
            if ind.get("fred_code") == series_id:
                return ind["initial_history"][-1], ind["initial_history"]
        return 0.0, [0.0]*5

# ---------------------- 6. 页面顶部：一键刷新+更新时间 ----------------------
st.title("美国CMBS危机跟踪与系统性风险监测（全功能版）")
col_refresh, col_time = st.columns([1, 3])
with col_refresh:
    refresh_btn = st.button("🔄 一键刷新所有自动数据", type="primary")
with col_time:
    st.write(f"最后更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.markdown("---")

# 点击刷新按钮时，清空缓存，重新拉取自动数据
if refresh_btn:
    st.cache_data.clear()
    st.success("已刷新所有自动更新指标！")

# ---------------------- 7. 侧边栏：零代码手动更新面板 ----------------------
st.sidebar.title("📊 CMBS危机监测系统")
st.sidebar.markdown("---")
st.sidebar.subheader("🛠️ 零代码手动更新面板")
st.sidebar.caption("（Trepp、MBA等无免费API的指标，在这里直接输入新数据）")

# 选择要更新的指标
manual_indicators = [ind for ind in st.session_state.indicators if ind["update_type"] == "manual"]
selected_ind_name = st.sidebar.selectbox(
    "选择要更新的指标",
    options=[ind["name"] for ind in manual_indicators]
)

# 找到选中的指标
selected_ind = next(ind for ind in manual_indicators if ind["name"] == selected_ind_name)

# 显示当前最新值
current_val = st.session_state.history_df[
    st.session_state.history_df["indicator_id"] == selected_ind["id"]
]["value"].iloc[-1]
st.sidebar.metric(f"当前{selected_ind['name']}", f"{current_val}{selected_ind['unit']}")

# 输入新数据
new_val = st.sidebar.number_input(
    f"输入{selected_ind['name']}的最新值",
    value=float(current_val),
    format="%.4f"
)

# 保存按钮
if st.sidebar.button("💾 保存并更新历史数据", type="secondary"):
    # 生成新的时间点
    if selected_ind["update_type"] == "manual":
        new_date = datetime.now().strftime("%Y-%m")
    else:
        new_date = datetime.now().strftime("%Y-%m-%d")
    
    # 添加新数据到历史DataFrame
    new_row = pd.DataFrame({
        "indicator_id": [selected_ind["id"]],
        "indicator_name": [selected_ind["name"]],
        "date": [new_date],
        "value": [new_val]
    })
    st.session_state.history_df = pd.concat([st.session_state.history_df, new_row], ignore_index=True)
    
    # 保存到CSV文件
    st.session_state.history_df.to_csv(HISTORY_DATA_FILE, index=False)
    
    st.sidebar.success(f"已成功更新{selected_ind['name']}！历史数据已永久保存到桌面。")

st.sidebar.markdown("---")

# ---------------------- 8. 获取所有指标的最新数据 ----------------------
# 构建完整的指标数据列表
full_indicators_data = []
for ind in st.session_state.indicators:
    if ind["update_type"] == "auto":
        # 自动更新指标：从API获取
        current, history = get_fred_data(ind["fred_code"])
        # 更新历史数据（如果API有新数据）
        if history:
            # 只保留最近5期
            recent_history = history[-5:]
        else:
            recent_history = ind["initial_history"]
    else:
        # 手动更新指标：从本地CSV获取
        ind_history = st.session_state.history_df[
            st.session_state.history_df["indicator_id"] == ind["id"]
        ]["value"].tolist()
        current = ind_history[-1]
        recent_history = ind_history[-5:]  # 只保留最近5期
    
    # 添加到完整列表
    full_indicators_data.append({
        **ind,
        "current_value": current,
        "history_data": recent_history
    })

# ---------------------- 9. 辅助函数：预警状态判断 ----------------------
def get_alert_status(value, yellow, orange, red, direction):
    if direction == "up":
        if value >= red:
            return "red", "🔴 红色预警"
        elif value >= orange:
            return "orange", "🟠 橙色预警"
        elif value >= yellow:
            return "yellow", "🟡 黄色预警"
        else:
            return "green", "🟢 安全"
    else:
        if value <= red:
            return "red", "🔴 红色预警"
        elif value <= orange:
            return "orange", "🟠 橙色预警"
        elif value <= yellow:
            return "yellow", "🟡 黄色预警"
        else:
            return "green", "🟢 安全"

# ---------------------- 10. 计算整体风险评级 ----------------------
def calculate_overall_rating(indicators):
    red_count = 0
    orange_count = 0
    yellow_count = 0
    for ind in indicators:
        color, _ = get_alert_status(
            ind["current_value"],
            ind["yellow_threshold"],
            ind["orange_threshold"],
            ind["red_threshold"],
            ind["direction"]
        )
        if color == "red":
            red_count += 1
        elif color == "orange":
            orange_count += 1
        elif color == "yellow":
            yellow_count += 1
    if red_count >= 2:
        return "🔴 红色预警", "★★★★★", "全面危机期"
    elif orange_count >= 2 or red_count >= 1:
        return "🟠 橙色预警", "★★★☆☆", "风险升级期"
    elif yellow_count >= 2:
        return "🟡 黄色预警", "★★☆☆☆", "风险酝酿期"
    else:
        return "🟢 安全", "★☆☆☆☆", "安全区间"

# ---------------------- 11. 侧边栏：整体风险概览 ----------------------
overall_status, overall_rating, overall_phase = calculate_overall_rating(full_indicators_data)
st.sidebar.metric("当前整体风险评级", overall_rating)
st.sidebar.subheader(f"风险阶段：{overall_status}")
st.sidebar.write(f"当前处于：**{overall_phase}**")
st.sidebar.markdown("---")

# 侧边栏预警统计
st.sidebar.subheader("预警指标统计")
alert_counts = {"red": 0, "orange": 0, "yellow": 0, "green": 0}
for ind in full_indicators_data:
    color, _ = get_alert_status(
        ind["current_value"],
        ind["yellow_threshold"],
        ind["orange_threshold"],
        ind["red_threshold"],
        ind["direction"]
    )
    alert_counts[color] += 1
col1, col2, col3, col4 = st.sidebar.columns(4)
col1.metric("🔴", alert_counts["red"])
col2.metric("🟠", alert_counts["orange"])
col3.metric("🟡", alert_counts["yellow"])
col4.metric("🟢", alert_counts["green"])

# ---------------------- 12. 主页面：指标卡片展示 ----------------------
# 按优先级分组展示指标
priority_groups = {}
for ind in full_indicators_data:
    if ind["priority"] not in priority_groups:
        priority_groups[ind["priority"]] = []
    priority_groups[ind["priority"]].append(ind)

for priority, indicators in priority_groups.items():
    st.subheader(priority)
    for i in range(0, len(indicators), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(indicators):
                ind = indicators[i + j]
                with cols[j]:
                    # 获取预警状态
                    color, status_text = get_alert_status(
                        ind["current_value"],
                        ind["yellow_threshold"],
                        ind["orange_threshold"],
                        ind["red_threshold"],
                        ind["direction"]
                    )
                    
                    # 指标卡片
                    st.markdown(f"### {ind['name']}")
                    st.caption(ind["core_logic"])
                    
                    # 显示当前值和预警状态
                    val_col, status_col = st.columns([1, 1])
                    with val_col:
                        st.metric(
                            label="当前值",
                            value=f"{ind['current_value']:.4f}{ind['unit']}"
                        )
                    with status_col:
                        st.markdown(f"### {status_text}")
                    
                    # 绘制历史走势图（从本地CSV读取完整历史）
                    ind_full_history = st.session_state.history_df[
                        st.session_state.history_df["indicator_id"] == ind["id"]
                    ]
                    fig = px.line(
                        ind_full_history,
                        x="date",
                        y="value",
                        title="完整历史走势",
                        height=200
                    )
                    
                    # 添加预警阈值线
                    fig.add_hline(y=ind["yellow_threshold"], line_dash="dash", line_color="orange", annotation_text="黄警")
                    fig.add_hline(y=ind["orange_threshold"], line_dash="dash", line_color="red", annotation_text="橙警")
                    fig.add_hline(y=ind["red_threshold"], line_dash="dash", line_color="darkred", annotation_text="红警")
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # 数据来源
                    st.caption(f"数据来源：{ind['data_source']}")
                    st.markdown("---")
