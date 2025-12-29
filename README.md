Ashita Users: Run [Thorny's TitleCheck addon](https://github.com/ThornyFFXI/TitleCheck) to generate a file of your missing titles.

Windower Users: Run [Kayte's Titles addon](https://github.com/kaytecat/FFXI-Addons/tree/main/titles) to generate a file of your missing titles.

Then simply:

1.) Delete titles between Line 15 and 209, and Copy/paste YOUR missing titles there (one title per line). 

2.) Run `python titlereportgenerator.py`

3.) Open HTML file in Browser (or CSV file in notepad if you prefer)

Example output:
```
Wrote:
 - titles_filtered.csv
 - titles_filtered.html
```

Quest links are clickable and columns are sortable as well.
Row counts are generated on page load. (This is the total number of titles you are missing):

![Here is an example of a generate HTML report](https://i.imgur.com/b4kfRhC.png)

If you need additional installation help:

0.) Make sure you updated titlereportgenerator.py with only your missing titles.

1.) Download / install python: [https://www.python.org/downloads/release/python-3142/](https://www.python.org/downloads/release/python-3142/)

2.) Open an elevated command window: Start > Run > Type cmd > Right-click, select "Run as Administrator"

3.) Run these commands:

```
pip install requests
pip install pandas
pip install beautifulsoup
cd "Your directory titlereportgenerator.py"
python titlereportgenerator.py
```
4.) Open your titles_filtered.html in your browser of choice.
