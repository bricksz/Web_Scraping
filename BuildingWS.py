from urllib.request import urlopen
from urllib.error import HTTPError
from bs4 import BeautifulSoup

# html = urlopen('http://pythonscraping.com/pages/page1.html')
html = urlopen('https://news.google.com/topics/CAAqJggKIiBDQkFTRWdvSkwyMHZNREZ4ZVdkc0VnVmxiaTFWVXlnQVAB?hl=en-US&gl=US&ceid=US%3Aen')

bsobj=BeautifulSoup(html.read(), 'lxml')
#print(bsobj.h1)     # or bsobj.html.body.h1     , bsobj.body.h1     , bsobj.html.h1
'''
try:
    html = urlopen('http://www.pythonscraping.com/pages/page1.html')
except HTTPError as e:
    print(e)
    #return null, break, or do some other "Plan B"
else:
    #program continue. Note: If you return or break in the
    #exception catch, you do not need to use the "else" statement
'''
'''
If an HTTP error code is returned, it will print the error and will not execute the rest of the program below the else statement.
'''

nameList = bsobj.findAll('span')
print(nameList)