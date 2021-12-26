import fitz
from utilities import annot_name, verticestoQuads
import pyperclip3
import clipboard

suffix='select-highlight'

light_blue=(153 / 256, 204 / 256, 255 / 256)
yellow=(1,1,0)
red=(1,0,0)

class selectedAnnot():
	def __init__(self,pg, annotxref, quads, colour):
		self.pg=pg
		self.annotxref=annotxref
		self.quads=quads
		self.colour=colour


class Char():

	def __init__(self,char,point):
		self.char=char
		self.point=point #point on the canvas
	def rect(self):
		if self.char:
			return fitz.Rect(self.char['bbox'])
	def pgrect(self,display):
		if self.char:
			return display.convertpageRect(self.rect())
	def tl(self):
		if self.char:
			return self.rect().tl
	def tr(self):
		if self.char:
			return self.rect().tr
	def br(self):
		if self.char:
			return self.rect().br
	def bl(self):
		if self.char:
			return self.rect().bl
	def origin(self):
		if self.char:
			return fitz.Point(self.char['origin'])
	def charLR(self,display, point=None):
		if not point:
			point=display.convertcanvasPointtoPDFpoint(self.point)
		else:
			point=display.convertcanvasPointtoPDFpoint(point)
		if self.rect():
			midpointx=self.rect()[0]+0.5*self.rect().width
			if point[0]>midpointx:
				return 'r'
			else:
				return 'l'
		return None
	def letter(self):
		if self.char:
			return self.char['c']


class rubberBand():

	class point():
		def __init__(self, eventPoint):
			self.eventPoint=eventPoint
		def canvasPoint(self):
			return fitz.Point(self.canvasObject.canvasx(eventPoint.x),self.canvasObject.canvasy(eventPoint.y))
		def pdfPoint(self,page, canvas,imageID):
			# converts a fitz.point on the page to a point on the pixmap
			c = canvas.coords(imageid)  # gives TL of image

			xFactor = self.display.width / page.rect.width
			yFactor = self.display.height / page.rect.height
			rtnPoint = fitz.Point((point[0] - c[0]) / xFactor, (point[1] - c[1]) / yFactor)
			return rtnPoint

	def getRect(self):
		return self.rect

	def mouseDown(self, event):
		# canvas x and y take the screen coords from the event and translate
		# them into the coordinate system of the canvas object
		if not self.display.doc: return

		page = self.display.doc[self.display.cur_page]

		self.canvasObject.focus_set()

		self.deleteRubberBand()

		self.startPoint=fitz.Point(self.canvasObject.canvasx(event.x),self.canvasObject.canvasy(event.y))

		lnk=page.link_clicked(self.display.convertcanvasPointtoPDFpoint(self.startPoint))
		self.display.action_link(lnk)

		self.startChar=self.getchar(self.startPoint)

		self.selectTextMode=True if self.startChar else False

		#remove any selected areas
		page.removeSelection()

		#Deselect any select annots
		page.deselectAnnot()

		#Highlight any selected annots
		page.selectAnnot(self.display.convertcanvasPointtoPDFpoint(self.startPoint))

		self.display.refreshPage(self.display.cur_page)
