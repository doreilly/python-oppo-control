from collections import OrderedDict
import re

from serial_protocol.events import Event


RESPONSE_START = b'@'
RESPONSE_END = b'\x0d'
RESPONSE_OK = b'OK'
RESPONSE_ERROR = b'ER'


class ResponseMatcherMeta(type):
    def __new__(cls, name, bases, dct):
        klass = super().__new__(name, bases, dct)

        match_expr = b'^%b%b (%b|%b)(?: (.*?))?%b$' % (
            klass.start_byte, klass.code, klass.ok_code, klass.error_code,
            klass.end_byte)

        klass.matcher = re.compile(match_expr)
        return klass


class OppoEvent(Event):
    
    def __init__(self):
        self.timeout = 10.0


_UPDATES = OrderedDict()


class UpdateMeta(type):

    def __new__(cls, name, bases, dct):
        klass = type.__new__(cls, name, bases, dct)

        if klass.code is not None:
            _UPDATES[klass.code] = klass
            matcher_expr = b'^@%b (.*?)\x0d$'
            klass.matcher = re.compile(matcher_expr)

        return klass


class Update(OppoEvent, metaclass=UpdateMeta):
    code = None


def get_event_for(data, requests):
    request = None

    is_short = data[1:3] in (RESPONSE_OK, RESPONSE_ERROR)
    command = data[1:4]
    
    if is_short:
        if len(requests) > 0:
            request = list(requests)[0]
    else:
        for req in requests:
            if req.code == command:
                request = req
                break
    
    if request is not None:
        instance = request.Response(data)
        if hasattr(instance.request, 'response_parser'):
            request.response_parser(instance)
        else:
            instance.parse(data)

        return instance, request
    else:
        try:
            klass = _UPDATES[command]
        except KeyError:
            return None, None

        instance = klass(data)
        instance.parse(data)
        return instance, None

    return None, None


class _Response:
    
    def __init__(self, data):
        self.data = data

    def parse(self, data):
        m = self.matcher.match(data)
        return m.group('data')


class RespondableMeta(type):

    def __new__(cls, name, bases, dct):
        response_class = dct.get('Response', None)
        
        if response_class is None:
            response_class = dct['Response'] = \
                type('Response', (_Response,), {})

        klass = type.__new__(cls, name, bases, dct)

        if klass.code:
            resp_expr = \
                b'^%b(?:%b )?(?P<status>%b|%b)(?: (?P<data>.*?))?%b$' % (
                    RESPONSE_START, klass.code, RESPONSE_OK, RESPONSE_ERROR,
                    RESPONSE_END)
        
            response_class.matcher = re.compile(resp_expr)

            response_class.request_type = klass

        return klass


class OppoCommand(OppoEvent):

    def get_params(self):
        return None
    
    def to_bytes(self):
        params = self.get_params()
        if params:
            params = b' %b' % params
        else:
            params = b''
        
        return b'#%b%b\x0d\x0a' % (self.code, params)


class Key(OppoCommand, metaclass=RespondableMeta):
    code = None


class _Query(OppoCommand, metaclass=RespondableMeta):
    code = None


class _Advanced(OppoCommand, metaclass=RespondableMeta):
    code = None


class _Set(_Advanced):

    def __init__(self, value):
        super().__init__()
        self.value = value
    
    def get_params(self):
        return str(self.value).encode('ascii')


class Power:

    class Toggle(Key):
        code = b'PWR'

        def response_parser(self, response):
            m = self.matcher.match(response.data)
            self.on = b'ON' == m.group('data')
    
    class Query(_Query):
        code = b'QPW'
    
    class On(Key):
        code = b'PON'
    
    class Off(Key):
        code = b'POF'


class Eject:

    class Toggle(Key):
        code = b'EJT'


class Dimmer:

    class Toggle(Key):
        code = b'DIM'


class Volume:

    class Up(Key):
        code = b'VUP'
    
    class Down(Key):
        code = b'VDN'
    
    class Mute(Key):
        code = b'MUT'
    
    class Query(_Query):
        code = b'QVL'
    
    class Set(_Set):
        code = b'SVL'


class Keypad:

    class N1(Key):
        code = b'NU1'

    class N2(Key):
        code = b'NU2'

    class N3(Key):
        code = b'NU3'

    class N4(Key):
        code = b'NU4'

    class N5(Key):
        code = b'NU5'

    class N6(Key):
        code = b'NU6'

    class N7(Key):
        code = b'NU7'

    class N8(Key):
        code = b'NU8'

    class N9(Key):
        code = b'NU9'

    class N0(Key):
        code = b'NU0'

    class Clear(Key):
        code = b'CLR'


class Info:

    class OSD(Key):
        code = b'OSD'
    
    class Info(Key):
        code = b'INH'


class Navigation:
    class Home(Key):
        code = b'HOM'

    class Goto(Key):
        code = b'GOT'
    
    class PageUp(Key):
        code = b'PUP'
    
    class PageDown(Key):
        code = b'PDN'
    
    class TopMenu(Key):
        code = b'TTL'
    
    class PopUpMenu(Key):
        code = b'MNU'

    class Up(Key):
        code = b'NUP'
    
    class Down(Key):
        code = b'NDN'
    
    class Left(Key):
        code = b'NLT'
    
    class Right(Key):
        code = b'NRT'
    
    class Select(Key):
        code = b'SEL'
    
    class Return(Key):
        code = b'RET'

    class Red(Key):
        code = b'RED'
    
    class Green(Key):
        code = b'GRN'
    
    class Blue(Key):
        code = b'BLU'
    
    class Yellow(Key):
        code = b'YLW'


class Transport:

    class Play(Key):
        code = b'PLA'
    
    class Pause(Key):
        code = b'PAU'
    
    class Previous(Key):
        code = b'PRE'
    
    class FastReverse(Key):
        code = b'REV'

        def __init__(self, value=None):
            self.value = value
        
        def get_params(self):
            if self.value is None:
                return None
            
            return str(self.value).encode('ascii')
    
    class FastForward(_Advanced):
        code = b'FWD'

        def __init__(self, value=None):
            self.value = value
        
        def get_params(self):
            if self.value is None:
                return None
            
            return str(self.value).encode('ascii')
    
    class Next(Key):
        code = b'NXT'
    

class VerboseMode:

    class Query(_Query):
        code = b'QVM'
    
    class Set(_Set):
        code = b'SVM'


class PowerUpdate(Update):
    code = b'UPW'


class PlaybackUpdate(Update):
    code = b'UPL'


class VolumeUpdate(Update):
    code = b'UVL'


class DiscTypeUpdate(Update):
    code = b'UDT'


class AudioTypeUpdate(Update):
    code = b'UAT'


class TimeCodeUpdate(Update):
    code = b'UTC'


class ResolutionUpdate(Update):
    code = b'UVO'
