# coding=latin-1
import fitz

def max_depth(doc):
    # returns max-depth of bookmarks
    toc = doc.getToC()
    max_depth = 0
    for t in toc:
        level = t[0]
        if level > max_depth: max_depth = level
    return max_depth

def isTOC(doc, display=None):
    #returns true if there is TOC (i.e. page labels with TOC)
    for pg in range(0,doc.pageCount):
        page=doc[pg]
        if isTOCPage(page): return True
    return False

def isTOCPage(page):
    if page.get_label()[:4]=="TOC_": return True
    return False

def delete_toc(doc, options=None, display=None, addHistory=True):
    # delete pages with pagelabel starting 'TOC'
    if display: display.updatestatusBar("Deleting TOC...")

    def adjusttoc(doc, no_pages):
        def search_tree(node):
            for child_node in display.tree.get_children(node):
                pg = display.tree.item(child_node)['values'][2] - 1
                if pg > 0: pg -= no_pages
                pgLbl = doc[pg].get_label()
                display.tree.set(child_node, 1, pgLbl)
                display.tree.set(child_node, 2, pg + 1)
                display.mirrorinChronoTree(child_node)
                if display.tree.get_children(child_node):
                    search_tree(child_node)

        search_tree("")

    def getStartEndPage():
        stPage = 0
        enPage = 0
        flag = False
        for i in range(0, doc.pageCount):
            page = doc[i]
            if isTOCPage(page):
                flag = True
                stPage = min(stPage, i)
                enPage = max(enPage, i)
            else:
                if flag==True: break
        if flag==True: return stPage, enPage
        return None, None

    no_pages = 0
    stPage, enPage=getStartEndPage()

    if not stPage==None and not enPage==None:
        if display: display.updatestatusBar('About to delete pages')
        doc.deletePageRange(stPage, enPage)
        no_pages = (enPage - stPage) + 1
        if display: display.updatestatusBar('Deleted pages')

    remove_toc_label(doc, no_pages)
    adjusttoc(doc,no_pages)
    for i in range(0,no_pages): display.dlist_tab.pop(0)
    display.readTree()

    if addHistory: display.adddocHistory({'code': 'DOC_removetoc'})

    if display: display.updatestatusBar("Deleted TOC.")
    return True


def remove_square_brackets(txt):
    # removes square brackets from end of string
    rBracket=txt.rfind(']')
    if rBracket==len(txt)-1:
        lBracket=txt.rfind('[')
        return txt[:lBracket].rstrip()
    return txt




