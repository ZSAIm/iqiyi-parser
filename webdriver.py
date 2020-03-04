import wx

from wx.html2 import WebView


class WebDriver(wx.Frame):
    def __init__(self):
        super(WebDriver, self).__init__(None, -1, 'VideoCrawlerEngine', size=(1000, 600))
        webview = WebView.New(self, style=wx.BORDER_NONE)
        self.browser = webview


def create_wx_app():
    app = wx.App()
    frame = WebDriver()
    frame.Show()
    app.frame = frame
    return app
