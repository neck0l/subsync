#!/usr/bin/env python3
import logging
logger = logging.getLogger(__name__)

from subsync import translations
translations.init()

import sys, os
from subsync import cmdargs
from subsync import loggercfg
from subsync.settings import settings


def subsync(argv=None):
    args = cmdargs.parseCmdArgs(argv)
    options = args.get('options', {})

    if options.get('logLevel') or options.get('logFile'):
        loggercfg.init(level=options.get('logLevel'), path=options.get('logFile'))
    if options.get('language'):
        translations.setLanguage(options.get('language'))

    if args:
        logger.debug('running with arguments: %r', args)

    if args.get('help'):
        cmdargs.printHelp()
        return 0

    if args.get('version'):
        print('subsync version {} on {}'.format(version()[0], sys.platform))
        return 0

    if not args.get('cli'):
        if os.path.basename(os.path.splitext(sys.argv[0])[0]) == 'subsync-cmd':
            logger.info("running command 'subsync-cmd', starting in headless mode")
            args['cli'] = True
        else:
            try:
                import wx
            except Exception as e:
                logger.warning("couldn't start wx, falling back to headless mode, %r", e)
                args['cli'] = True

    if args.get('cli'):
        return cli(**args)
    else:
        return gui(**args)


def gui(sync=None, fromFile=None, batch=False, options={}, **args):
    import wx
    from subsync.gui.mainwin import MainWin
    from subsync.gui.batchwin import BatchWin
    from subsync.gui.errorwin import showExceptionDlg

    class _App(wx.App):
        def InitLocale(self):
            # #167: wxPython >= 4.1 on Windows / Python >= 3.8 can abort with
            # 'assert strcmp(setlocale(0,0), "C") == 0' in wxLocale::GetInfo().
            # Pin the C locale to satisfy wx (harmless for this app).
            import locale
            try:
                locale.setlocale(locale.LC_ALL, 'C')
            except Exception:
                pass

    try:
        settings().load()
    except Exception as e:
        logger.warning('settings load failed, %r', e, exc_info=True)

    try:
        app = _App()
        _init(options)
        tasks = _loadTasks(sync, fromFile)

        if batch or len(tasks) > 1:
            win = BatchWin(None, tasks)
        else:
            task = None
            if len(tasks) > 0:
                task = tasks[0]
            win = MainWin(None, task)

        win.Show()
        app.MainLoop()
        return 0

    except Exception as err:
        logger.error('subsync failed, %r', err, exc_info=True)
        showExceptionDlg()
        return 1

    finally:
        settings().save()


def _setupWindowsConsole():
    """Ensure a usable console on Windows for headless/CLI mode (#191).

    - If the process already has a console (launched from a terminal), use it
      as-is so output stays in that terminal and piped stdout is preserved.
    - Otherwise attach to the launching terminal if there is one; only when
      there is none (e.g. double-clicked GUI exe) allocate a new console.

    Returns one of 'existing', 'attached', 'allocated', 'skipped'.
    """
    if sys.platform != 'win32':
        return 'skipped'

    import ctypes
    kernel32 = ctypes.windll.kernel32
    if kernel32.GetConsoleWindow() != 0:
        return 'existing'

    ATTACH_PARENT_PROCESS = -1
    how = 'attached' if kernel32.AttachConsole(ATTACH_PARENT_PROCESS) else None
    if how is None:
        kernel32.AllocConsole()
        how = 'allocated'

    sys.stdout = open('CONOUT$', 'w')
    sys.stderr = open('CONOUT$', 'w')
    sys.stdin = open('CONIN$', 'r')
    return how


def cli(sync=None, fromFile=None, verbose=1, offline=False, options={}, **args):
    from subsync import cli

    try:
        _setupWindowsConsole()
    except Exception as err:
        cli.pr.printException(0, err, 'console allocation failed')

    try:
        _init(options)
        tasks = _loadTasks(sync, fromFile)

    except Exception as err:
        cli.pr.printException(0, err)
        return 1

    try:
        app = cli.App(verbosity=verbose, offline=offline)
        return app.runTasks(tasks)

    except Exception as err:
        logger.error('subsync failed, %r', err, exc_info=True)
        return 1


def version():
    try:
        from subsync.version import version, version_short
        return version_short, version
    except:
        return None, 'UNDEFINED'


def _init(options={}):
    if options:
        settings().set(temp=True, **options)

    if not loggercfg.initialized:
        loggercfg.init(level=settings().logLevel, path=settings().logFile)

    if settings().logBlacklist:
        loggercfg.setBlacklistFilters(settings().logBlacklist)

    logger.info('starting subsync %s@%s', version()[1], sys.platform)
    translations.setLanguage(settings().language)

    if settings().test:
        print("[!] TEST MODE ENABLED! You're on your own!", file=sys.stderr)
        logger.warning("TEST MODE ENABLED! You're on your own!")


def _loadTasks(sync=None, fromFile=None):
    from subsync.synchro import SyncTaskList
    if sync:
        return SyncTaskList.deserialize(sync)
    if fromFile:
        return SyncTaskList.load(fromFile)
    return []


if __name__ == "__main__":
    res = subsync()
    sys.exit(res)