def write_toc(doc, options, display=None, addHistory=True):
    if not 'margin' in options: options['margin']=25
    if options['maxDepth']>doc.max_depth(): options['maxDepth']=doc.max_depth()

    new_doc=fitz.open() #doc for storing toc
    lnks=[]

    if display: display.updatestatusBar("Adding TOC...")

    def breaktext(title, page, font_size, indent, width_pageref):
        #returns list of lines to print for main text
        lines=[] #stores each line of text
        lines.append("") #add first line with empty string
        title=title.strip() #remove leading and trailing spaces
        words=title.split() #split into words
        line=0 #which line we are on
        for word in words: #iterate each word
            line_width =indent + fitz.getTextlength(text=lines[line] + word, fontsize=font_size)
            if line_width>page.rect.width-options['margin'] - width_pageref:
                #then we put this word onto newline
                lines.append("")
                line +=1
                lines[line]=word + " "
            else:
                #otherwise we just add to this line
                lines[line] +=word + " "
        return lines

    def add_page():
        #adds a page
        fmt = fitz.PaperRect("a4")
        new_doc.newPage(width=fmt.width, height=fmt.height)
        return new_doc[- 1]

    if isTOC(doc): delete_toc(doc,options, display,addHistory=False)

    toc = doc.getToC()

    total = len(toc)

    indent = options['margin']
    y = 10
    max_font_size = 20
    font_size = 25
    page = add_page()
    w=page.rect.width
    h=page.rect.height

    #The title
    ls = breaktext(options['title'], page, font_size, indent, 0)  # break long text into lines
    for l in ls:
        y+=1.2 * font_size
        page.insertText(point=(indent, y), text=l, fontsize=font_size) #the title
    page.drawLine(p1=(options['margin'], y + (0.2 * font_size)), p2=(w - options['margin'], y + (0.2 * font_size)),
                  color=(0, 0, 0))
    y += 10  # gap under contents line
    count = 0


    for t in toc:
        level = t[0]
        title = remove_square_brackets(t[1])
        pg = t[2]
        if level <= options['maxDepth']:
            #get page label
            if pg > -1:
                pg_label = display.doc[t[2] - 1].get_label()
            else:
                pg_label = 'n/a'  # bookmark doesn't point to valid page
            # Set font size and colour depending on level
            if level == 1:
                font_size = max_font_size
                colour = (0, 0, 1)
                indent = options['margin']
            else:
                font_size = max_font_size - (2 * level)
                colour = (0, 0, 0)
                indent = options['margin'] + 10 * level


            width_pageref = fitz.getTextlength(text=pg_label, fontsize=font_size)

            ls=breaktext(title,page,font_size, indent, width_pageref) #break long text into lines
            if (y + len(ls)*font_size) + (len(ls)-1)*(0.2*font_size) + options['margin'] > h:
                page= add_page()  # add page if needed
                y = options['margin']
            for l in ls:
                y += 1.2 * font_size
                page.insertText(point=(indent, y), text=l, fontsize=font_size, color=colour) #insert main text
                width_text = fitz.getTextlength(text=l, fontsize=font_size)

            page.drawLine(p1=(indent + width_text + 2, y - 0.25 * font_size * 1.2),
                          p2=(w - options['margin'] - width_pageref - 2, y - 0.25 * font_size * 1.2), color=colour,
                          dashes="[3] 0")
            page.insertText(point=((w - options['margin']) - width_pageref, y), text=pg_label, fontsize=font_size,
                            color=colour) #insert page label
            # add link
            stY=y-(len(ls)-1)*(1.2 * font_size)
            pg = t[2]-1
            if not pg == -1:
                l = {'kind': 1, 'from': fitz.Rect(indent, stY - 0.5 * font_size * 1.2, w - options['margin'], y),
                     type: 'goto', 'page': pg, 'nflink': True, 'zoom': 0.0}
                lnks.append({'pgNo': page.number, 'link':l})
        count += 1
        percentComplete = (float(count) / float(total)) * 100
        if int(percentComplete) % 10 == 0:
            if display: display.updateprogressBar(percentComplete)

    # add TOC labels
    _add_toc_label(new_doc)
    display.insertPages(new_doc,0)
    for l in lnks:
        l['link']['page']+=new_doc.pageCount
        doc[l['pgNo']].insertLink(l['link'])
    new_doc.close()
    display.readTree()
    if addHistory: display.adddocHistory({'code':'DOC_addtoc', 'options':options})
    if display: display.updatestatusBar('Finished TOC.')
    return True

def _add_toc_label(new_doc):
    labels = []
    labels.append({'startpage': 0, 'prefix': 'TOC_', 'style': 'r', 'firstpagenum': 1})
    new_doc.set_page_labels(labels)

def remove_toc_label(doc, no_pages):
    # remove toc_label and update the rest
    labels = doc.get_labels_rule_dict()
    new_labels = []
    for label in labels:
        if not label['prefix'][:3] == 'TOC':  # skip TOC label
            label['startpage'] = label['startpage'] - no_pages  # adjust
            new_labels.append(label)
    doc.set_page_labels(new_labels)


def add_toc_label(doc, no_pages):
    # adds toc label
    new_label = {'startpage': 0, 'prefix': 'TOC_', 'style': 'r', 'firstpagenum': 1}
    labels = doc.get_labels_rule_dict()
    # increment startpage all by no_pages
    if len(labels)==0: #if no labels create default one
        labels.append({'startpage': 0, 'prefix': '', 'style': 'D', 'firstpagenum': 1})
    for label in labels:
        label['startpage'] = label['startpage'] + no_pages
    labels.insert(0, new_label)
    doc.set_page_labels(labels)

