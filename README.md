Ashita Users: Run [Thorny's TitleCheck addon](https://github.com/ThornyFFXI/TitleCheck) to generate a file of your missing titles.

Windower Users: Run [Kayte's Titles addon](https://github.com/kaytecat/FFXI-Addons/tree/main/titles) to generate a file of your missing titles.

Then simply:

1.) Copy/paste your missing titles between Line 15 and Line 209 (one title per line). 

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
![Here is an example of a generate HTML report](https://i.imgur.com/fAWYwNP.png)
