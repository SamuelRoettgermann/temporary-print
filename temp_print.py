import builtins
import threading
import time
from typing import List, Tuple, Union, Any, NoReturn


class TemporaryText:
    """A class that allows for temporary printing of one-liners"""
    display_time: Union[float, None]
    _visible: int
    _thread: threading.Thread
    refresh_rate: Union[float, None]
    _need_stop: bool
    _queue: List[Tuple[str, float, bool, Any, bool, float, float]]

    # queue := text, display_time, flush, file, normal_print, delay, post_delay

    def __init__(self, display_time: Union[float, None] = None, refresh_rate: Union[float, None] = None):
        """Creates a new instance of TemporaryText.
        Only one instance of this should be active at a time, and no other print statements can be done

        :param display_time: time in seconds for which the text should get displayed

        :param refresh_rate: Describes how many seconds need to pass until a stop-check.
        A stop-check is a simple check that checks whether the user wants the text to disappear again.
        Only useful if you don't know how long you want the text to be _visible.
        It's only necessary if you plan on setting the overwrite-flag in the print method of this class.
        None signals to just wait for the entire display_time.
        A value of 0 or smaller signals to make permanent checks. This is very CPU-intensive and only recommended for
        scenarios where you can't wait even a small refresh-rate but need instant adjustments. Because of the GIL this
        will notably slow your application down.
        Any positive values describe the amount of time to wait before making a stop-check.
        The default value is recommended if you know the waiting lengths prior."""
        self.set_display_time(display_time)
        self._visible = 0
        self._thread = threading.Thread(target=lambda: None)
        self.set_refresh_rate(refresh_rate)
        self._need_stop = False
        self._queue = []

    def _clean_up(self):
        builtins.print('\r' + ' ' * self._visible + '\r', end="")
        self._visible = 0
        self._need_stop = False

    def skip(self):
        """Allows to skip the currently displayed text"""
        if self.is_running():
            self._need_stop = True

    def _wait(self, wait_time: float):
        if not wait_time or self._need_stop:
            return

        refresh_rate = self.refresh_rate  # save that variable, as it might get swapped during execution otherwise

        if refresh_rate is None:
            # don't refresh at all if refresh_rate rate is None
            time.sleep(wait_time)
        elif refresh_rate <= 0:
            # permanent checks
            stop_time = time.time() + wait_time
            while time.time() < stop_time:
                if self._need_stop:
                    break
        else:
            # checks with a period of refresh_rate
            iterations = wait_time // refresh_rate
            stop_time = time.time() + wait_time
            for _ in range(int(iterations)):
                if self._need_stop and time.time() < stop_time:
                    break

                time.sleep(refresh_rate)

            if not self._need_stop and (t := time.time()) < stop_time:
                time.sleep(stop_time - t)

    def _print(self):
        while len(self._queue):
            text, display_time, flush, file, print_normal, delay, post_delay = self._queue.pop(0)

            self._wait(delay)
            if print_normal:
                builtins.print(text)
                self._wait(post_delay)
                continue

            self._visible = len(text)
            builtins.print(text, end='', flush=flush, file=file)
            self._wait(display_time)
            self._wait(post_delay)

            self._clean_up()

    def _try_process(self, overwrite):
        if not len(self._queue):
            return

        if not self._thread.is_alive() or overwrite:
            if self._thread.is_alive():
                self.skip()
                self._thread.join()

            # here we know the _thread is not alive
            self._thread = threading.Thread(target=TemporaryText._print, args=(self,))
            self._thread.start()

    def print(self,
              *texts,
              display_time: float = None,
              sep: str = ' ',
              end: str = '',
              flush: bool = False,
              file=None,
              priority: bool = False,
              overwrite: bool = False,
              print_normal: bool = False,
              delay: float = 0,
              post_delay: float = 0) \
            -> NoReturn:

        # texts is a tuple which we are now converting to the string to print
        text: str = sep.join(str(e) for e in texts) + end

        # my method cannot recover from any newlines or carriage returns
        if '\n' in text or '\r' in text:
            raise ValueError("the printed text can't contain a newline or carriage return character")

        # build the tuple we want to pass the queue
        queue_tuple = (text,
                       self.display_time if display_time is None else max(display_time, 0),
                       flush,
                       file,
                       print_normal,
                       delay,
                       post_delay)

        if overwrite or priority:
            self._queue.insert(0, queue_tuple)
        else:
            self._queue.append(queue_tuple)

        self._try_process(overwrite)

    def set_display_time(self, display_time: Union[float, None]) -> NoReturn:
        if not (display_time is None) and display_time < 0:
            raise ValueError("display_time can't be less than 0")

        self.display_time = display_time

    def set_refresh_rate(self, refresh_rate: float) -> NoReturn:
        self.refresh_rate = refresh_rate

    def is_running(self) -> bool:
        """Return true if a temporary text is currently shown, false otherwise"""
        return self._thread.is_alive() or len(self._queue)

    def clear(self, undisplay: bool = False) -> NoReturn:
        """Clears the queue and if wanted also clears the currently displayed text"""
        self._queue = []
        if undisplay and self.is_running():
            self.skip()

    def not_initialized(self) -> bool:
        return self.display_time is None


