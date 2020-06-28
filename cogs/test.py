import os

dir = os.listdir('./')
itemlist = []
for item in dir:
    if item.endswith(('.m4a', 'webm')):
        itemlist.append(os.stat(item).st_size)
mb = round((sum(itemlist)/(1024*1024)),2)

print(mb)