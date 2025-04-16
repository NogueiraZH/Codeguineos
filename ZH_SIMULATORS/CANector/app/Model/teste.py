from canlib import canlib, Frame

if __name__ == "__main__":
    ch = canlib.openChannel(channel=0, flags=canlib.canOPEN_ACCEPT_VIRTUAL)
    ch.setBusParams(canlib.canBITRATE_250K)
    ch.busOn()

    while True:
        message = ch.read(timeout=-1)
        if message.id == 0x18DA3DFA:
            frame = Frame(id_=0x18DAFA3D, dlc=8,data=[0x10, 0x10, 0x10, 0x10, 0x16, 0xbc, 0x10, 0x10],  flags=canlib.MessageFlag.EXT)
            ch.write(frame)
        elif message.id == 0x18da00fa:
            frame = Frame(id_=0x18DAFA00, dlc=8,data=[0x10, 0x10, 0x10, 0x10, 0x16, 0xbc, 0x10, 0x10],  flags=canlib.MessageFlag.EXT)
            ch.write(frame)