_printer: TemporaryText = TemporaryText()


def print(*args,
          display_time: float = None,
          sep: str = ' ',
          end: str = '',
          flush: bool = False,
          file=None,
          priority: bool = False,
          overwrite: bool = False,
          persistent: bool = True,
          delay: float = 0,
          post_delay: float = 0) \
        -> NoReturn:
    """Expansion for the print method.
    For more detailed information on how this method can be fine-tuned read the parameter descriptions.

    :param args: The value(s) to be printed.

    :param display_time: The time for which the texts will be displayed. Will fall back to self.display_time if
    set to None.

    :param sep: string inserted between values, default a space.

    :param end: string appended after the last value.

    :param flush: whether to forcibly flush the stream.

    :param file: a file-like object (stream); defaults to the current sys.stdout.

    :param priority: Tells the print statement to make this texts the next statement to print in the queue.
    If overwrite is True, then it overshadows this parameter.

    :param overwrite: Same as priority, but additionally tries to get the texts onto the screen as fast as possible,
    by removing the currently displayed texts. If no texts is currently displayed, then this gets ignored.
    For this I use a busy-waiting inside the print-thread with a sleeping period of self.refresh_rate.
    When the

    :param persistent: Allows for normal enqueued printing and all characters are allowed, including '\n' and '\r'

    :param delay: Specifies how long to wait for the texts to show up

    :param post_delay: Same as delay, but after the printing has finished
    """
    if not persistent and not display_time and _printer.not_initialized():
        raise AttributeError("Couldn't find a display time.\n"
                             "You can either call tempPrint.fix_display_time to set that for all future prints or set "
                             "the display_time parameter of this method to change it only for the current print")

    return _printer.print(*args, display_time=display_time, sep=sep, end=end, flush=flush, file=file,
                          priority=priority, overwrite=overwrite, print_normal=persistent, delay=delay,
                          post_delay=post_delay)


def set_display_time(display_time: float) -> NoReturn:
    """Changes the display_time, cannot be less than 0"""
    _printer.set_display_time(display_time)


def set_refresh_rate(refresh_rate: float) -> NoReturn:
    """Changes the refresh-rate.
    Changes to this don't take affect the string that is currently displayed,
    but will impact all future prints, even the ones already enqueued"""
    _printer.set_refresh_rate(refresh_rate)


def is_running() -> bool:
    """Return true if a temporary text is currently shown, false otherwise"""
    return _printer.is_running()


def clear(undisplay: bool = False) -> NoReturn:
    """Clears the queue and if wanted also clears the currently displayed text"""
    _printer.clear(undisplay)


