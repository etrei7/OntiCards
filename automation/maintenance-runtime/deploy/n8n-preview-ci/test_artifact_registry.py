import tempfile, unittest
from pathlib import Path
import artifact_registry as a

class PrivateSnapshotTests(unittest.TestCase):
    def test_private_copy_is_independent_before_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'source';dest=root/'snapshot'
            source.write_bytes(b'original');a.copy_snapshot(source,dest,100)
            source.write_bytes(b'changed')
            self.assertEqual(dest.read_bytes(),b'original')
            self.assertEqual(dest.stat().st_mode&0o777,0o600)
            with self.assertRaises(FileExistsError):a.copy_snapshot(source,dest,100)
    def test_symlink_and_oversize_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'source';source.write_bytes(b'oversize')
            link=root/'link';link.symlink_to(source)
            with self.assertRaises(OSError):a.copy_snapshot(link,root/'dest',100)
            with self.assertRaises(ValueError):a.copy_snapshot(source,root/'large',1)

if __name__=='__main__':unittest.main(verbosity=2)
