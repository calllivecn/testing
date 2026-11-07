import tempfile
import unittest
import select
import subprocess
import sys
from unittest import mock
from pathlib import Path

import inotify
from inotify import E, INotify


class RecursiveWatchTests(unittest.TestCase):
    def test_fast_nested_creation_and_deletion(self):
        with tempfile.TemporaryDirectory() as tmp, INotify() as ni:
            root = Path(tmp)
            ni.inotify_add_watch_recursive(root, E.IN_MODIFY)
            nested = root / "d1" / "d2" / "d3"
            nested.mkdir(parents=True)
            ni.read()
            self.assertIn(nested, ni.path2wd)

            nested.rmdir()
            ni.read()
            self.assertNotIn(nested, ni.path2wd)

    def test_moved_in_tree(self):
        with tempfile.TemporaryDirectory() as tmp, INotify() as ni:
            base = Path(tmp)
            root = base / "root"
            root.mkdir()
            source = base / "source"
            (source / "child").mkdir(parents=True)
            ni.inotify_add_watch_recursive(root, E.IN_MODIFY)
            source.rename(root / "source")
            ni.read()
            self.assertIn(root / "source" / "child", ni.path2wd)

    def test_failed_watch_is_not_recorded(self):
        with tempfile.TemporaryDirectory() as tmp, INotify() as ni:
            with self.assertRaises(FileNotFoundError):
                ni.inotify_add_watch(Path(tmp) / "missing", E.IN_CREATE)
            self.assertEqual(ni.wd, {})


class MultipleEventsTests(unittest.TestCase):
    def test_open_close_and_move(self):
        with tempfile.TemporaryDirectory() as tmp, INotify() as ni:
            root = Path(tmp)
            original = root / "original"
            original.touch()
            mask = E.IN_OPEN | E.IN_CLOSE | E.IN_MOVE
            ni.inotify_add_watch(root, mask)

            with original.open("w") as stream:
                stream.write("test")
            renamed = root / "renamed"
            original.rename(renamed)

            self.assertTrue(select.select([ni.fd], [], [], 1)[0])
            events = ni.read()
            for expected, path in (
                (E.IN_OPEN, original),
                (E.IN_CLOSE_WRITE, original),
                (E.IN_MOVED_FROM, original),
                (E.IN_MOVED_TO, renamed),
            ):
                self.assertTrue(any(expected in flags and name == path
                                    for flags, name in events))


class CommandLineTests(unittest.TestCase):
    def test_help(self):
        result = subprocess.run(
            [sys.executable, str(Path(__file__).with_name("inotify.py")), "-h"],
            capture_output=True, text=True, check=True,
        )
        self.assertIn("递归监控注意事项", result.stdout)
        self.assertIn("IN_OPEN|IN_CLOSE|IN_MOVE", result.stdout)

    def test_invalid_event(self):
        result = subprocess.run(
            [sys.executable, str(Path(__file__).with_name("inotify.py")),
             "-e", "IN_INVALID", "."], capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("无效的事件名称", result.stderr)

    def test_multiple_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = [Path(tmp) / "one", Path(tmp) / "two"]
            for path in paths:
                path.mkdir()
            for recursive in (False, True):
                with self.subTest(recursive=recursive):
                    argv = ["inotify.py"] + (["-r"] if recursive else [])
                    argv += [str(path) for path in paths]
                    with mock.patch.object(sys, "argv", argv), mock.patch.object(inotify, "INotify") as cls:
                        watcher = cls.return_value.__enter__.return_value
                        watcher.read.side_effect = KeyboardInterrupt
                        inotify.main()
                        add = (watcher.inotify_add_watch_recursive if recursive
                               else watcher.inotify_add_watch)
                        self.assertEqual(add.call_args_list, [
                            mock.call(path, inotify.IN_ALL_EVENTS) for path in paths
                        ])


if __name__ == "__main__":
    unittest.main()
