import fitz  # pip install pymupdf

nCurPage=0

def orderPages(doc, display=None):
    #order pages in the order of the bookmarks
    if display: display.updatestatusBar('Ordering pages...')
    BkMks=fillBkMks(doc)
    sortRoutines(BkMks,doc.pageCount)
    MoveThePages(BkMks,doc)
    refillBkMks(BkMks,doc)
    if display: display.updatestatusBar('Ordered pages...')

def refillBkMks(BkMks,doc):
    newTOCs=[]
    for BkMk in BkMks:
        newTOC=BkMk['BkMk']
        newTOC[2]=BkMk['pg']+1
        newTOCs.append(newTOC)
    doc.setToC(newTOCs)

def fillBkMks(doc):
    #Fill array of bookmarks, noting the order in which they appear and the pages to which they point
    BkMks=[]
    TOC = doc.getToC()
    count=0
    for t in TOC:
        BkMk={'BkMk': t, 'pg': t[2]-1, 'order': count, 'chunk':0, 'pgEnd':0}
        BkMks.append(BkMk)
        count +=1
    return BkMks

def sortRoutines(BkMks, pgCount):
    global nCurPage

    def byPg(e):
        return e['pg']
    def byOrder(e):
        return e['order']

    #Sort by page reference first
    BkMks.sort(key=byPg)

    #Calculate the chunk sizes
    for i in range(0,len(BkMks)):
        if i<len(BkMks)-1:
            BkMks[i]['chunk']=BkMks[i+1]['pg']-BkMks[i]['pg']
            BkMks[i]['pgEnd']=BkMks[i+1]['pg']
        else:
            BkMks[i]['chunk']=pgCount-BkMks[i]['pg']
            BkMks[i]['pgEnd']=pgCount-1

    nCurPage=BkMks[0]['pg'] #sets the starting point for insertion at the first bookmark pageref

    #Sort by order - i.e. back to how it was
    BkMks.sort(key=byOrder)

def MoveThePages(BkMks,doc):
    #move the pages to the right place
    global nCurPage

    for i in range(0,len(BkMks)):
        if BkMks[i]['pg']>nCurPage: #i.e. needs moving
            pgtoMove=BkMks[i]['pg']
            newPg=nCurPage
            for j in range(0,BkMks[i]['chunk']):
                doc.movePage(pgtoMove,nCurPage)
                pgtoMove +=1
                nCurPage +=1

            #Increase the pageref for other bookmarks by the chunksize where there has been a jumping of the queue
            if i<len(BkMks)-1:
                for k in range(i+1,len(BkMks)):
                    if BkMks[i]['pg']>BkMks[k]['pg']: #i.e. a queue jump
                        BkMks[k]['pg']=BkMks[k]['pg'] + BkMks[i]['chunk']

            #Reset the pageref for the BkMk we have moved
            BkMks[i]['pg']=newPg
        else:
            #if BkMk doesn't need moving then we need to increase the insertion point
            nCurPage=nCurPage+BkMks[i]['chunk']