import asyncio
import edge_tts
import os

# 输出目录
output_dir = "docs/voiceover"
os.makedirs(output_dir, exist_ok=True)

# 语音设置
VOICE = "zh-CN-YunxiNeural"
RATE = "+0%"
VOLUME = "+0%"

# 配音稿内容
scripts = [
    {
        "filename": "01_intro.mp3",
        "text": """大家好，今天给大家介绍我开发的AI小说转剧本工具。
这个项目是七牛云×XEngineer暑期实训营6月5-7日活动题目三的作品，目标是帮助小说作者快速将作品改编成剧本。
接下来，我会演示这个工具的主要功能和技术亮点。"""
    },
    {
        "filename": "02_basic_convert.mp3",
        "text": """首先，我们来看基础转换功能。
我在文本框中输入一段小说文本，这是一个咖啡馆的对话场景。
点击开始转换按钮，可以看到YAML文本是逐步出现的，这就是流式输出效果。
用户可以实时看到AI的生成过程，不用等待全部完成。
转换完成后，自动切换到剧本预览页面，显示了几个场景。"""
    },
    {
        "filename": "03_edit.mp3",
        "text": """接下来，我们来看剧本预览和编辑功能。
点击编辑按钮进入编辑模式，可以看到可编辑的元素都显示了虚线边框。
我来修改一下林小雨的台词。
大家可以看到，修改过的文字显示为红色标注，这样用户可以清楚地看到哪些内容被修改过。
点击保存按钮，YAML源码会自动同步更新。"""
    },
    {
        "filename": "04_scene_nav.mp3",
        "text": """对于长篇剧本，我们提供了分场景导航功能。
左侧显示场景列表，包含场景编号、地点和时间。
我点击第二个场景，可以看到右侧预览自动滚动到对应位置。
反过来，我滚动右侧预览，左侧场景列表会自动高亮当前场景。
我们还支持拖拽调整左右分屏的宽度，用户可以根据自己的喜好调整布局。"""
    },
    {
        "filename": "05_file_upload.mp3",
        "text": """除了手动输入，用户还可以上传文件。
我们支持TXT、DOCX、PDF三种格式。
系统会自动提取文本内容，并填入输入框。
这样用户可以直接上传已有的小说文件，非常方便。"""
    },
    {
        "filename": "06_export.mp3",
        "text": """我们支持三种导出格式：YAML、JSON和DOCX。
YAML和JSON格式适合开发者使用，可以进一步处理或集成到其他系统。
DOCX格式是Word文档，适合普通用户。
大家可以看到，文档采用好莱坞专业格式。
这样导出的文档可以直接用于专业场景。"""
    },
    {
        "filename": "07_character.mp3",
        "text": """角色管理功能可以自动从剧本中提取所有角色信息。
大家可以看到，右侧显示了角色列表，包含角色名称、出场场景数和台词数量。
我点击林小雨这个角色，可以看到剧本中林小雨的内容被高亮显示，其他内容变淡。
这个功能对于分析剧本结构和角色戏份非常有帮助。"""
    },
    {
        "filename": "08_batch.mp3",
        "text": """对于长篇小说，系统会自动分章节处理。
我输入一段多章节的小说文本，点击转换。
大家可以看到，进度条会实时更新，显示当前处理到第几章、总章节数和百分比。
这样即使是很长的小说，用户也能清楚地看到转换进度。
转换完成后，进度条自动消失。"""
    },
    {
        "filename": "09_api_settings.mp3",
        "text": """最后，我们来看API设置功能。
用户可以使用自己的API密钥，也可以使用服务器默认密钥。
我们支持任何兼容OpenAI协议的API服务，包括小米MiMo、DeepSeek、GPT等。
这样用户可以根据自己的需求选择不同的AI模型。"""
    },
    {
        "filename": "10_tech_highlights.mp3",
        "text": """接下来，我来介绍这个项目的技术亮点。
第一，流式输出。使用Server-Sent Events技术，AI生成的内容会实时推送到前端，体验非常好。
第二，多层YAML解析。我们实现了多层解析策略，可以最大程度保证解析成功。
第三，时序保持。我们使用items列表来保持动作和对话的时间顺序，这是我们的核心创新点。
第四，角色自动提取。使用智能提取算法，可以从剧本中自动识别所有角色。
第五，分批处理与进度推送。对于长篇小说，系统采用分章处理策略，提升了用户体验。"""
    },
    {
        "filename": "11_conclusion.mp3",
        "text": """总结一下，这个AI小说转剧本工具具有以下特点：
功能完整，覆盖了题目要求的所有功能。
持续开发，从开题至今，我们保持了稳定的PR和commit频率。
代码质量，架构清晰、代码健壮、测试覆盖完整。
创新设计，使用items列表保持动作和对话的时间顺序。
项目的代码已经开源在GitHub上，欢迎大家Star和Fork。
感谢大家观看，如果觉得有用，欢迎点赞和关注。
我们下期再见！"""
    }
]

async def generate_voiceover():
    """生成所有配音文件"""
    for script in scripts:
        output_path = os.path.join(output_dir, script["filename"])
        print(f"正在生成: {script['filename']}...")

        communicate = edge_tts.Communicate(
            text=script["text"],
            voice=VOICE,
            rate=RATE,
            volume=VOLUME
        )

        await communicate.save(output_path)
        print(f"  完成: {output_path}")

    print(f"\n所有配音文件已生成到 {output_dir} 目录")

if __name__ == "__main__":
    asyncio.run(generate_voiceover())
