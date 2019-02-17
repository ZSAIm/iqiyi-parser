

class Packer:
    def pack(self):

        def dig_pack(obj):
            if isinstance(obj, list) or isinstance(obj, tuple):
                tmplist = []
                for m in obj:
                    if 'pack' in dir(m):
                        tmplist.append(m.pack())
                    else:
                        tmplist.append(dig_pack(m))

                if isinstance(obj, tuple):
                    tmplist = tuple(tmplist)
                return tmplist

            elif isinstance(obj, dict):
                tmpdict = {}
                obj_tmp = obj.copy()
                for m, n in obj_tmp.items():
                    if 'pack' in dir(n):
                        tmpdict[m] = n.pack()
                    else:
                        tmpdict[m] = dig_pack(n)

                return tmpdict
            else:
                return obj.pack() if 'pack' in dir(obj) else obj

        retdict = {}

        packet_params = self.__packet_params__()

        retdict['[order]'] = packet_params

        for i in packet_params:
            tmp = getattr(self, i, None)
            retdict[i] = dig_pack(tmp)
        return retdict

    def unpack(self, packet):
        unpack_order = packet.get('[order]', None)
        if '[order]' in packet:
            del packet['[order]']

        if unpack_order:
            for i in unpack_order:
                if hasattr(self, i):
                    if 'unpack' in dir(getattr(self, i)):
                        getattr(self, i).unpack(packet[i])
                    else:
                        setattr(self, i, packet[i])
        else:
            for i, j in packet.items():
                if hasattr(self, i):
                    if 'unpack' in dir(getattr(self, i)):
                        getattr(self, i).unpack(j)
                    else:
                        setattr(self, i, j)

    def __packet_params__(self):
        return []




class ProgressSaver(object):
    def __init__(self):
        pass



