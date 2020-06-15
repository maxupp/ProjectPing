# Project "Ping"

This is a Python script to periodically grab part of different websites and compare them to their previous state.
The intent is to detect changes like new results for a search on a classifieds page, or new instagram posts.

### Setup
Python-Requirements:

    * selenium
    * tqdm

It's recommended to create an Anaconda environment using the supplied `environmet.yml`.

Additional requirements:
 * Chrome installation
 * A version of chromedriver.exe corresponding to the installed chrome version
 
The path to `chromedriver.exe` has to be inserted into the system PATH variable. 
If no chromedriver is found the user will be prompted to insert the path to the supplied `chromedriver.exe`.
The supplied chromedriver corresponds to Chrome v83. Replace with correct version if necessary.  

### Usage

Insert any websites you want to observe into `pings.txt` with the following formatting:
~~~
https://www.ebay-kleinanzeigen.de/s-katzen/c136 | | //*[@id="srchrslt-adtable"]/li[1]
~~~
Each entry consists of three `|`-separated entries, which represent in order; 
    
    1. The URL of the observed site.
    2. A list of XPaths to be clicked before grabbing the content, separated by semicolons.
    3. The XPath to the element used for the actual comparison.
    
 