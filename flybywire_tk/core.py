"""Core module"""
import abc
import asyncio as aio
import collections
import copy
import inspect
import tkinter
from tkinter import N,NE,E,SE,S,SW,W,NW

import dictdiffer

from dictdiffer import diff, patch
from dictdiffer.utils import dot_lookup

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
        if root_node['text'] is not None:
            comp_node = comp_name(text=root_node['text'], **comp_props)
        else:
            comp_node = comp_name(**comp_props)
        try:
            comp_node.on_mount()
        except:
            pass
    elif comp_name in ui.available_widgets:
        comp_node = root_node
    else:
        raise ValueError('Widget not found : %s' % comp_name)

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
        self._comp_tree = None
        self._old_tree = None

    def invalidate(self):
        self._dirty = True

    def mount(self, component, **props):
        """Mounts the given component in the application."""

        self._root_comp = component
        self._root_comp.add_observer(self.invalidate)
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
        self._frame = tkinter.Frame(self.canvas)
        self._frame.columnconfigure(0, weight=1)
        self._frame.columnconfigure(1, weight=1)

        self.render()

        # After component creation
        # puts tkinter widget onto canvas
        self.canvas.create_window(0, 0, anchor=NW, window=self._frame, width = int(self.canvas.config()['width'][4])-int(self.vscrollbar.config()['width'][4]))

        # deal with canvas being resized
        def resize_canvas(event):
            self.canvas.create_window(0, 0, anchor=NW, window=self._frame, width = int(event.width)-int(self.vscrollbar.config()['width'][4]))

        self.canvas.bind("<Configure>", resize_canvas)

        # updates geometry management
        self._frame.update_idletasks()
        # set canvas scroll region to all of the canvas
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

        # set minimum window width
        self._root.update()
        self._root.minsize(self._root.winfo_width(), 0)
        self._root.config(**self.kw)

        self.is_running = True
        self._frame.update()

    def render_component(self, node):
        node_cls = ui.available_widgets[node['_name']]

        # Create component
        comp_obj, update_fn = node_cls(self._frame, node['text'], node['_props'])
        comp_obj.pack(side='top')
        node['_comp_obj'] = comp_obj
        node['_comp_update'] = update_fn

        # TODO: Also make child nodes

        # Store component and update fn

    def render(self):
        # TODO: Fix it so only changed components are updated
        # for widget in self._frame.winfo_children():
        #     widget.destroy()

        # Recursively build component tree dict
        root_tree = parse_component_tree(self._root_comp())

        if self._old_tree is not None:
            delta = diff(self._old_tree, root_tree, ignore=('_comp_obj','_comp_update'))

            for diff_type, index, data in delta:
                if isinstance(index, str) or len(index) == 1:
                    # Top-level change
                    old_node = self._old_tree
                else:
                    # Sub-node change
                    old_node = dot_lookup(self._old_tree, index[:-1])

                # Update node props
                update_fn = old_node['_comp_update']
                if diff_type == 'change':
                    new_node = patch([(diff_type, index, data)], dict(_name=old_node['_name'],text=old_node['text'], _props=old_node['_props']))
                    if update_fn is not None:
                        update_fn(text=old_node['text'], **old_node['_props'])

                # Copy component info
                new_node['_comp_obj'] = old_node['_comp_obj']
                new_node['_comp_update'] = old_node['_comp_update']

                if isinstance(index, str) or len(index) == 1:
                    root_tree = new_node
                else:
                    patch(root_tree, [('change', index[:-1], (old_node, new_node))])
        else:
            render_list = [(root_tree, None)]
            self.render_component(root_tree)
        # TODO: Diff tree against existing tree

        # Instantiate or modify components as needed (pack(), update() or destroy())


        self._dirty = False
        self._old_tree = root_tree

    @aio.coroutine
    def main_loop(self, loop=aio.get_event_loop()):
        """Run the tkinter event loop asynchronously."""
        self._root_comp.on_mount()
        while self.is_running:
            # start mainloop
            if self._dirty:
                self.render()

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
    def __init__(self):
        self.observers = []

    @abc.abstractmethod
    def __call__(self, props):
        """Component must implement this method."""
        raise NotImplementedError()

    def __str__(self):
        return self.__class__.__name__.upper()

    def on_mount(self):
        pass

    def on_unmount(self):
        pass

    def add_observer(self, obs):
        self.observers.append(obs)

    def update(self, **new_state):
        for k,v in new_state.items():
            setattr(self, k, v)

        for obs in self.observers:
            obs()

class TimerApp(Component):
    def __init__(self):
        """Initialize the application."""
        super().__init__()

        self.secondsElapsed = 0
        self.task = None

    def __call__(self):
        """Renders view given application state."""
        count = self.secondsElapsed
        return T(TimerView, count=self.secondsElapsed)

    def tick(self):
        """Increments counter."""
        self.update(secondsElapsed = self.secondsElapsed + 1)

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

class CounterApp(Component):
    def __init__(self):
        """Initialize the application."""
        super().__init__()

        self.count = 0

    def __call__(self):
        """Renders view given application state."""
        return T('Frame', [
                    T('Label', str(self.count)),
                    T('Button','+'),
                    T('Button','-')
        ])

def TimerView(count=0):
    return T('Label', 'Seconds Elapsed: '+str(count))

if __name__ == '__main__':
    # Tests for component parsing
    comps = T('Frame', [T(TimerView, count=1337), T(TimerView, count=6969)], align='center')
    out = parse_component_tree(comps)
    # print(out)
    # assert out == {'_name': 'Frame',
    #          '_props': {'align': 'center'},
    #          'text': [{'_name': 'Label',
    #                    '_props': {},
    #                    'text': 'Seconds Elapsed: 1337'},
    #                   {'_name': 'Label',
    #                    '_props': {},
    #                    'text': 'Seconds Elapsed: 6969'}]}
    #
    # comps = T(TimerView, count=1337)
    # assert parse_component_tree(comps) == {'_name': 'Label', 'text': 'Seconds Elapsed: 1337', '_props': {}}

    fbw = FBWApplication()
    fbw.mount(TimerApp())
    fbw.start()
