import webview, sys, ctypes
ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
def on_closed(): sys.exit(0)
if __name__ == '__main__':
    window = webview.create_window('MISO OS', 'http://159.223.186.21:8000', fullscreen=True, frameless=True, on_top=True)
    window.events.closed += on_closed
    webview.start()
