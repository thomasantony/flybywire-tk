"""Core module"""
import abc
import asyncio as aio
import tkinter
from tkinter import N,NE,E,SE,S,SW,W,NW
from misc import set_interval, clear_interval, AutoScrollbar

def T(name, children=None, **kwargs):
    """Helper function for building components."""
    return dict(component=name, children=children, **kwargs)


class FBWApplication(object):
    """The main Applicaton object."""
    def __init__(self, title="flybywire-tk application", **kw):
        self._root = tkinter.Tk()
        self._root.title(title)
        self.kw = kw
        self._root_comp = None

    def mount(self, component):
        """Mounts the given component in the application."""
        self._root_comp = component
        self._build_app()

    def _build_app(self):
        # create scroll bar
        self.vscrollbar = AutoScrollbar(self._root)
        self.vscrollbar.grid(row=0, column=1, sticky=N+S)

        # create canvas
        self.canvas = tkinter.Canvas(self._root,yscrollcommand=self.vscrollbar.set, bd=5)

        self.canvas.grid(row=0, column=0, sticky=N+S+E+W)

        # configure scroll bar for canvas
        self.vscrollbar.config(command=self.canvas.yview)

        # make the canvas expandable
        self._root.grid_rowconfigure(0, weight=1)
        self._root.grid_columnconfigure(0, weight=1)

        # create frame in canvas
        self.frame = tkinter.Frame(self.canvas)
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=1)

        # After component creation
        # puts tkinter widget onto canvas
        self.canvas.create_window(0, 0, anchor=NW, window=self.frame, width = int(self.canvas.config()['width'][4])-int(self.vscrollbar.config()['width'][4]))

        # deal with canvas being resized
        def resize_canvas(event):
            self.canvas.create_window(0, 0, anchor=NW, window=self.frame, width = int(event.width)-int(self.vscrollbar.config()['width'][4]))
        self.canvas.bind("<Configure>", resize_canvas)

        # updates geometry management
        self.frame.update_idletasks()

        # set canvas scroll region to all of the canvas
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

        # set minimum window width
        self._root.update()
        self._root.minsize(self._root.winfo_width(), 0)
        self._root.config(**self.kw)

        self.is_running = True
        self.frame.update()

    @aio.coroutine
    def main_loop(self, loop=aio.get_event_loop()):
        while self.is_running:
            # start mainloop
            self._root.update_idletasks()
            self._root.update()
            try:
                yield from aio.sleep(.1)
            except aio.CancelledError:
                break

    def start(self):
        loop = aio.get_event_loop()
        def on_closing():
            self.is_running = False
        self._root.protocol("WM_DELETE_WINDOW", on_closing)
        try:
            loop.run_until_complete(self.main_loop())
        except KeyboardInterrupt:
            pass
        finally:
            loop.close()


class Component(object):
    """Class defining a UI component."""
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __call__(self, props):
        """Component must implement this method."""
        raise NotImplementedError()

    def __str__(self):
        return self.__class__.__name__.upper()

    def update(**new_state):
        pass

class TimerApp(Component):
    def __init__(self):
        """Initialize the application."""
        super().__init__()

        self.secondsElapsed = 0
        self.task = None

    def __call__(self, props):
        """Renders view given application state."""
        count = self.secondsElapsed
        return T('Label', 'Seconds Elapsed: '+str(count))

    def tick(self):
        """Increments counter."""
        count = self.secondsElapsed
        self.update(secondsElapsed = count + 1)

    def on_load(self):
        """
        Triggers when the application first loads in the browser
        """
        self.task = set_interval(self.tick, 1)

    def on_close(self):
        """
        Triggers when the application window is closed
        """
        clear_interval(self.task)


fbw = FBWApplication()
fbw.mount(TimerApp())
fbw.start()
