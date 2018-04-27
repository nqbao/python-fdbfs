from unittest import TestCase
from fdbfs.blob import BlobWriter, BlobReader
import fdb


class BlobTestCase(TestCase):
    def setUp(self):
        self.db = fdb.open()
        self.directory = fdb.directory.create_or_open(self.db, ('blob-test',))

    def tearDown(self):
        del self.db[
            self.directory.range()
        ]
        self.db = None

    def test_blob_writer(self):
        writer = BlobWriter(self.db, self.directory, 4)
        writer.write('abcd')
        writer.write('efg')

        self.assertEqual(7, writer.tell())

        reader = BlobReader(self.db, self.directory, 4)
        self.assertEquals('abcdefg', reader.read())

    def test_seek_read(self):
        writer = BlobWriter(self.db, self.directory, 4)
        writer.write('abcdefg')

        self.assertEqual(7, writer.tell())

        reader = BlobReader(self.db, self.directory, 4)
        reader.seek(4)
        self.assertEquals('efg', reader.read())

        reader.seek(2)
        self.assertEquals('cdefg', reader.read())