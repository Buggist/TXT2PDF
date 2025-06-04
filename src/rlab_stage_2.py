import os

from reportlab.lib.pagesizes import letter, A4                                  # 页面尺寸
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import Color


def is_halfwidth(char):
    """半角字符unicode编码从0x0021-0x007E，外加空格"""
    code = ord(char)
    if 0x0021 <= code <= 0x007E:
        return True
    elif char == " ":
        return True
    return False

def split_lines_by_pagewidth(text, size, content_width):
    """获取按渲染后文字宽度与页面宽度分行后的行列表"""
    lines = []
    width = 0
    index = 0
    for char in text[:]:
        if is_halfwidth(char):
            width += size / 2
        else:
            width += size

        if width > content_width:
            width = size / 2 if is_halfwidth(char) else size
            lines.append(text[:index])
            text = text[index:]
            index = 1
                
        index += 1
        
    lines.append(text)
    return lines

def get_textwidth(text, size):
    """获取字符串渲染后的宽度"""
    width = 0
    for char in text:
        if is_halfwidth(char):
            width += size / 2
        else:
            width += size
    return width

def remove_char(s, index):
    """返回移除指定索引的字符后的字符串"""
    # 确保索引在字符串长度范围内
    if index < 0 or index >= len(s):
        raise IndexError("索引超出字符串范围")

    # 使用切片移除指定索引的字符
    return s[:index] + s[index+1:]

def insert_string(original_string, index, string_to_insert):
    """返回在指定索引处插入了另一个字符串后的原字符串"""
    # 确保索引在字符串长度范围内
    if index < 0 or index > len(original_string):
        raise IndexError("索引超出字符串范围")

    # 在指定索引位置插入字符串
    return original_string[:index] + string_to_insert + original_string[index:]

def get_visualindex(text, index):
    """获得字符在字符串中的视觉索引。（按照中英文2:1等宽字体）"""
    vindex = 0
    
    for i in range(index):
        if is_halfwidth(text[i]):
            vindex += 1
        else:
            vindex += 2
            
    return vindex

def freeze_tab(text):
    """冻结渲染前文本中的制表符为视觉等长的空格。（按照中英文2:1等宽字体）"""
    tab_length = 8
    offset     = 0
    new_text   = text
    for i in range(len(text)):
        if text[i] == "\t":
            vindex = get_visualindex(new_text, i+offset)                        # 该制表符前面的文本的视觉宽度
            mod = vindex % tab_length
            new_text = remove_char(new_text, i+offset)                          # 移除该匹配到的制表符
            new_text = insert_string(new_text, i+offset, " " * (8-mod))         # 插入与该制表符视觉宽度等宽的若干空格
            offset  += 8 - mod - 1                                              # 校正插入空格可能导致的索引偏移

    return new_text

def get_barefilename(file_path):
    """根据文件路径获得不带拓展名的文件名。"""
    # 使用 os.path.basename 获取文件名（包括后缀）
    file_name_with_ext = os.path.basename(file_path)

    # 使用 os.path.splitext 分离文件名和后缀
    file_name_without_ext, file_ext = os.path.splitext(file_name_with_ext)

    return file_name_without_ext

def cut_extname(file_path):
    # 查找最后一个点号的位置
    last_dot_index = file_path.rfind('.')
    # 如果找到点号，则删除点号及其后的所有字符
    if last_dot_index != -1:
        return file_path[:last_dot_index]
    else:
        # 如果没有找到点号，返回整个字符串
        return file_path
            

