# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import hashlib
import socket
import sys

from pypjlink import protocol

class ProjectorError(Exception):
    pass

reverse_dict = lambda d: dict(zip(d.values(), d.keys()))

POWER_STATES = {
    'off': '0',
    'on': '1',
    'cooling': '2',
    'warm-up': '3',
}
POWER_STATES_REV = reverse_dict(POWER_STATES)

SOURCE_TYPES = {
    'RGB/VGA':  '1',
    'VIDEO':    '2',
    'DIGITAL':  '3',
    'STORAGE':  '4',
    'NETWORK':  '5',

# Benq
#11 = VGA1
#12 = VGA2
#21 = SVideo
#22 = CVBS
#31 = HDMI
#51 = CARD_READER
#52 = LAN DISPLAY
#53 = USB DISPLAY

}
SOURCE_TYPES_REV = reverse_dict(SOURCE_TYPES)

MUTE_VIDEO = 1
MUTE_AUDIO = 2
MUTE_STATES_REV = {
    '10': (False, False),  # video mute off
    '11': (True, False),   # video mute on
    '20': (False, False),  # audio mute off
    '21': (False, True),   # audio mute on
    '30': (False, False),  # video and audio mute off
    '31': (True, True),    # video and audio mute on
}

ERROR_STATES_REV = {
    '0': 'ok',
    '1': 'warning',
    '2': 'error',
}

class Projector(object):
    def __init__(self, f, encoding):
        self.f = f
        self.encoding = encoding

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.close()

    def close(self):
        self.f.close()

    @classmethod
    def from_address(cls, address, port=4352, encoding='utf-8', timeout=10):
        """build a Projector from a ip address"""
        sock = socket.socket()
        sock.settimeout(timeout)
        sock.connect((address, port))
        # in python 3 I need to specify newline, otherwise read hangs
        # in "PJLINK 0\r"
        # I expect socket file to return byte strings in python 2 and
        # unicode strings in python 3
        if sys.version_info.major == 2:
            f = sock.makefile()
        else:
            f = sock.makefile(mode='rw', newline='\r', encoding=encoding)
        sock.close()
        return cls(f, encoding)

    def authenticate(self, password=None):
        # I'm just implementing the authentication scheme designed in the
        # protocol. Don't take this as any kind of assurance that it's secure.

        data = protocol.read(self.f, 9, self.encoding)
        assert data[:7].upper() == 'PJLINK '
        security = data[7]
        if security == '0':
            return None
        data += protocol.read(self.f, 9, self.encoding)
        assert security == '1'
        assert data[8] == ' '
        salt = data[9:17]
        assert data[17] == '\r'

        if password is None:
            raise RuntimeError('projector needs a password')

        if callable(password):
            password = password()

        pass_data = (salt + password).encode('utf-8')
        pass_data_md5 = hashlib.md5(pass_data).hexdigest()

        # we *must* send a command to complete the procedure,
        # so we just get the power state.

        cmd_data = protocol.to_binary('POWR', '?')
        self.f.write(pass_data_md5 + cmd_data)
        self.f.flush()

        # read the response, see if it's a failed auth
        data = protocol.read(self.f, 7, self.encoding)
        if data.upper() == 'PJLINK ':
            # should be a failed auth if we get that
            data += protocol.read(self.f, 5, self.encoding)
            assert data == 'PJLINK ERRA\r'
            # it definitely is
            return False

        # good auth, so we should get a reply to the command we sent
        body, param = protocol.parse_response(self.f, self.encoding, data)

        # make sure we got a sensible response back
        assert body == 'POWR'
        if param in protocol.ERRORS:
            raise ProjectorError(protocol.ERRORS[param])

        # but we don't care about the value if we did
        return True

    def get(self, body):
        success, response = protocol.send_command(self.f, body, '?', self.encoding)
        if not success:
            raise ProjectorError(response)
        return response

    def set(self, body, param):
        success, response = protocol.send_command(self.f, body, param, self.encoding)
        if not success:
            raise ProjectorError(response)
        assert response == 'OK'

    # Power

    def get_power(self):
        param = self.get('POWR')
        return POWER_STATES_REV[param]

    def set_power(self, status, force=False):
        if not force:
            assert status in ('off', 'on')
        self.set('POWR', POWER_STATES[status])

    # Input

    def get_input(self):
        param = self.get('INPT')
        source, number = param
        source = SOURCE_TYPES_REV[source]
        number = int(number)
        return (source, number)

    def set_input(self, source, number):
        source = SOURCE_TYPES[source]
        number = str(number)
        assert number in '123456789'
        self.set('INPT', source + number)

    # A/V mute

    def get_mute(self):
        param = self.get('AVMT')
        return MUTE_STATES_REV[param]

    def set_mute(self, what, state):
        assert what in (MUTE_VIDEO, MUTE_AUDIO, MUTE_VIDEO | MUTE_AUDIO)
        what = str(what)
        assert what in '123'
        state = '1' if state else '0'
        self.set('AVMT', what + state)

    # Errors

    def get_errors(self):
        param = self.get('ERST')
        errors = 'fan lamp temperature cover filter other'.split()
        assert len(param) == len(errors)
        return dict((key, ERROR_STATES_REV[value]) for key, value in zip(errors, param))

    # Lamps

    def get_lamps(self):
        param = self.get('LAMP')
        assert len(param) <= 65
        values = param.split(' ')
        assert len(values) <= 16 and len(values) % 2 == 0

        lamps = []
        for time, state in zip(values[::2], values[1::2]):
            time = int(time)
            state = bool(int(state))
            lamps.append((time, state))

        assert len(lamps) <= 8
        return lamps

    # Input list

    def get_inputs(self):
        param = self.get('INST')
        assert len(param) <= 95

        values = param.split(' ')
        assert len(values) <= 50

        inputs = []
        for value in values:
            source, number = value
            source = SOURCE_TYPES_REV[source]
            assert number in '123456789'
            number = int(number)
            inputs.append((source, number))

        return inputs

    # Projector info

    def get_name(self):
        param = self.get('NAME')
        assert len(param) <= 64
        return param

    def get_manufacturer(self):
        param = self.get('INF1')
        assert len(param) <= 32
        # stupidly, this is not defined as utf-8 in the spec. :(
        return param

    def get_product_name(self):
        param = self.get('INF2')
        assert len(param) <= 32
        # stupidly, this is not defined as utf-8 in the spec. :(
        return param

    def get_other_info(self):
        param = self.get('INFO')
        assert len(param) <= 32
        return param

    # TODO: def get_class(self): self.get('CLSS')
    # once we know that class 2 is, and how to deal with it

    # class 1 spec: https://pjlink.jbmia.or.jp/english/data/5-1_PJLink_eng_20131210.pdf
    # class 2 spec: https://pjlink.jbmia.or.jp/english/data_cl2/PJLink_5-1.pdf
    #def get_serial_number(self):
    #    param = self.get('SNUM')
    #def get_software_version(self):
    #    param = self.get('SVER')
    #def get_lamp_spare_pn(self):
    #    param = self.get('RLMP')
    #def get_filter_spare_pn(self):
    #    param = self.get('RFIL')

