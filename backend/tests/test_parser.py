from backend.app.parser import split_chapters, extract_characters


class TestSplitChapters:
    def test_chinese_chapter_numbers(self):
        text = "第一章 开始\n\n这是第一章内容\n\n第二章 结束\n\n这是第二章内容"
        chapters = split_chapters(text)
        assert len(chapters) == 2
        assert chapters[0]["title"] == "第一章 开始"
        assert chapters[1]["title"] == "第二章 结束"

    def test_digit_chapter_numbers(self):
        text = "第1章 开始\n\n内容一\n\n第2章 中间\n\n内容二\n\n第3章 结束\n\n内容三"
        chapters = split_chapters(text)
        assert len(chapters) == 3
        assert chapters[0]["title"] == "第1章 开始"
        assert chapters[2]["title"] == "第3章 结束"

    def test_english_chapters(self):
        text = "Chapter 1 Beginning\n\nHello\n\nChapter 2 End\n\nWorld"
        chapters = split_chapters(text)
        assert len(chapters) == 2
        assert chapters[0]["title"] == "Chapter 1 Beginning"

    def test_no_chapters(self):
        text = "这是一段没有章节的文本内容"
        chapters = split_chapters(text)
        assert len(chapters) == 1
        assert chapters[0]["title"] == "序章"
        assert "没有章节" in chapters[0]["text"]

    def test_empty_text(self):
        chapters = split_chapters("")
        assert len(chapters) == 1
        assert chapters[0]["title"] == "全文"

    def test_chapter_text_preserved(self):
        text = "第一章 测试\n\n对话内容\n动作描写"
        chapters = split_chapters(text)
        assert "对话内容" in chapters[0]["text"]
        assert "动作描写" in chapters[0]["text"]


class TestExtractCharacters:
    def test_basic_characters(self):
        text = '林小雨说："你好。"陈默答："你好。"'
        characters = extract_characters(text)
        assert "林小雨" in characters
        assert "陈默" in characters

    def test_no_characters(self):
        text = "没有对话的叙述文本"
        characters = extract_characters(text)
        assert len(characters) == 0

    def test_deduplication(self):
        text = '林小雨说："一"林小雨说："二"'
        characters = extract_characters(text)
        assert characters.count("林小雨") == 1
