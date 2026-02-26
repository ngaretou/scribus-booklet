# Scribus RS/AS booklet format

A process that allows you to quickly lay out an RS/AS booklet intended for just-in-time local production of scripture portions or a chronological presentation set. 

#### Depends on the free *Scribus* software, get it here: http://scribus.net for Windows, macOS & Linux

<p align="center">
  <img src="https://github.com/ngaretou/scribus-booklet/blob/main/examples/printout.jpg">
  <br>
  <i>booklets printed on pastel paper showing AS and RS script</i>
</p>

<p align="center">
  <a href="https://fdn.al/gallery/booklet-training.html"><img src="https://fdn.al/gallery/booklet-training.png"></a>
  <br>
  <i>training video</i>
</p>

## Process highlights
* Get fonts - Charis 7.0 and Harmattan 4.4 from https://software.sil.org/fonts/ 
* Download the Scribus 20-page template and the usfmConversion.py python script here: https://github.com/ngaretou/scribus-booklet/archive/refs/heads/main.zip 
* Use SFM formatted Paratext files, either open in a text editor or in Paratext in View/Unformatted
* Open Scribus and the template file and Save As a new project
* Page 1 is Roman script - Select All and delete what is there, and paste a chapter of USFM text
* Select All again and clear formatting with the recycle bin button next to the Paragraph and Character formatting dropdowns in Window/Content Properties
* Script/Execute Script and select the python script 
  * Choose the Yes for Arabic script and No for Roman script
  * On subsequent runs, you can choose it from Script/Recent Scripts
* The styles in effect in the document will be applied to the text based on USFM styles
  * Change styles as necessary (Edit/Styles) to acheive the desired styling
  * Save your style changes by creating a new template file via Save As when you are done and before you delete pages *or* import styles via Edit/Styles/Import from another file
* This is a minimalist conversion so glossary and footnote markers are deleted. 
* Change the title and chapter number as well as copyright info (vertical text box on page 2)
* Begin to fine-tune the format
  * Adjust the Manual Tracking of paragraphs via Content Properties/Advanced Settings to increase or decrease paragraphs by one line to make text fill the page
  * Make sure that the final page count is a multiple of four for printing. 
  * Styles are your superpower: 
    * The current styles of the template are set so that the text falls on the baseline grid. 
    * If you adjust, simply keep in mind the leading in the default style. 
    * For RS, currently 12 point font on 14 point font
    * For AS, currently 22 on 26.9. 
    * Examples: 
      * If you look at s1AS, you will see it's 22 on 26.9 pt leading with an extra 26.9 spacing below (then adjusted down with Baseline Offset), which makes two lines even lines - that way the lines continue to fall in the right place. 
      * The mrAS style is 20 on 26.9 - smaller text, same leading. So the space is preserved. 
        * It's then moved up 10% via Baseline Offset to be closer to msAS, but that doesn't change the spacing. 
  * Guides are for RS lines - Baseline Grid for AS lines
    * To turn on and off guides (for working with RS), go to View > Guides > Show Guides
    * To turn on and off Baseline Grid (for working with AS), go to View > Text Frames > Baseline Grid
  * You can move text boxes around and add decorative designs from pixabay.com - search for Arabic dividers - to make it come out evenly
* Delete unneeded pages via Page/Delete when done to get to multiple of four pages
* Export to PDF
* Run through an imposition process that readies the file for print. *PDFDroplet* recommended for Windows https://software.sil.org/pdfdroplet/ - for macOS and Linux use https://online2pdf.com/en/create-a-booklet 
* Also: 
  * Double check the copyright statment
  * Triple check you changed *both* titles
  * You could just use this same doc to make a monolingual booklet
  * Preview mode: View/Preview/Preview mode
  * Hand tool: click in the empty space, press space and release, and you have the grabby hand tool - press space again to go back to normal
