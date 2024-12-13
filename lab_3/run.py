#!/usr/bin/env python3
from entity.publisher import run_publisher
from ftp_feeder import feed_ftp
from multiprocessing import Process

if __name__ == "__main__":
    publisher_process = Process(target=run_publisher)
    ftp_process = Process(target=feed_ftp)

    publisher_process.start()
    ftp_process.start()

    publisher_process.join()
    ftp_process.join()