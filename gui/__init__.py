
import wx
# from gui.frame import FrameMain
from gui.frame_main import *
from gui.frame_parse import DialogParser
from gui.about import About_Dialog
app = None
frame_main = None
frame_parse = None
timer = None


def init():
    global app, frame_main, frame_parse
    app = wx.App()
    frame_main = FrameMain(None)
    frame_main.Hide()
    frame_parse = DialogParser(frame_main)



def MainLoop():
    global app
    app.MainLoop()

def setTimerHandler(handler):
    if frame_main.timer.IsRunning():
        frame_main.timer.Stop()
    frame_main.Bind(wx.EVT_TIMER, handler, frame_main.timer)

def runTimer(ms, oneShot=False):
    frame_main.timer.Start(ms, oneShot=oneShot)

def stopTimer():
    frame_main.timer.Stop()