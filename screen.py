from PySide.QtCore import Signal

from screenpresenter import ScreenPresenter
from uiview import UiView

class Screen(UiView):
    keyreleased = Signal(int)

    def __init__(self, uistack):
        UiView.__init__(self, 'screen.ui', ScreenPresenter, uistack, self)

    def keyReleaseEvent(self, e):
        self.keyreleased.emit(e.key())
