import requests
from bs4 import BeautifulSoup

url = "https://news.google.com/rss/search?q=crypto"

res = requests.get(url)
soup = BeautifulSoup(res.text, "xml")

for item in soup.find_all("item")[:5]:
    print(item.title.text)
