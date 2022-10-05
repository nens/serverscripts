# Copied from the __init__.py of the pypi clfparser project

from datetime import datetime

import re


class CLFParser:
    "Represents a single Apache common log format record"

    # "%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-agent}i\""

    commonLogFormat = r'(?P<h>([^ ]*)) (?P<l>([^ ]*)) (?P<u>([^ ]*)) (?P<t>\[([^]]*)\]) (?P<r>"([^"]*)") (?P<s>([^ ]*)) (?P<b>([^ ]*))'
    combinedLogFormat = r'(?P<h>([^ ]*)) (?P<l>([^ ]*)) (?P<u>([^ ]*)) (?P<t>\[([^]]*)\]) (?P<r>"([^"]*)") (?P<s>([^ ]*)) (?P<b>([^ ]*)) (?P<Referer>"([^"]*)") (?P<Useragent>"([^"]*)")'

    nullRec = {
        "h": "",
        "l": "",
        "u": "",
        "t": "",
        "r": "",
        "s": "",
        "b": "",
        "Referer": "",
        "Useragent": "",
        "time": "",
        "timezone": "",
    }

    clfDict = {}

    def __init__(self, rec):
        for p in (self.combinedLogFormat, self.commonLogFormat):
            m = re.match(p, rec)
            if m:
                self.clfDict = m.groupdict()
                if p == self.commonLogFormat:
                    self.clfDict.update({"Referer": "", "Useragent": ""})
                self.clfDict.update(
                    {
                        "time": datetime.strptime(
                            self.clfDict["t"][1:21], "%d/%b/%Y:%H:%M:%S"
                        ),
                        "timezone": (self.clfDict["t"])[22:27],
                    }
                )
                break
        else:
            self.clfDict = self.nullRec

    @classmethod
    def logDict(cls, rec):
        return cls(rec).clfDict

    @classmethod
    def logParts(cls, rec, formatString):
        w = cls(rec)
        t = re.findall(r"(%\w+)", formatString)
        output = []
        for p in t:
            if p == "%>s":
                p = "s"
            if p == "%i{User-agent}":
                p = "Useragent"
            if p == "%i{Referer}":
                p = "Referer"
            output.append(w.clfDict[p.replace("%", "")])
        return output