class PDF():
    def __init__(self, file_path, font_normal, font_bold, page_size=A4):

        self.file_name = cut_extname(file_path) + ".pdf"
        self.pdf_name  = get_barefilename(file_path)
        
        # 在reportlab中注册字体对象
        pdfmetrics.registerFont(TTFont('normal', font_normal))
        pdfmetrics.registerFont(TTFont('bold', font_bold))

        # 创建文档对象
        self.c = canvas.Canvas(self.file_name, pagesize=page_size)

        # 页面坐标相关配置
        self.page_width, self.page_height = page_size                           # 文档页面长宽
        self.page_margin = 28                                                   # 页边距
        self.pos = [self.page_margin, self.page_height - self.page_margin]      # "写入位置"坐标
        self.line_margin = 4                                                    # 行间距
        self.content_width = self.page_width - 2 * self.page_margin             # 页面内容区域宽度

        # 字号
        ratio = 1.2
        self.heading1_size = int(25 * ratio)
        self.heading2_size = int(20 * ratio)
        self.heading3_size = int(15 * ratio)
        self.content_size  = int(10 * ratio)
        self.doctitle_size = int(40 * ratio)
        self.pagefoot_size = int(10 * ratio)

        # 颜色
        self.color_text = Color(0.1, 0.1, 0.1)
        self.color_h2 = Color(0.6, 0.7, 1)
        self.color_h3 = Color(1, 0.9, 0.6)

        # 跳转标记
        self.page_num = 1                                                       # 页码
        self.write_pagefoot()                                                   # 写页码
        self.c.bookmarkPage("p%s" % self.page_num)                              # 令当前页面可被跳转到
        self.link_num = 0                                                       # 文档中的链接数量，用于给链接编号

        # 标题-页码表
        self.heading_table = []                                                 # 用于写目录，同时存储链接跳转点[["h_text", "hx", page_num], ...]

    def save(self):
        # 保存到本地文件
        self.c.save()

    def write_pagefoot(self):
        # 在页面底部写入页码
        size = self.pagefoot_size
        self.c.setFont('normal', size)
        x = (self.page_width - len(str(self.page_num)) * size) / 2
        y = 10
        self.c.drawString(x, y, str(self.page_num))

    def enter_newpage(self):
        # 创建并进入新的页面
        self.c.showPage()
        self.page_num += 1                                                      # 更新页码
        self.pos = [self.page_margin, self.page_height - self.page_margin]      # 更新"写入位置"坐标
        self.write_pagefoot()                                                   # 写页码
        self.c.bookmarkPage("p%s" % self.page_num)                              # 令当前页面可被跳转到

        self.write_homelink(2)

    def change_page_if_needed(self, size):
        # 判断下一行是否将超出页面内容最大高度，是则进行换页
        if self.pos[1] - size < self.page_margin:
            self.enter_newpage()

    def write_doctitle(self, text="default"):
        # 写入文档标题（自动换页）
        if text=="default":
            text = self.pdf_name
        size = self.doctitle_size
        self.c.setFont('bold', size)
        self.c.drawString(self.pos[0], self.pos[1] - size, text)
        self.enter_newpage()

    def write_content(self, text):
        # 写入内容
        text = freeze_tab(text)
        size = self.content_size
        lines = split_lines_by_pagewidth(text, size, self.content_width)
        self.c.setFont('normal', size)
        for line in lines:
            self.change_page_if_needed(size)
            self.c.drawString(self.pos[0], self.pos[1] - size, line)
            self.pos[1] = self.pos[1] - size - self.line_margin

    def write_h1(self, text, center=False):
        """写入一级标题（不与上一个一级标题的下属内容位于同一页）"""
        # 因为一级标题默认位于页顶，因此没有上方 gap
        original_pos = [self.page_margin, self.page_height - self.page_margin]
        if self.pos[1] < original_pos[1]:
            self.enter_newpage()
            
        size = self.heading1_size
        gap  = int(size // 5)
        self.c.setFont('bold', size)
        self.change_page_if_needed(size)

        # 如果居中
        if center:
            x = (self.page_width - len(str(text)) * size) / 2
        else:
            x = self.pos[0]

        self.c.drawString(x, self.pos[1] - size, text)                          # 写入文字
        self.heading_table.append([text, "h1", self.page_num])                  # 储存标题
        self.pos[1] = self.pos[1] - size - self.line_margin - gap               # 重置“写入位置”

    def write_h2(self, text):
        # 写入二级标题
        size = self.heading2_size
        gap  = int(size // 5)
        self.c.setFont('bold', size)
        self.change_page_if_needed(size)
        self.c.drawString(self.pos[0], self.pos[1] - size - gap, text)          # 写入文字
        self.heading_table.append([text, "h2", self.page_num])                  # 储存标题
        self.pos[1] = self.pos[1] - size - self.line_margin - gap * 2           # 重置“写入位置”

    def write_h2color(self, text):
        # 写入二级标题 - 修改中
        size = self.heading2_size
        gap  = int(size // 5)

        # 绘制矩形
        self.c.setFillColor(self.color_h2)
        x = self.pos[0]
        y = self.pos[1] - gap - size - gap
        width  = self.page_width - 2 * self.page_margin
        height = size
        self.c.rect(x, y, width, height + gap, stroke=0, fill=1)
        self.c.setFillColor(Color(0.1, 0.1, 0.1))

        # 写入文字
        self.c.setFont('bold', size)
        self.change_page_if_needed(size)
        self.c.drawString(self.pos[0], self.pos[1] - size - gap, text)          # 写入文字
        self.heading_table.append([text, "h2", self.page_num])                  # 储存标题
        self.pos[1] = self.pos[1] - size - self.line_margin - gap * 2           # 重置“写入位置”

    def write_h3(self, text):
        # 写入三级标题
        size = self.heading3_size
        gap  = int(size // 5)
        self.c.setFont('bold', size)
        self.change_page_if_needed(size)
        self.c.drawString(self.pos[0], self.pos[1] - size - gap, text)          # 写入文字
        self.heading_table.append([text, "h3", self.page_num])                  # 储存标题
        self.pos[1] = self.pos[1] - size - self.line_margin - gap * 2           # 重置“写入位置”

    def write_h3color(self, text):
        # 写入二级标题 - 修改中
        size = self.heading3_size
        gap  = int(size // 5)

        # 绘制矩形
        self.c.setFillColor(self.color_h3)
        x = self.pos[0]
        y = self.pos[1] - gap - size - gap
        width  = (self.page_width - 2 * self.page_margin) * 0.85
        height = size
        self.c.rect(x, y, width, height + gap, stroke=0, fill=1)
        self.c.setFillColor(Color(0.1, 0.1, 0.1))

        # 写入文字
        self.c.setFont('bold', size)
        self.change_page_if_needed(size)
        self.c.drawString(self.pos[0], self.pos[1] - size - gap, text)          # 写入文字
        self.heading_table.append([text, "h2", self.page_num])                  # 储存标题
        self.pos[1] = self.pos[1] - size - self.line_margin - gap * 2           # 重置“写入位置”

    def write_link(self, text, page_num):
        # 写入链接内容
        size = self.content_size
        self.c.setFont('normal', size)
        self.c.setFillColor(Color(0, 0, 1))
        self.change_page_if_needed(size)
        
        self.c.drawString(self.pos[0], self.pos[1] - size, text)
        self.c.setFillColor(Color(0, 0, 0))
        self.pos[1] = self.pos[1] - size - self.line_margin

        width  = self.pos[0] + get_textwidth(text, size)
        height = self.pos[1] + size
        rect = (self.pos[0], self.pos[1], width, height)
        
        self.link_num += 1
        self.c.linkAbsolute(
            f"link_{self.link_num}",    # 该按钮名为 f"link_{self.link_num}"，其作用不明
            f"p{page_num}",             # 跳转到 f"p{page_num}" 目标点所在的页面
            rect,                       # 跳转按钮在激活页面上占据的矩形区域
            thickness=0,                # 跳转按钮的边框宽度，单位是像素
        )

    def write_halflink(self, text, page_num, bold=False):
        """写入带有尾部链接的普通文本"""
        # 写入文本内容
        text = freeze_tab(text)
        tail_text = " [跳转到]"
        size = self.content_size
        if bold:
            self.c.setFont('bold', size)
        else:
            self.c.setFont('normal', size)
        self.c.drawString(self.pos[0], self.pos[1] - size, text)
        # self.pos[1] = self.pos[1] - size - self.line_margin

        # 写入尾部链接文字
        self.c.setFillColor(Color(0, 0, 1))
        x = self.pos[0] + get_textwidth(text, size)
        self.c.drawString(x, self.pos[1] - size, tail_text)
        self.c.setFillColor(Color(0, 0, 0))
        self.pos[1] = self.pos[1] - size - self.line_margin

        # 写入尾部链接按钮
        width  = x + get_textwidth(tail_text, size)
        height = self.pos[1] + size
        rect = (x, self.pos[1], width, height)
        self.link_num += 1
        self.c.linkAbsolute(
            f"link_{self.link_num}",    # 该按钮名为 f"link_{self.link_num}"，其作用不明
            f"p{page_num}",             # 跳转到 f"p{page_num}" 目标点所在的页面
            rect,                       # 跳转按钮在激活页面上占据的矩形区域
            thickness=0,                # 跳转按钮的边框宽度，单位是像素
        )

    def write_catalog(self, pdf, offset=0):
        # 写目录
        self.write_h1("目录", center=True)
        self.write_content(" ")

        for item in pdf.heading_table:
            if item[1] == "h1":

                spare_width = self.page_width - 2 * self.page_margin - get_textwidth(item[0] + "999" + " [跳转到]", self.content_size)
                char_num    = int(spare_width * 2 // self.content_size) - 2
                char_num    = char_num if char_num >= 0 else 0
                
                text = item[0] + " " + "." * char_num + " " + str(item[2] + offset)

                self.write_halflink(text, item[2] + offset, bold=True)
                
            if item[1] == "h2":
                indent = 3 * " "
                spare_width = self.page_width - 2 * self.page_margin - get_textwidth(indent + item[0] + "999" + " [跳转到]", self.content_size)
                char_num    = int(spare_width * 2 // self.content_size) - 2
                char_num    = char_num if char_num >= 0 else 0
                
                text = "   " + item[0] + " " + "." * char_num + " " + str(item[2] + offset)

                self.write_halflink(text, item[2] + offset)
                
            if item[1] == "h3":
                indent = 6 * " "
                spare_width = self.page_width - 2 * self.page_margin - get_textwidth(indent + item[0] + "999" + " [跳转到]", self.content_size)
                char_num    = int(spare_width * 2 // self.content_size) - 2
                char_num    = char_num if char_num >= 0 else 0
                
                text = "      " + item[0] + " " + "." * char_num + " " + str(item[2] + offset)

                self.write_halflink(text, item[2] + offset)

    def write_homelink(self, page_num):
        """写入每页右上角的【返回目录】按钮"""
        # 写入链接文本
        text = "返回目录"
        size = self.content_size
        self.c.setFont('normal', size)
        self.c.setFillColor(Color(0, 0, 1))
        x = self.page_width - get_textwidth(text, size) - 5
        y = self.page_height - size - 5
        self.c.drawString(x, y, text)
        self.c.setFillColor(Color(0, 0, 0))

        # 写入链接按钮
        width  = x + get_textwidth(text, size)
        height = y + size
        rect = (x, y, width, height)
        self.link_num += 1
        self.c.linkAbsolute(
            f"link_{self.link_num}",    # 该按钮名为 f"link_{self.link_num}"，其作用不明
            f"p{page_num}",             # 跳转到 f"p{page_num}" 目标点所在的页面
            rect,                       # 跳转按钮在激活页面上占据的矩形区域
            thickness=0,                # 跳转按钮的边框宽度，单位是像素
        )

        
        

        
# ===========================================================

if __name__ == "__main__":
    pdf = PDF("顽皮.pdf", "sarasa.ttf", "sarasa-bold.ttf")

    pdf.write_doctitle()
    
    pdf.write_content("测试文本1234ABCD")
    pdf.write_content("测试文本第二行1。测试文本第二行2。测试文本第二行3。测试文本第二行4。测试文本第二行5。测试文本第二行6。测试文本第二行7。测试文本第二行8。")
    pdf.write_content("测试文本\t第三行。")
    pdf.write_content("测试文本        第四行。")
    pdf.write_content("测试文本\t--->\t第五行。")
    pdf.write_h3("三级标题")
    pdf.write_h2("二级标题")
    pdf.write_h1("一级标题")
    pdf.write_h1("居中一级标题", True)
    pdf.write_link("返回标题", 1)
    pdf.write_content("普通文本。")

    for i in range(1, 51):
        pdf.write_content(f"重复的第{i}行")

    pdf.save()





















