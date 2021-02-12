from __future__ import annotations

from typing import List, Callable


class EventHook:
    """
    Provides functionality for registering and firing events
    """

    def __init__(self):
        """
        Creates a new event handler
        """
        self.__handlers: List[Callable] = []

    def __iadd__(self, handler) -> EventHook:
        self.__handlers.append(handler)
        return self

    def __isub__(self, handler) -> EventHook:
        self.__handlers.remove(handler)
        return self

    def add_top(self, handler):
        """
        Adds an event to the top of the handler list.
        This causes the handler to be called first
        :param handler:  handler
        """
        self.__handlers.insert(0, handler)

    def fire(self, *args, **keywargs):
        """
        Fires the event
        :param args: arguments for the event
        :param keywargs: keyword arguments
        :return:
        """
        for handler in self.__handlers:
            handler(*args, **keywargs)

    def clear_object_handlers(self, in_object):
        """
        Removes all handles for a given object
        :param in_object: Object that should be removed
        """
        for handler in self.__handlers:
            if handler.im_self == in_object:
                self -= in_object
