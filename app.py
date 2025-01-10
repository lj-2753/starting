import streamlit as st
import pandas as pd
import time
import io

def process_duplicates(df):
    """
    处理DataFrame中的重复客户编号，为每个社区生成唯一的客户编号。

    :param df: 包含客户编号的DataFrame
    :return: 处理后的DataFrame
    """
    start_time = time.time()  # 记录开始时间
    
    # 确保只保留需要的列
    if '客户编号' not in df.columns:
        raise ValueError("上传的Excel文件必须包含'客户编号'列")
    
    # 只保留客户编号列
    df = df[['客户编号']]
    
    # 从客户编号中提取前8位作为社区编号
    df['社区编号'] = df['客户编号'].astype(str).str[:8]
    
    # 将小写x转换为大写X
    df['客户编号'] = df['客户编号'].astype(str).apply(lambda x: x[:-1] + 'X' if x.endswith('x') else x)
    
    # 在第二列插入新的列'修改后客户编号'，初始值为原'客户编号'
    if '修改后客户编号' not in df.columns:
        df.insert(1, '修改后客户编号', df['客户编号'])
    
    # 按社区分组处理
    for community in df['社区编号'].unique():
        # 创建当前社区的掩码
        community_mask = df['社区编号'] == community
        
        # 根据掩码筛选出当前社区的数据并复制
        community_df = df[community_mask].copy()
        
        # 找出所有重复项
        seen_ids = set()
        for idx in community_df.index:
            # 获取原始客户编号
            original_id = df.loc[idx, '客户编号']
            # 取除最后一位外的部分作为基础ID
            base_id = original_id[:-1]
            
            if original_id in seen_ids:
                # 如果原始ID已存在，则生成新ID直到找到未使用的
                for suffix in list('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
                    new_id = base_id + suffix
                    if new_id not in seen_ids:
                        # 更新DataFrame中的'修改后客户编号'
                        df.loc[idx, '修改后客户编号'] = new_id
                        # 将新ID加入已见集合
                        seen_ids.add(new_id)
                        break
            else:
                # 如果原始ID不存在于已见集合中，直接加入
                seen_ids.add(original_id)
    
    # 只保留需要的列
    df = df[['客户编号', '修改后客户编号']]
    
    end_time = time.time()  # 记录结束时间
    processing_time = end_time - start_time
    return df, processing_time

def main():
    # 设置页面配置
    st.set_page_config(
        page_title="客户编号处理工具",
        page_icon="🔄",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # 自定义CSS样式
    st.markdown("""
        <style>
        .main {
            padding: 2rem;
        }
        .stButton>button {
            width: 100%;
            border-radius: 8px;
            height: 3em;
            background-color: #FF4B4B;
            color: white;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            background-color: #FF3333;
            box-shadow: 0 4px 8px rgba(255, 75, 75, 0.2);
        }
        .stProgress > div > div > div > div {
            background-color: #FF4B4B;
        }
        .instruction-box {
            background-color: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            margin-bottom: 2rem;
            border: 1px solid #f0f2f6;
        }
        h1, h4 {
            font-family: 'Segoe UI', sans-serif;
        }
        </style>
    """, unsafe_allow_html=True)

    # 页面标题
    st.markdown("""
        <h1 style='text-align: center; color: #FF4B4B; margin-bottom: 2rem; font-weight: 600; font-size: 2.5rem;'>
            客户编号重复处理 🔄
        </h1>
    """, unsafe_allow_html=True)

    # 创建三列布局
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        # 使用说明
        st.markdown("""
            <div class='instruction-box'>
                <h4 style='color: #FF4B4B; margin-bottom: 1rem;'>📝 使用说明</h4>
                <p style='color: #444; line-height: 1.6;'>1. 仅保留一列数据，将所有编号汇总到一张表上，第一行<b>客户编号</b></p>
                <p style='color: #444; line-height: 1.6;'>2. 按照0-9 A-Z替换，如替换完仍然有重复，请手工手改</p>
            </div>
        """, unsafe_allow_html=True)

        # 文件上传组件
        uploaded_file = st.file_uploader("选择Excel文件上传", type=['xlsx', 'xls'])

        if uploaded_file is not None:
            try:
                with st.spinner('正在处理数据...'):
                    # 读取上传的文件
                    df = pd.read_excel(uploaded_file)
                    
                    # 处理数据
                    processed_df, processing_time = process_duplicates(df)
                    
                    # 显示处理时间
                    st.success(f"✨ 处理完成！用时: {processing_time:.2f} 秒")
                    
                    # 显示处理后的数据
                    st.markdown("<h4 style='color: #FF4B4B; margin: 2rem 0 1rem 0;'>🔍 处理结果预览</h4>", unsafe_allow_html=True)
                    st.dataframe(processed_df, use_container_width=True)
                    
                    # 准备下载处理后的文件
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        processed_df.to_excel(writer, index=False)
                    
                    # 下载按钮
                    st.download_button(
                        label="📥 下载处理后的文件",
                        data=output.getvalue(),
                        file_name="processed_data.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                
            except Exception as e:
                st.error(f"❌ 处理文件时出错: {str(e)}")

if __name__ == "__main__":
    main()
