"""Wrappers for tkinter widgets."""
import sys
import inspect
import tkinter

def Label(self, root, component_def):
    """A wrapper for tkinter.Label."""
    _, content, props = component_def

    text_var = tkinter.StringVar()
    def update(**props):
        """Function used to update the label if changed."""
        text_var.set(props['text'] if 'text' in props else content)

    update(**props)
    if 'text' in props:
        del props['text']

    return (tkinter.Label(root, textvariable=text_var, **props), update)

def Frame():
    """Test widget."""
    pass

available_widgets = {name: fn for name, fn in inspect.getmembers(sys.modules[__name__])
                     if callable(fn)}