#		print ("Clicked", self.rect,self.charLR)

	def Motion(self,event):
		if not self.display.doc: return
		page=self.display.doc[self.display.cur_page]
		point=fitz.Point(self.canvasObject.canvasx(event.x),self.canvasObject.canvasy(event.y))
		point=self.display.convertcanvasPointtoPDFpoint(point)
		if page.inTextArea(point):
			self.overText=True
			self.canvasObject.config(cursor='left_side')
		else:
			self.overText=False
			self.canvasObject.config(cursor='cross')
		if page.isAnnotArea(point):
			self.overAnnot=True
			self.canvasObject.config(cursor='arrow')

	def dblClick(self,event):
		#double-click
		if not self.display.doc: return
		page=self.display.doc[self.display.cur_page]
		point=fitz.Point(self.canvasObject.canvasx(event.x),self.canvasObject.canvasy(event.y))
		point=self.display.convertcanvasPointtoPDFpoint(point)
		w=page.selectWord(point)
		if w:
			print(w)
			self.display.refreshPage()

	def getchar(self,event):
		#returns char rect at event.x,event.y and if the point is to the left or right of char
		point = self.display.convertcanvasPointtoPDFpoint(fitz.Point(self.canvasObject.canvasx(event.x), self.canvasObject.canvasy(event.y)))
		if self.display.doc:
			page=self.display.doc[self.display.cur_page]
			char=page.getchar(point)
			if char: return Char(char,event)
		return None

	def createCursor(self):
		if self.startChar:
			if self.cursorOn and self.startChar.charLR(self.display):
				if self.startChar.charLR(self.display)=='l':
					self.cursor=self.canvasObject.create_line(self.startChar.pgrect(self.display)[0],self.startChar.pgrect(self.display)[1],self.startChar.pgrect(self.display)[0],self.startChar.pgrect(self.display)[3])
				elif self.startChar.charLR(self.display)=='r':
					self.cursor=self.canvasObject.create_line(self.startChar.pgrect(self.display)[2],self.startChar.pgrect(self.display)[1],self.startChar.pgrect(self.display)[2],self.startChar.pgrect(self.display)[3])
			else:
				if self.cursor:
					self.canvasObject.delete(self.cursor)
		self.cursorOn=not self.cursorOn
		self.canvasObject.update_idletasks()
		self.canvasObject.after(400, self.createCursor)

	def bmouseMotion(self,event):
		#motion while the mouse is moving and button pressed
		if not self.display.doc: return
		point=fitz.Point(self.canvasObject.canvasx(event.x),self.canvasObject.canvasy(event.y))
		self.endChar=self.getchar(point)
