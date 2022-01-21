import argparse
import logging
from pathlib import Path

from .objective_function import SessionMaker
from .config import OptclimConfig


def main():
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument('config', type=Path,
                        help='name of configuration file')
    args = parser.parse_args()

    cfg = OptclimConfig(args.config)
    dbName = cfg.cfg['setup']['db']

    if dbName is not None:
        logging.info(f'creating database {dbName}')

        sessionmaker = SessionMaker()

        session = sessionmaker(dbName)
        session.close()


if __name__ == '__main__':
    main()
