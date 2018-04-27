import fdb
import math


DEFAULT_CHUNK_SIZE = 1024*10


class BlobManager(object):
    def __init__(self, db, directory=None, chunk_size=DEFAULT_CHUNK_SIZE):
        self._db = db
        self._space = fdb.directory.create_or_open(db, directory or ('blobs',))
        self._chunk_size = chunk_size

    def get_reader(self, key):
        pass

    def get_writer(self, key):
        pass


class BlobReader(object):
    """
    Seekable blob reader
    """
    def __init__(self, db, space, chunk_size):
        self._db = db
        self._space = space
        self._chunk_size = chunk_size
        self._cursor = 0

    def read(self, size=None):
        return self._read_chunk(self._db, self._cursor)

    @fdb.transactional
    def _read_chunk(self, tr, cursor):
        chunk_index = cursor / self._chunk_size
        return tr[self._space.pack((chunk_index,))]

    def seek(self, cursor):
        self._cursor = cursor

    def tell(self):
        return self._cursor

    def close(self):
        pass


class BlobWriter(object):
    """
    Seekable blob writer
    """
    def __init__(self, db, space, chunk_size):
        self._db = db
        self._space = space
        self._chunk_size = chunk_size
        self._cursor = 0

    def write(self, data):
        # this is not thread-safe
        self._cursor = self._write(self._db, self._cursor, data)

    @fdb.transactional
    def _write(self, tr, cursor, data):
        buf = buffer(data)
        chunk_size = self._chunk_size

        chunks = int(math.ceil(float(len(buf)) / chunk_size))
        chunk_index = cursor / chunk_size
        start_cursor = chunk_index * chunk_size

        # write the first partial chunk
        if start_cursor != cursor:
            next_cursor = start_cursor + chunk_size
            chunk = tr[self._space.pack((chunk_index,))]

            assert chunk.present(), 'Do not support missing chunk yet'

            # TODO: we may cache this current chunk to avoid repeat reading
            new_chunk = chunk[0:cursor - start_cursor] + buf[0:next_cursor - cursor]
            tr[self._space.pack((chunk_index,))] = new_chunk

            buf = buffer(data, next_cursor - cursor)

            # advance the cursor
            if len(new_chunk) == chunk_size:
                cursor = next_cursor
            else:
                cursor = start_cursor + len(new_chunk)

            if len(buf) == 0:
                return cursor

            return self._write(tr, cursor, buf)

        for i in range(chunks):
            chunk = data[i * chunk_size:(i+1) * chunk_size]
            this_chunk_size = len(chunk)
            assert this_chunk_size <= chunk_size

            tr[self._space.pack((chunk_index,))] = chunk
            cursor += len(chunk)
            chunk_index += 1

        return cursor

    def seek(self, cursor):
        pass

    def tell(self):
        return self._cursor

    def close(self):
        pass