#		print(self.endChar.letter())
		self.endPoint=fitz.Point(self.canvasObject.canvasx(event.x),self.canvasObject.canvasy(event.y))
		if self.selectTextMode==True:
			self.select(event)
		else:
			self.mouseMotion(event)

	def mouseMotion(self, event):
		#movement while shift is down
		# canvas x and y take the screen coords from the event and translate
		# them into the coordinate system of the canvas object
		if not self.display.doc: return
		if (self.startPoint.x != event.x)  and (self.startPoint.y != event.y) :
			self.canvasObject.delete(self.rubberbandBox)
			self.rect=fitz.Rect(self.startPoint, self.endPoint)
			self.rubberbandBox = self.canvasObject.create_rectangle(self.rect[:4])
			self.canvasObject.update_idletasks()

	def furthestBR(self, pointA, pointB):
		#returns the point furthest south east
		if not pointA: return pointB
		if not pointB: return pointA
		if not pointA and not pointB: return None
		if pointB.x>pointA.x and pointB.y>pointA.y:
			return pointB
		return pointA

	def furthestTL(self, pointA, pointB):
		#returns the point furthest south east
		if not pointA: return pointB
		if not pointB: return pointA
		if not pointA and not pointB: return None
		if pointB.x<pointA.x and pointB.y<pointA.y:
			return pointB
		return pointA

	def swapPoints(self,startPoint,endPoint,startChar,endChar):
		#which is first in order?
		if not startPoint or not endPoint:
			return startPoint, endPoint, startChar, endChar
		if startPoint.y<endPoint.y:
			#startChar is first
			return startPoint,endPoint, startChar, endChar
		if startPoint.y>endPoint.y:
			#endChar is first
			return endPoint,startPoint, endChar, startChar
		if startPoint.y==endPoint.y:
			#on same line
			if startPoint.x<endPoint.x:
				#startChar is first
				return startPoint, endPoint, startChar, endChar
		return endPoint, startPoint, endChar, startChar


	def select(self, event):
		#selects the text between startChar.tl and endChar.br or endPoint if further south east
		if not self.startChar or not self.display.doc: return

		startPoint, endPoint, startChar, endChar=self.swapPoints(self.startPoint,self.endPoint, self.startChar, self.endChar)

		if endChar:
			if endChar.charLR(self.display,endPoint)=="r":
				end=self.furthestBR(endChar.br(),self.display.convertcanvasPointtoPDFpoint(endPoint))
			else:
				end=self.furthestBR(endChar.bl(),self.display.convertcanvasPointtoPDFpoint(endPoint))
		else:
			end=self.display.convertcanvasPointtoPDFpoint(endPoint)

		if startChar:
			if startChar.charLR(self.display,startPoint)=="r":
				start=self.furthestTL(startChar.tr(),self.display.convertcanvasPointtoPDFpoint(startPoint))
			else:
				start=self.furthestTL(startChar.tl(),self.display.convertcanvasPointtoPDFpoint(startPoint))
		else:
			start=self.display.convertcanvasPointtoPDFpoint(startPoint)

		page=self.display.doc[self.display.cur_page]
		page.select(start,end)
		self.display.refreshPage(self.display.cur_page)

	def mouseUp(self, event):
		#self.canvasObject.delete(self.rubberbandBox)
		pass

	def deleteRubberBand(self):
		self.canvasObject.delete(self.rubberbandBox)
		self.rect=None

	def colourYellow(self,event):
		page=self.display.doc[self.display.cur_page]
		annotxref=page.highlightSelection()
		if annotxref:
			self.display.refreshPage(self.display.cur_page)
			annot=page.loadAnnot(annotxref)
			quads=verticestoQuads(annot.vertices)
			colour=annot.colors['stroke']
			self.display.adddocHistory({'code': "DOC_highlight", 'annot': selectedAnnot(self.display.cur_page, annotxref, quads, colour)})

	def leftArrow(self,event):
		self.display.decPg()

	def shiftleftArrow(self, event):
		self.display.dechistPg()

	def rightArrow(self, event):
		self.display.incPg()

	def shiftrightArrow(self, event):
		self.display.dechistPg()

	def deleteselectedannots(self,event):
		if not self.display.doc: return
		pg=self.display.cur_page
		page=self.display.doc[pg]
		annots=[]
		for annotxref in page.selectedAnnots:
			annot=page.loadAnnot(annotxref)
			quads=verticestoQuads(annot.vertices)
			colour=annot.colors['stroke']
			annots.append(selectedAnnot(pg,annotxref,quads,colour))
		self.display.adddocHistory({'code': "DOC_deletehighlight", 'annots': annots })
		page.removeSelectedAnnots()
		self.display.refreshPage(pg)


	def copySelection(self,event):
		page=self.display.doc[self.display.cur_page]
		txt=page.getselectedText()
		if not txt=="":
			pyperclip3.copy(txt)
			print(txt)
		txt=page.gettextselectedHighlights()
		if not txt == "":
			pyperclip3.copy(txt)
			print(txt)

	def __init__(self, canvas, display):
		self.display=display
		self.canvasObject=canvas

		self.startPoint=fitz.Point(0,0) #for storing first start point
		self.endPoint=fitz.Point(0,0) #for storing end point



		self.rect=None #to store rect of final band
		self.startChar=None #first selected character
		self.endChar=None #final selected character
		self.cursor=None #for cursor line
		self.cursorOn=True #for whether cursor is displayed
		self.createCursor() #display the cursor. Gets called very 400 ms

		self.overText=False

		self.selectTextMode=False

		# this is a "tagOrId" for the rectangle we draw on the canvas
		self.rubberbandBox = None

		# and the bindings that make it work..
		self.canvasObject.bind("<Button-1>", self.mouseDown)
#		self.canvasObject.bind("<Shift-Button-1>", self.mouseDown)
		self.canvasObject.bind ("<Shift-Button1-Motion>", self.mouseMotion)
		self.canvasObject.bind ("<Button1-Motion>", self.bmouseMotion)
		self.canvasObject.bind ("<Button1-ButtonRelease>", self.mouseUp)
		self.canvasObject.bind ("<Motion>", self.Motion)
		self.canvasObject.bind ("<Double-Button-1>", self.dblClick)

		self.canvasObject.bind('<F3>', self.colourYellow)
		self.canvasObject.bind('<Left>', self.leftArrow)
		self.canvasObject.bind('<Right>', self.rightArrow)
		self.canvasObject.bind('<Shift-Left>', self.shiftleftArrow)
		self.canvasObject.bind('<Shift-Right>', self.shiftrightArrow)
		self.canvasObject.bind('<Delete>', self.deleteselectedannots)
		self.canvasObject.bind('<BackSpace>', self.deleteselectedannots)
		self.canvasObject.bind('<Command-c>', self.copySelection)
		self.canvasObject.bind('<Control-c>', self.copySelection)

