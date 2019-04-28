
import wx
# from gui.frame import FrameMain
from gui.frame_downloader import *
from gui.frame_parser import FrameParser
from gui.about import DialogAbout
from gui.frame_merger import FrameMerger
from gui.tool_request import DialogToolReq
from gui.settings import DialogSettings

app = None
frame_downloader = None
frame_parse = None
timer = None
frame_merger = None

def init():
    global app, frame_downloader, frame_parse, frame_merger
    app = wx.App()
    frame_downloader = FrameMain(None)
    frame_parse = FrameParser(None)
    frame_merger = FrameMerger(None)

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