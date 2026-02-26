# RS/AS booklet format

A process that allows you to quickly lay out an RS/AS booklet intended for just-in-time local production of scripture portions or a chronological presentation set. 

#### Depends on the free *Scribus* software, get it here: http://scribus.net for Windows, macOS & Linux

## Process highlights
* Download the Scribus 20 page template and the usfmConversion.py python script
* Use SFM formatted Paratext files, either open in a text editor or in Paratext in View/Unformatted
* Open Scribus and the template file
* Page 1 is Roman script - Select All and delete what is there, and paste a chapter of USFM text
* Select All again and clear formatting with the recycle bin button next to the Paragraph and Character formatting dropdowns in Window/Content Properties
* Script/Execute Script and select the python script
  * On subsequent runs, you can choose it from Script/Recent Scripts
* The styles in effect in the document will be applied to the text based on USFM styles
* This is a minimalist conversion so glossary and footnote markers are deleted. 
* Change the title and chapter number as well as copyright info (vertical text box on page 2)
* Begin to fine-tune the format
  * Adjust the Manual Tracking of paragraphs to increase or decrease paragraphs by one line to make text fill the page
  * Make sure that the final page count is a multiple of four for printing. 
  * You can move text boxes around and add decorative designs from pixabay.com to make it come out evenly
* Delete unneeded pages via Page Delete when done
* Export to PDF
* Run through an imposition process that readies the file for print. *PDFDroplet* recommended for Windows https://software.sil.org/pdfdroplet/ - for macOS and Linux use https://online2pdf.com/en/create-a-booklet 

