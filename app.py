import streamlit as st
import fal_client
import os
import asyncio
import tempfile  # 新增：用于处理临时文件

# 页面配置
st.set_page_config(page_title="Nano Banana 写真馆", layout="wide")

st.title("📷 Nano Banana 智能写真馆")
st.markdown("上传一张照片，AI 自动为你生成 6 种不同风格的写真大片。")

# 侧边栏：API Key 设置
api_key = st.secrets.get("FAL_KEY")
if not api_key:
    api_key = st.sidebar.text_input("请输入你的 FAL_KEY", type="password")
    if api_key:
        os.environ["FAL_KEY"] = api_key
else:
    os.environ["FAL_KEY"] = api_key

# 定义 6 种风格
STYLES = {
    "1_职业肖像": "Professional LinkedIn headshot, business attire, confident smile, studio lighting, neutral grey background, high quality, 8k.",
    "2_时尚写真": "High fashion photography, vogue magazine style, trendy outfit, dynamic pose, dramatic studio lighting.",
    "3_美术馆迷失": "Candid shot standing in a modern art gallery, looking at abstract painting, 'lost in art' vibe, soft ambient lighting.",
    "4_黑白艺术": "Black and white fine art photography, high contrast, dramatic shadows, noir style, grainy texture, emotional gaze.",
    "5_美式封面": "American magazine cover style, close-up portrait, bold colors, studio lighting, sharp details, commercial photography.",
    "6_电影肖像": "Cinematic movie shot, anamorphic lens, shallow depth of field, Wong Kar-wai style, dramatic lighting."
}

# 异步生成函数
async def generate_single_image(image_url, style_name, prompt):
    try:
        # 使用 flux 图生图模型
        handler = await fal_client.submit_async(
            "fal-ai/flux/dev/image-to-image", 
            arguments={
                "image_url": image_url,
                "prompt": prompt,
                "strength": 0.75, 
                "guidance_scale": 7.5
            }
        )
        result = await handler.get()
        return style_name, result["images"][0]["url"]
    except Exception as e:
        # 打印错误以便调试
        print(f"Error generating {style_name}: {e}")
        return style_name, None

async def run_all_generations(image_url):
    tasks = []
    for name, prompt in STYLES.items():
        tasks.append(generate_single_image(image_url, name, prompt))
    return await asyncio.gather(*tasks)

# 上传组件
uploaded_file = st.file_uploader("请上传人物照片 (JPG/PNG)", type=["jpg", "png", "jpeg"])

if uploaded_file and api_key:
    # 展示原图
    st.image(uploaded_file, caption="原图", width=300)
    
    if st.button("✨ 开始生成写真 (消耗积分)"):
        with st.spinner("正在上传图片并请求 AI 模型..."):
            # ================= 修复部分开始 =================
            # 创建临时文件来存储上传的图片
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
                temp_file.write(uploaded_file.getvalue())
                temp_file_path = temp_file.name
            
            try:
                # 传入文件路径，而不是对象
                url = fal_client.upload_file(temp_file_path)
            finally:
                # 上传完成后删除临时文件，保持清洁
                os.remove(temp_file_path)
            # ================= 修复部分结束 =================
            
        # 2. 并行生成
        progress_text = "正在并行绘制 6 张写真，请稍候..."
        my_bar = st.progress(0, text=progress_text)
        
        # 运行异步任务
        results = asyncio.run(run_all_generations(url))
        my_bar.progress(100, text="生成完毕！")
        
        # 3. 展示结果
        st.divider()
        cols = st.columns(3)
        
        for i, (style_name, img_url) in enumerate(results):
            col_idx = i % 3
            with cols[col_idx]:
                if img_url:
                    st.image(img_url, caption=style_name, use_column_width=True)
                else:
                    st.error(f"{style_name} 生成失败")
                    
elif uploaded_file and not api_key:
    st.warning("⚠️ 请先配置 FAL_KEY 才能开始生成。")
