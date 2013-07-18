from connect import HttpQueryPool
from linkmanager import HyperlinkManager
from bs4 import BeautifulSoup
from urlparse import urlparse
from Tkinter import Tk, Frame, Entry, Text, BOTH, END, WORD

error_text = "Error querying %s"

class Renderer(Frame):
    def __init__(self, parent, pool):
        Frame.__init__(self, parent, background="white")
        self.parent = parent
        self.pool = pool
        self.initUI()

    def initUI(self):
        # parent config
        self.parent.title("Simple")
        self.parent.bind("<Return>", self.search)

        # frame fill
        self.pack(fill=BOTH, expand=1)

        # text entry config
        self.entry = Entry(self)
        self.entry.pack()

        # text config
        self.txt = Text(self, wrap=WORD)
        self.txt_config()
        self.txt.pack(fill=BOTH, expand=1)
        self.links = HyperlinkManager(self.txt)
        self.txt.insert(END, "Query google via the search bar ^")

    def txt_config(self):
        self.txt.tag_config("a", foreground="blue", underline=1)
        self.txt.tag_bind("a", "<Enter>", lambda _ : self.txt.config(cursor="hand2"))
        self.txt.tag_bind("a", "<Leave>", lambda _ : self.txt.config(cursor="arrow"))
        self.txt.config(cursor="arrow")

    def clear_text(self):
        self.txt.delete(1.0, END)

    def lazy_link(self, url):
        return lambda : self.reload_page(url, self.basic_render)

    def newline(self):
        self.txt.insert(END, "\n")

    def google_links(self, html):
        soup = BeautifulSoup(html)
        for link in soup.find_all("h3", class_="r"):
            linkurl = "http://www.google.com" + link.a["href"]
            callback = self.lazy_link(linkurl)
            self.newline()
            self.txt.insert(END, link.a.get_text(), self.links.add(callback))
            self.txt.insert(END, linkurl)
            self.newline()

    def basic_render(self, html):
        self.txt.insert(END, html)

    def search(self, _):
        query = self.entry.get()
        search_url = "http://www.google.com/search?q=" + query
        self.reload_page(search_url, self.google_links)

    def reload_page(self, url, renderer):
        print "url: ", url
        self.clear_text()
        urlparts = urlparse(url)
        connection = self.pool.get(urlparts.netloc)
        html = connection.query(url)
        if html:
            renderer(html)
        else:
            self.txt.insert(END, error_text % url)

def run_renderer(pool):
    root = Tk()
    root.geometry("250x150+300+300")
    app = Renderer(root, pool)
    root.mainloop()

if __name__ == '__main__':
    pool = HttpQueryPool()
    run_renderer(pool)
