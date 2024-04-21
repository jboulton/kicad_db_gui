import argparse
import configparser
import json
import logging
import logging.config
import logging.handlers
import os
import pathlib
import signal
import sys
import psycopg2
import gui

logger = logging.getLogger("DashN2kMonitor")

CONFIG_FILENAME = "db_manager.ini"
SHUTDOWN = False
CONFIG_FILE_PARSER = None
MAIN_GUI = None

if sys.platform.startswith('darwin'):
    # Set app name, if PyObjC is installed
    # Python 2 has PyObjC preinstalled
    # Python 3: pip3 install pyobjc-framework-Cocoa
    try:
        from Foundation import NSBundle
        bundle = NSBundle.mainBundle()
        if bundle:
            app_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
            app_info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
            if app_info:
                app_info['CFBundleName'] = "KiCAD Db Manager"
    except ImportError:
        pass


def _signal_cntrl_c(os_signal, os_frame):
    logger.info("Shutdown")
    if MAIN_GUI:
        MAIN_GUI.close()


def _get_log_level(level) -> int:
    log_level = logging.NOTSET
    if level == 1:
        log_level = logging.WARN
    elif level == 2:
        log_level = logging.INFO
    elif level == 3:
        log_level = logging.DEBUG
    return log_level


def _setup_logging():
    config_file = pathlib.Path("logger_config.json")
    with open(config_file, encoding='utf-8') as f_in:
        config = json.load(f_in)

    logging.config.dictConfig(config)

    # queue_handler = logging.getHandlerByName("queue_handler")
    # if queue_handler is not None:
    #    queue_handler.listener.start()
    #    atexit.register(queue_handler.listener.stop)


def _parse_commandline_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v",
        "--verbose",
        const=1,
        default=0,
        type=int,
        nargs="?",
        help="""increase verbosity:
                        0 = Not set,  1 only warnings, 2 = info, 3 = debug.
                        No number means info. Default is no verbosity.""",
    )
    parser.add_argument("-l", "--logfile", dest="logfilename",
                        default="", help="logfile location", metavar="FILE")
    args = parser.parse_args()
    return args


def _save_config():
    if CONFIG_FILE_PARSER is not None:
        with open(CONFIG_FILENAME, 'w', encoding='utf-8') as configfile:
            CONFIG_FILE_PARSER.write(configfile)


def _parse_config():

    global CONFIG_FILE_PARSER  # pylint: disable=global-statement
    new_ini_file = False
    CONFIG_FILE_PARSER = configparser.ConfigParser()
    CONFIG_FILE_PARSER.defaults()

    try:
        ini_f = open(CONFIG_FILENAME, encoding='utf-8')
        ini_f.close()
    except FileNotFoundError:
        default = {
            'log_level': 3
        }
        kicad_db_manager = {
            'installation_description_2': "A Development Happening Place"
        }
        database = {
            'db_user': '',
            'db_password': '',
            'db_host': 'localhost',
            'db_port': 5432,
            'db_database': 'kicad_lib'
        }
        CONFIG_FILE_PARSER['DEFAULT'] = default  # type: ignore
        CONFIG_FILE_PARSER['KICAD_DB_MANAGER'] = kicad_db_manager
        CONFIG_FILE_PARSER['DATABASE'] = database
        with open(CONFIG_FILENAME, 'w', encoding='utf-8') as configfile:
            CONFIG_FILE_PARSER.write(configfile)
        new_ini_file = True

    if not new_ini_file:
        CONFIG_FILE_PARSER.read(CONFIG_FILENAME)
    return CONFIG_FILE_PARSER


def _make_db_connection(**kwargs):
    connection = psycopg2.connect(
        user=kwargs["db_user"],
        password=kwargs["db_password"],
        host=kwargs["db_host"],
        port=kwargs["db_port"],
        database=kwargs["db_database"],
    )
    return connection


def main():
    """The main Shebang!"""
    # Catch CNTRL-C signal
    signal.signal(signal.SIGINT, _signal_cntrl_c)
    args = _parse_commandline_arguments()
    config = _parse_config()
    log_level = args.verbose
    if log_level == 0:
        log_level = config.getint('DEFAULT', 'log_level')

    _setup_logging()

    logger.info("Starting up")
    db_connection = _make_db_connection(**config['DATABASE'])
    global MAIN_GUI
    MAIN_GUI = gui.mainGUI(db_connection)


if __name__ == "__main__":
    main()
