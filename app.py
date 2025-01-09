import streamlit as st
import pandas as pd
import time
import io
from PIL import Image
import os

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
        
        # 获取重复的客户编号
        duplicates = community_df[community_df.duplicated(['客户编号'], keep=False)]
        
        if not duplicates.empty:
            # 对重复的客户编号进行处理
            for original_id in duplicates['客户编号'].unique():
                # 获取当前重复编号的所有行
                duplicate_rows = community_df[community_df['客户编号'] == original_id]
                
                # 为重复的行生成新的编号（在原编号后添加-1, -2等）
                for i, idx in enumerate(duplicate_rows.index[1:], 1):
                    new_id = f"{original_id}-{i}"
                    df.loc[idx, '修改后客户编号'] = new_id
    
    # 只保留需要的列
    df = df[['客户编号', '修改后客户编号']]
    
    end_time = time.time()  # 记录结束时间
    processing_time = end_time - start_time
    return df, processing_time

def main():
    # 设置页面配置
    st.set_page_config(
        page_title="客户编号重复处理",
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
            border-radius: 5px;
            height: 3em;
            background-color: #ff4b4b;
            color: white;
        }
        .stProgress > div > div > div > div {
            background-color: #ff4b4b;
        }
        </style>
    """, unsafe_allow_html=True)

    # 创建三列布局
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        # 创建两列布局用于说明和示例
        instruction_col, example_col = st.columns(2)
        
        with instruction_col:
            st.markdown("""
                <div style='background-color: #f0f2f6; padding: 1rem; border-radius: 10px; margin-bottom: 2rem;'>
                    <h4 style='color: #ff4b4b;'>📝 使用说明</h4>
                    <p>1. 仅保留一列数据，将所有编号汇总到一张表上，第一行<b>客户编号</b></p>
                    <p>2. 按照0-9 A-Z替换，如替换完仍然有重复，请手工手改</p>
                </div>
            """, unsafe_allow_html=True)

        with example_col:
            # 显示示例图片
            example_image = Image.open("example.png")
            st.image(example_image, use_container_width=True)

        # 文件上传
        st.markdown("<h4 style='color: #ff4b4b; margin-top: 2rem;'>📤 上传文件</h4>", unsafe_allow_html=True)
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
                    st.markdown("<h4 style='color: #ff4b4b;'>🔍 处理结果预览</h4>", unsafe_allow_html=True)
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
