
import wx

from gui.frame_downloader import *
from gui.frame_parser import FrameParser
from gui.about import DialogAbout
from gui.frame_merger import FrameMerger
from gui.dialog_gettool import DialogGetTool
from gui.dialog_settings import DialogSettings
from gui.dialog_copylink import DialogCopyLink
from gui.dialog_dllog import DialogDLLog

app = None
frame_downloader = None
frame_parse = None
timer = None
frame_merger = None
dialog_copylink = None
dialog_dllog = None

def init():
    global app, frame_downloader, frame_parse, frame_merger, dialog_copylink, dialog_dllog
    app = wx.App()
    frame_downloader = FrameMain(None)
    frame_parse = FrameParser(None)
    frame_merger = FrameMerger(None)
    dialog_copylink = DialogCopyLink(frame_parse)
    dialog_dllog = DialogDLLog(None)

def MainLoop():
    global app
    app.MainLoop()

def setTimerHandler(handler):
    if frame_downloader.timer.IsRunning():
        frame_downloader.timer.Stop()
    frame_downloader.Bind(wx.EVT_TIMER, handler, frame_downloader.timer)

def runTimer(ms, oneShot=False):
    frame_downloader.timer.Start(ms, oneShot=oneShot)

def stopTimer():
    frame_downloader.timer.Stop()