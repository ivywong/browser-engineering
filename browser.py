import socket
import ssl


class URL:
    def __init__(self, url: str) -> None:
        self.socket = None
        self.view_source = False

        # TODO: figure out better way to parse urls
        if url.startswith("data:"):
            self.scheme, url = url.split(":", 1)
        if url.startswith("view-source:"):
            self.view_source = True
            url = url.split(":", 1)[1]
            self.scheme, url = url.split("://", 1)

        elif "://" in url:
            self.scheme, url = url.split("://", 1)

        assert self.scheme in ["http", "https", "file", "data"]

        if self.scheme == "data":
            self.content_type, self.content = url.split(",", 1)

        elif self.scheme == "file":
            self.path = url

        elif self.scheme in ["http", "https"]:
            if "/" not in url:
                url = url + "/"

            self.host, url = url.split("/", 1)
            self.path = "/" + url

            if self.scheme == "http":
                self.port = 80
            elif self.scheme == "https":
                self.port = 443

            if ":" in self.host:
                self.host, port = self.host.split(":", 1)
                self.port = int(port)

            self.header_dict = {
                "Host": self.host,
                "Connection": "Keep-Alive",
                "User-Agent": "pybrowser",
            }

    def get_headers(self):
        return "".join([f"{k}: {v}\r\n" for k, v in self.header_dict.items()])

    def open_file(self):
        import pathlib
        path = pathlib.Path(self.path)
        if path.exists() and path.is_file():
            with path.open() as f:
                content = f.read()
                return content
        elif path.exists() and path.is_dir():
            return "".join([f"- {str(c)}\r\n" for c in path.iterdir()])

        return "404 File not found\r\n"

    def open_data(self):
        # only support basic media types for now
        if self.content_type not in ["text/html", "text/plain"]:
            return ""
        return self.content + "\n"

    def request(self):
        if not self.socket:
            self.socket = socket.socket(
                family=socket.AF_INET,
                type=socket.SOCK_STREAM,
                proto=socket.IPPROTO_TCP,
            )
            self.socket.connect((self.host, self.port))

            if self.scheme == "https":
                ctx = ssl.create_default_context()
                self.socket = ctx.wrap_socket(
                    self.socket, server_hostname=self.host)

        request = f"GET {self.path} HTTP/1.1\r\n"
        request += self.get_headers()
        request += "\r\n"

        self.socket.send(request.encode("utf8"))

        response = self.socket.makefile("r", encoding="utf8", newline="\r\n")
        statusline = response.readline()
        version, status, explanation = statusline.split(" ", 2)

        response_headers = {}
        while True:
            line = response.readline()
            if line == "\r\n":
                break

            # create map of headers and ignore case
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()

        # these have to do with compression, which we aren't handling rn
        assert "transfer-encoding" not in response_headers
        assert "content-encoding" not in response_headers

        content = response.read(int(response_headers["content-length"]))

        return content

    def cleanup(self):
        if self.socket:
            self.socket.close()


def show(body: str):
    in_tag = False
    in_entity = False
    curr_entity = ""

    ENTITIES = {
        "lt": "<",
        "gt": ">",
    }
    for c in body:
        if c == "&":
            in_entity = True
        elif c == ";":
            print(ENTITIES[curr_entity]
                  if curr_entity in ENTITIES else "", end="")
            curr_entity = ""
            in_entity = False
        elif in_entity:
            curr_entity += c
        elif c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag and not in_entity:
            print(c, end="")


def load(url: URL):
    if url.scheme == "file":
        show(url.open_file())
    elif url.scheme == "data":
        show(url.open_data())
    elif url.scheme in ["http", "https"]:
        body = url.request()
        if url.view_source:
            print(body)
        else:
            show(body)


if __name__ == "__main__":
    import sys
    url = URL(sys.argv[1])
    load(url)
    # test reusing sockets
    load(url)

    url.cleanup()
