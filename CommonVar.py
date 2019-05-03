
# status

SHUTDOWN = False
ALLTASKDONE = False

# parse

SEL_RES = None


# copy link
CPYLINK_SEL_ITEMS = {}
LISTCTRL_ITEMS = []


# download
MAX_CONN = 5
MAX_TASK = 3
BUFFER_SIZE = 20
FILEPATH = ''

BLOCK_SIZE = 512

UNDONE_JOB = ''


# merge

FFMPEG_PATH = ''


MER_VIDEO_AUDIO = object()

MER_CONCAT_SIMPLE = object()

MER_CONCAT_DEMUXER = object()
MER_CONCAT_PROTOCAL = object()


MER_CONVERT_MP4 = object()
MER_CONVERT_FLV = object()
MER_CONVERT_MKV = object()

TARGET_FORMAT = '.mp4'


import wx

# wxID
ID_PARSER_GODOWNLOAD = wx.NewId()

