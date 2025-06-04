import win32api
import win32con
import win32gui
import win32ui
from win32com.shell import shell

import rlab_stage_3 as main

class MyWindow:
    def __init__(self):
        # 受控制的资源
        # 显示的文本1
        self.text2 = " "

        # 注册窗口类和创建窗口的代码
        className = 'MyWindowClass'
        wndClass = win32gui.WNDCLASS()
        wndClass.style = win32con.CS_HREDRAW | win32con.CS_VREDRAW
        wndClass.lpfnWndProc = self.WindowProcedure
        wndClass.hInstance = win32api.GetModuleHandle(None)
        wndClass.hCursor = win32gui.LoadCursor(None, win32con.IDC_ARROW)
        wndClass.hbrBackground = win32con.COLOR_WINDOW
        wndClass.lpszClassName = className
         
        # 加载自定义图标（替换为你的图标文件路径）
        iconFilePath = "ok.ico"  # 你的图标文件路径
        iconHandle = win32gui.LoadImage(
            win32api.GetModuleHandle(None),   # 模块句柄
            iconFilePath,                     # 图标文件路径
            win32con.IMAGE_ICON,              # 图像类型
            0, 0,                             # 图标宽度和高度，0 表示原始大小
            win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE  # 加载选项
        )
         
        # 将图标句柄赋值给窗口类结构的 hIcon 成员
        wndClass.hIcon = iconHandle
         
        # 注册窗口类
        atom = win32gui.RegisterClass(wndClass)
         
        # 创建窗口
        windowTitle = 'PDF生成器'
        hWnd = win32gui.CreateWindow(
            className,
            windowTitle,
            win32con.WS_OVERLAPPEDWINDOW,
            win32con.CW_USEDEFAULT, win32con.CW_USEDEFAULT,
            400, 300,
            0,
            0,
            wndClass.hInstance,
            None
        )
         
        # 显示窗口
        win32gui.ShowWindow(hWnd, win32con.SW_SHOW)
         
        # 强制更新一次窗口
        win32gui.UpdateWindow(hWnd)
         
        # 允许窗口接受拖放的文件
        win32gui.DragAcceptFiles(hWnd, True)

        self.file_num = 0
        
    # 定义窗口的回调函数，处理绘画和拖放文件消息
    def WindowProcedure(self, hwnd, msg, wParam, lParam):
        result = 0  # 默认的 LRESULT 值
        if msg == win32con.WM_PAINT:
            hdc, paintStruct = win32gui.BeginPaint(hwnd)

            # 设置背景模式为透明
            win32gui.SetBkMode(hdc, win32con.TRANSPARENT)
     
            # 创建 LOGFONT 结构体
            logFont = win32gui.LOGFONT()
            logFont.lfFaceName = 'Arial'  # 字体名称
            logFont.lfHeight = 20         # 字体高度
            logFont.lfWeight = win32con.FW_BOLD  # 字体粗细
            logFont.lfItalic = False      # 是否斜体
            logFont.lfUnderline = False   # 是否下划线
         
            # 从 LOGFONT 结构体创建字体句柄
            fontHandle = win32gui.CreateFontIndirect(logFont)
         
            # 选择字体到设备上下文
            hfont = win32gui.SelectObject(hdc, fontHandle)
     
            # 绘制文本
            text = "将文件拖到此窗口内"
            rect = (20, 20, 380, 60)
            win32gui.DrawText(hdc, text, len(text), rect, win32con.DT_LEFT)

            # 绘制文本
            logFont.lfWeight = win32con.FW_NORMAL  # 字体改成细的
            fontHandle = win32gui.CreateFontIndirect(logFont)   # 重来一遍
            hfont = win32gui.SelectObject(hdc, fontHandle)      # 重来一遍
            
            rect2 = (20, 180, 370, 280)
            win32gui.DrawText(hdc, self.text2, len(self.text2), rect2, win32con.DT_LEFT | win32con.DT_WORDBREAK)
     
            # 恢复原来的字体
            win32gui.SelectObject(hdc, hfont)
     
            # 删除字体对象
            win32gui.DeleteObject(fontHandle)
     
            win32gui.EndPaint(hwnd, paintStruct)
        elif msg == win32con.WM_DROPFILES:
            count = shell.DragQueryFile(wParam, -1)
            for i in range(count):
                path = shell.DragQueryFile(wParam, i)
                # print(f"Dropped file: {path}")

                # 调用外部功能
                new_path = main.main(path, self.file_num)
                self.text2 = new_path + " 生成完毕！  "
                self.file_num += 2

                # 重绘窗口以显示新文本
                win32gui.InvalidateRect(hwnd, None, True)
                
            win32api.DragFinish(wParam)
            result = 0  # 返回 0 表示消息已处理
        elif msg == win32con.WM_DESTROY:
            win32gui.PostQuitMessage(0)
        else:
            result = win32gui.DefWindowProc(hwnd, msg, wParam, lParam)
        return result  # 确保返回正确的 LRESULT


if __name__ == "__main__":
    win = MyWindow()
    win32gui.PumpMessages()

    # # 当窗口关闭时，清理资源
    # win32gui.DestroyWindow(win.hWnd)
    # win32gui.UnregisterClass('MyWindowClassName', win.hinst)










