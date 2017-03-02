"""Core module"""
import abc
import asyncio as aio
import tkinter
import inspect
import collections
import copy
from tkinter import N,NE,E,SE,S,SW,W,NW
from misc import set_interval, clear_interval, AutoScrollbar
import ui

def T(name, content=None, **props):
    """Helper function for building components."""
    return dict(_name=name, text=content, _props=props)


def parse_component_tree(root_node):
    """
    Travereses and builds the component tree

    Parameters
    ----------
    root_comp : dict
        Root component description generated using the T() function
    """
    output = {}
    comp_name = root_node['_name']
    comp_props = root_node['_props']

    if callable(comp_name):
        comp_node = comp_name(text=root_node['text'], **comp_props)
    elif comp_name not in ui.available_widgets:
        raise ValueError('Widget not found : %s' % comp_name)
    else:
        comp_node = root_node

    subnodes = comp_node['text']
    if not isinstance(subnodes, str) and isinstance(subnodes, collections.Iterable):
        output['text'] = [parse_component_tree(n) for n in subnodes]

    return dict(collections.ChainMap(output, comp_node))


class FBWApplication(object):
    """The main Applicaton object."""
    def __init__(self, title="flybywire-tk application", **kw):
        self._root = tkinter.Tk()
        self._root.title(title)
        self.kw = kw
        self._root_comp = None

    def mount(self, component, **props):
        """Mounts the given component in the application."""
        self._root_comp = component
        self._build_app()

    def _build_app(self):
        """Build the tkinter window with default settings."""
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

        self.draw_component()

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

    def draw_component(self):
        comp_tree = self._root_comp()
        # Recursively build component tree dict
        # Diff tree against existing tree
        # Instantiate or modify components as needed (pack(), update() or destroy())


    @aio.coroutine
    def main_loop(self, loop=aio.get_event_loop()):
        """Run the tkinter event loop asynchronously."""
        while self.is_running:
            # start mainloop
            self._root.update_idletasks()
            self._root.update()
            try:
                yield from aio.sleep(.1)
            except aio.CancelledError:
                break

    def start(self):
        """Start the application."""
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

    def __call__(self):
        """Renders view given application state."""
        count = self.secondsElapsed
        return T(TimerView, self.secondsElapsed)

    def tick(self):
        """Increments counter."""
        count = self.secondsElapsed
        self.update(secondsElapsed = count + 1)

    def on_mount(self):
        """
        Triggers when the component is mounted
        """
        self.task = set_interval(self.tick, 1)

    def on_unmount(self):
        """
        Triggers when the component is removed
        """
        clear_interval(self.task)

def TimerView(text=0):
    return T('Label', 'Seconds Elapsed: '+str(text), color='red')

# fbw = FBWApplication()
# fbw.mount(TimerApp())
# fbw.start()

if __name__ == '__main__':
    # Tests for component parsing
    comps = T('Frame', [T(TimerView, 1337), T(TimerView, 6969)], align='center')
    out = parse_component_tree(comps)
    assert out == {'_name': 'Frame',
             '_props': {'align': 'center'},
             'text': [{'_name': 'Label',
                       '_props': {'color': 'red'},
                       'text': 'Seconds Elapsed: 1337'},
                      {'_name': 'Label',
                       '_props': {'color': 'red'},
                       'text': 'Seconds Elapsed: 6969'}]}

    comps = T(TimerView, 1337)
    assert parse_component_tree(comps) == {'_name': 'Label', 'text': 'Seconds Elapsed: 1337', '_props': {'color': 'red'}}
