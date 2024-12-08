class EcuScreenDataRef:
    name = ""
    type = ""

    def __init__(self, dr, n="", t=""):
        if len(n):
            self.name = n
            self.type = t
            return
        self.name = dr.getAttribute("name")
        self.type = dr.getAttribute("type")


class EcuOwnScreen:
    datarefs = []
    functions = []
    name = ""

    def __init__(self, n):
        self.name = n


class EcuScreenSubFunction:
    datarefs = []
    name = ""
    text = ""

    def __init__(self, sfu, tran):
        self.name = sfu.getAttribute("name")
        codetext = sfu.getAttribute("codetext")
        defaultText = sfu.getAttribute("defaultText")
        self.text = ""
        if codetext:
            if codetext in list(tran.keys()):
                self.text = tran[codetext]
            elif defaultText:
                self.text = defaultText
        DataRefs = sfu.getElementsByTagName("DataRef")
        if DataRefs:
            self.datarefs = []
            for dr in DataRefs:
                dataref = EcuScreenDataRef(dr)
                self.datarefs.append(dataref)


class EcuScreenFunction:
    subfunctions = []
    datarefs = []
    name = ""
    text = ""

    def __init__(self, fu, tran):
        self.name = fu.getAttribute("name")
        codetext = fu.getAttribute("codetext")
        defaultText = fu.getAttribute("defaultText")
        self.text = ""
        if codetext:
            if codetext in list(tran.keys()):
                self.text = tran[codetext]
            elif defaultText:
                self.text = defaultText
        SubFunctions = fu.getElementsByTagName("SubFunction")
        if SubFunctions:
            self.subfunctions = []
            for sfu in SubFunctions:
                subfunction = EcuScreenSubFunction(sfu, tran)
                self.subfunctions.append(subfunction)
            return
        DataRefs = fu.getElementsByTagName("DataRef")
        if DataRefs:
            self.datarefs = []
            for dr in DataRefs:
                dataref = EcuScreenDataRef(dr)
                self.datarefs.append(dataref)


class EcuScreen:
    functions = []
    datarefs = []
    name = ""
    text = ""

    def __init__(self, sc, tran=None):
        if tran is None:
            self.name = sc
            return
        self.name = sc.getAttribute("name")
        codetext = sc.getAttribute("codetext")
        defaultText = sc.getAttribute("defaultText")
        self.text = ""
        if codetext:
            if codetext in list(tran.keys()):
                self.text = tran[codetext]
            elif defaultText:
                self.text = defaultText
        Functions = sc.getElementsByTagName("Function")
        if Functions:
            self.functions = []
            for fu in Functions:
                function = EcuScreenFunction(fu, tran)
                self.functions.append(function)
            return
        DataRefs = sc.getElementsByTagName("DataRef")
        if DataRefs:
            self.datarefs = []
            for dr in DataRefs:
                dataref = EcuScreenDataRef(dr)
                self.datarefs.append(dataref)


class EcuScreens:
    def __init__(self, screen_list, mdoc, tran):
        Screens = mdoc.getElementsByTagName("Screens").item(0)
        if Screens:
            Screen = Screens.getElementsByTagName("Screen")
            if Screen:
                for sc in Screen:
                    screen = EcuScreen(sc, tran)
                    if len(screen.functions) > 0 or len(screen.datarefs) > 0:
                        screen_list.append(screen)
