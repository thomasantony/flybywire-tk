import asyncio
import tkinter
from functools import wraps

def set_interval(fn, interval, args=()):
    """
    Calls a function periodically (assuming there is already an asyncio event
    loop running)

    fn: Function to be called
    interval: Period in seconds
    args: Tuple of arguments to be passed in

    Returns an asyncio.Future object

    Ref: http://stackoverflow.com/a/37512537/538379
    """
    @wraps(fn)
    @asyncio.coroutine
    def repeater():
        while True:
            yield from asyncio.sleep(interval)
            fn(*args)

    loop = asyncio.get_event_loop()
    task = asyncio.ensure_future(repeater())
    return task

def clear_interval(task):
    """
    Stops a periodic function call setup using set_inteval()
    """
    def stopper():
        task.cancel()

    loop = asyncio.get_event_loop()
    loop.call_soon(stopper)

class AutoScrollbar(tkinter.Scrollbar):
    # a scrollbar that hides itself if it's not needed.  only
    # works if you use the grid geometry manager.
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            # grid_remove is currently missing from Tkinter!
            self.tk.call("grid", "remove", self)
        else:
            self.grid()
        tkinter.Scrollbar.set(self, lo, hi)
    def pack(self, **kw):
        raise TclError("cannot use pack with this widget")
    def place(self, **kw):
        raise TclError("cannot use place with this widget")
