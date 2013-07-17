from connect import HttpQuery
from bs4 import BeautifulSoup
from Tkinter import Tk, Frame, Entry, Text, BOTH, END, WORD

error_text = "Error querying %s"

class Renderer(Frame):
    def __init__(self, parent, lookup=None):
        Frame.__init__(self, parent, background="white")
        self.parent = parent
        self.lookup = lookup
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
        self.txt.tag_config("a", foreground="blue", underline=1)
        self.txt.tag_bind("a", "<Enter>", lambda _ : self.txt.config(cursor="hand2"))
        self.txt.tag_bind("a", "<Leave>", lambda _ : self.txt.config(cursor="arrow"))
        self.txt.config(cursor="arrow")
        self.txt.pack(fill=BOTH, expand=1)
        self.txt.insert(END, "Query google via the search bar ^")

    def clear_text(self):
        self.txt.delete(1.0, END)

    def lazy_link(self, url):
        return lambda _: self.reload_page(url, self.basic_render)

    def newline(self):
        self.txt.insert(END, "\n")

    def google_links(self, html):
        soup = BeautifulSoup(html)
        for link in soup.find_all("h3", class_="r"):
            self.newline()
            self.txt.tag_bind("a", "<Button-1>", self.lazy_link(link.a["href"]))
            self.txt.insert(END, link.a.get_text(), "a")
            self.newline()

    def basic_render(self, html):
        return html

    def search(self, _):
        query = self.entry.get()
        self.reload_page(query, self.google_links)

    def reload_page(self, query, render):
        self.clear_text()
        html = self.lookup(query)
        if html:
            render(html)
        else:
            self.txt.insert(END, error_text % query)

def run_renderer(lookup):
    root = Tk()
    root.geometry("250x150+300+300")
    app = Renderer(root, lookup)
    root.mainloop()

if __name__ == '__main__':
    client = HttpQuery("www.google.com")
    run_renderer(client.query)
