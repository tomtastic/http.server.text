""" Serve files using an HTTP request handler which returns plaintext if unsure of type """

import sys
import os
import posixpath
import mimetypes
import socketserver
from http.server import SimpleHTTPRequestHandler


class TextHandler(SimpleHTTPRequestHandler):
    """Serve stuff as plain text if unsure"""

    def end_headers(self):
        # Include additional response headers here. CORS for example:
        # self.send_header('Access-Control-Allow-Origin', '*')
        SimpleHTTPRequestHandler.end_headers(self)

    def send_head(self):
        """Common code for GET and HEAD commands.
        This sends the response code and MIME headers.
        Return value is either a file object (which has to be copied
        to the outputfile by the caller unless the command was HEAD,
        and must be closed by the caller under all circumstances), or
        None, in which case the caller has nothing further to do.
        """
        path = self.translate_path(self.path)
        filehandle = None
        if os.path.isdir(path):
            if not self.path.endswith("/"):
                # redirect browser - doing basically what apache does
                self.send_response(301)
                self.send_header("Location", self.path + "/")
                self.end_headers()
                return None
            for index in "index.html", "index.htm":
                index = os.path.join(path, index)
                if os.path.exists(index):
                    path = index
                    break
            else:
                return self.list_directory(path)
        ctype = self.guess_type(path)
        # Always read in binary mode. Opening files in text mode may cause
        # newline translations, making the actual size of the content
        # transmitted *less* than the content-length!

        try:
            with open(path, "rb") as filehandle:
                self.send_response(200)
                self.send_header("Content-type", ctype)
                fstat = os.fstat(filehandle.fileno())
                self.send_header("Content-Length", str(fstat[6]))
                self.send_header("Last-Modified", self.date_time_string(fstat.st_mtime))
                self.end_headers()
                return filehandle
        except IOError:
            self.send_error(404, "File not found")
            return None

    def guess_type(self, path):
        """Guess the type of a file.
        Argument is a PATH (a filename).
        Return value is a string of the form type/subtype,
        usable for a MIME Content-type header.
        The default implementation looks the file's extension
        up in the table self.extensions_map, using application/octet-stream
        as a default; however it would be permissible (if
        slow) to look inside the data to make a better guess.
        """

        _, ext = posixpath.splitext(path)
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        ext = ext.lower()
        if ext in self.extensions_map:
            return self.extensions_map[ext]

        return self.extensions_map[""]

    if not mimetypes.inited:
        mimetypes.init()  # try to read system mime.types
    extensions_map = mimetypes.types_map.copy()
    extensions_map.update(
        {
            "": "text/plain",  # Default was application/octet-stream
            ".py": "text/plain",
            ".c": "text/plain",
            ".h": "text/plain",
        }
    )


if __name__ == "__main__":
    PORT = int(sys.argv[1])
    with socketserver.TCPServer(("", PORT), TextHandler) as httpd:
        print(f"Listening on port {format(PORT)}. Press Ctrl+C to stop.")
        httpd.serve_forever()
