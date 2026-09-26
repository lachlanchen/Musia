#!/usr/bin/env python3
"""Capture native Musia screenshots and a short foreground-service review demo."""
import argparse
import json
import re
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--serial', required=True)
    p.add_argument('--adb', default=str(Path.home() / 'Android/Sdk/platform-tools/adb'))
    p.add_argument('--output', type=Path, default=Path('store/.runtime/formal/android'))
    a = p.parse_args()
    if not re.fullmatch(r'emulator-\d+', a.serial):
        p.error('Use an owned emulator, never an attached phone')
    a.output.mkdir(parents=True, exist_ok=True)

    def adb(*args, binary=False):
        result = subprocess.run([a.adb, '-s', a.serial, *args], capture_output=True, check=True, timeout=90)
        return result.stdout if binary else result.stdout.decode().strip()

    name = adb('emu', 'avd', 'name').splitlines()[0]
    if not name.startswith('Musia_'):
        p.error('This is not a Musia emulator')

    def screen():
        adb('shell', 'uiautomator', 'dump', '/sdcard/musia-store.xml')
        return ET.fromstring(adb('exec-out', 'cat', '/sdcard/musia-store.xml'))

    def click(label, description=False, scroll=False):
        for _ in range(7):
            node = next((n for n in screen().iter('node') if n.get('content-desc' if description else 'text') == label), None)
            if node is not None:
                x1, y1, x2, y2 = map(int, re.findall(r'\d+', node.get('bounds')))
                if x2 > x1 and y2 > y1:
                    adb('shell', 'input', 'tap', str((x1+x2)//2), str((y1+y2)//2))
                    time.sleep(.6)
                    return
            if scroll:
                w,h = map(int, re.findall(r'(\d+)x(\d+)', adb('shell', 'wm', 'size'))[-1])
                adb('shell', 'input', 'swipe', str(w//2), str(h*3//4), str(w//2), str(h//3), '350')
            time.sleep(.4)
        raise RuntimeError('Missing visible control: ' + label)

    def capture(label):
        (a.output / (label+'.png')).write_bytes(adb('exec-out', 'screencap', '-p', binary=True))

    def playing(label):
        for _ in range(30):
            raw = adb('shell', 'dumpsys', 'media_session')
            (a.output/(label+'.txt')).write_text(raw)
            section = re.search(r'package=art\.lazying\.musia\n(.*?)(?=\n {4}\S|\Z)', raw, re.S)
            if section and re.search(r'state=(?:3\b|PLAYING\b)', section.group(1)):
                return
            time.sleep(.5)
        raise RuntimeError('Musia media session is not PLAYING: '+label)

    recording = None
    try:
        adb('shell', 'input', 'keyevent', 'KEYCODE_WAKEUP')
        adb('shell', 'wm', 'dismiss-keyguard')
        adb('shell', 'am', 'force-stop', 'art.lazying.musia')
        adb('shell', 'am', 'start', '-W', '-n', 'art.lazying.musia/.MainActivity')
        time.sleep(4)
        capture('library')
        click('Practice')
        click('First Pulse')
        click('Play')
        click('O open / X muted', scroll=True)
        capture('guitar')
        # Native screenrecord only: no replacement soundtrack or reconstructed UI.
        recording = subprocess.Popen([a.adb, '-s', a.serial, 'shell', 'screenrecord', '--bit-rate', '6000000', '--time-limit', '30', '/sdcard/musia-media-playback.mp4'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
        click('Play', description=True, scroll=True)
        time.sleep(2)
        playing('foreground')
        capture('playing')
        adb('shell', 'input', 'keyevent', 'KEYCODE_HOME')
        time.sleep(1)
        playing('background')
        adb('shell', 'cmd', 'statusbar', 'expand-notifications')
        time.sleep(2)
        capture('notification')
        playing('notification')
        recording.wait(timeout=40)
        adb('pull', '/sdcard/musia-media-playback.mp4', str(a.output/'media-playback.mp4'))
        (a.output/'receipt.json').write_text(json.dumps({'emulator':name, 'serial':a.serial, 'capture':'native adb screenrecord', 'checks':['foreground PLAYING','background PLAYING','notification PLAYING'], 'audio':'screenrecord has no audio track; demonstration of native playback controls, not audible QA'}, indent=2)+'\n')
    finally:
        if recording and recording.poll() is None:
            recording.terminate()
            recording.wait(timeout=10)
        adb('shell', 'cmd', 'statusbar', 'collapse')
        adb('shell', 'am', 'force-stop', 'art.lazying.musia')


if __name__ == '__main__':
    main()
