# Python 2/3 compatibility
try:
    basestring
except NameError:
    basestring = str


def issequence(obj):
    """Test if object is sequence, not a string.

    Args:
        obj (object): object to test

    Returns:
        bool: is object a sequence
    """
    if isinstance(obj, basestring):
        return False
    try:
        iter(obj)
    except TypeError:
        return False
    return True
