import logging
import time
import webbrowser

import click

from recorder.source import douyin

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


@click.group()
def cli():
    pass


@cli.command()
@click.option('--room_id', '-r', type=int, required=True)
@click.option('--interval', '-i', type=int, default=10)
def sub(room_id, interval):
    while True:
        if not douyin.get_stream(room_id):
            # not live yet
            time.sleep(interval)
            continue

        logging.info(f'Live started: {room_id}')
        webbrowser.open(f'https://live.douyin.com/{room_id}')

        while True:
            time.sleep(interval)
            if not douyin.get_stream(room_id):
                # live ended
                logging.info(f'Live ended: {room_id}')
                break


if __name__ == '__main__':
    cli()
