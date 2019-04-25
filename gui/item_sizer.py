
import wx


def format_byte(bytes, format='%.2f%s'):
    if bytes > 1024 * 1024 * 1024:
        return format % (bytes / 1024.0 / 1024 / 1024, 'GB')
    elif bytes > 1024 * 1024:
        return format % (bytes / 1024.0 / 1024, 'MB')
    elif bytes > 1024:
        return format % (bytes / 1024.0, 'KB')
    else:
        return format % (bytes, 'B')



class ItemBoxSizer(wx.BoxSizer):
    def __init__(self, parent, current_byte, total_byte, **kwargs):
        wx.BoxSizer.__init__(self, wx.HORIZONTAL)
        self.SetMinSize(wx.Size(-1, 10))
        self.parent = parent

        self.text_name = None
        self.text_percent = None
        self.text_speed = None
        self.text_progress = None

        self.total = total_byte

        self.gauge_progress = None

        self.initWidget(current=current_byte, **kwargs)



    def initWidget(self, **kwargs):

        name = kwargs.get('name', '')
        current = kwargs.get('current', 0)
        percent = current*100.0 / self.total if self.total > 0 else 0
        speed = format_byte(kwargs.get('speed', 0), '%.1f%s/S')

        self.text_name = wx.StaticText(self.parent, wx.ID_ANY, name, wx.DefaultPosition, wx.Size(20, -1),
                                       wx.ALIGN_RIGHT)
        self.text_percent = wx.StaticText(self.parent, wx.ID_ANY, str(round(percent, 1)) + '%', wx.DefaultPosition,
                                          wx.Size(40, -1), wx.ALIGN_RIGHT)
        self.text_speed = wx.StaticText(self.parent, wx.ID_ANY, speed, wx.DefaultPosition, wx.Size(65, -1),
                                        wx.ALIGN_RIGHT)

        self.text_name.Wrap(-1)
        self.text_percent.Wrap(-1)
        self.text_speed.Wrap(-1)

        self.gauge_progress = wx.Gauge(self.parent, wx.ID_ANY, 10000, wx.DefaultPosition, wx.DefaultSize,
                                       wx.GA_HORIZONTAL)
        self.gauge_progress.SetValue(int(percent*100))

        self.Add(self.text_name, 0, wx.ALIGN_RIGHT | wx.ALL, 5)
        self.Add(self.gauge_progress, 5, wx.ALL, 5)
        self.Add(self.text_percent, 0, wx.ALL, 5)
        self.Add(self.text_speed, 0, wx.ALL, 5)
        # self.Add(self.text_progress, 0, wx.ALL, 5)
        staticline1 = wx.StaticLine(self.parent, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL)

        self.Add(staticline1, 0, wx.EXPAND | wx.ALL, 2)

    def update(self, current_byte, speed_byte, totol_byte):
        self.total = totol_byte if totol_byte > 0 else 0
        percent = current_byte * 100.0 / self.total if self.total > 0 else 0
        speed = format_byte(speed_byte if speed_byte > 0 else 0, '%.1f%s/s')

        text_percent = str(round(percent, 1)) + '%'
        if text_percent != self.text_percent.GetLabelText():
            self.text_percent.SetLabelText(text_percent)

        if speed != self.text_speed.GetLabelText():
            self.text_speed.SetLabelText(speed)

        self.gauge_progress.SetValue(int(percent*100))

