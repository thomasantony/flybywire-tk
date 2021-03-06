"""Wrappers for tkinter widgets."""
import sys
import inspect
import tkinter

def Label(root, content, props):
    """A wrapper for tkinter.Label."""

    text_var = tkinter.StringVar()
    def update(**props):
        """Function used to update the label if changed."""
        text_var.set(props.get('text', content))

    update(**props)
    if 'text' in props:
        del props['text']

    return (tkinter.Label(root, textvariable=text_var, **props), update)

def Button(root, content, props):
    """A wrapper for tkinter.Button."""

    text_var = tkinter.StringVar()
    def update(**props):
        """Function used to update the label if changed."""
        text_var.set(props.get('text', content))

    update(**props)
    if 'text' in props:
        del props['text']

    return (tkinter.Button(root, textvariable=text_var, **props), update)

def Frame(root, content, props):
    """Frame container."""
    return tkinter.Frame(root, **props), None

available_widgets = {name: fn for name, fn in inspect.getmembers(sys.modules[__name__])
                     if callable(fn)}
