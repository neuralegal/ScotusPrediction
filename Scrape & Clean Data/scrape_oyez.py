import re
from selenium import webdriver
from bs4 import BeautifulSoup
import time 
import csv

#Path will need to be adjusted
#Selenium 
path = "r'D:\Users\Ian\Legal"

### Part 1: Grabs the URLs for all the case landing pages ###
def get_source(url):
	#Since Oyez hides all its data use Selenium to automate chrome to open site and scrape from there.
	#Selenium requires downloading chromedriver.exe to match your webbrowser version
    options = webdriver.ChromeOptions()
    options.add_argument("headless")
    driver = webdriver.Chrome(r'D:\Users\Ian\Legal\chromedriver.exe', options=options)  
    driver.get(url);
    time.sleep(5)
    source = driver.page_source
    driver.quit()
    return source
	
def get_year_urls():
#makes a URL list on Oyez from 1970 to 2019

    year_urls = []
    for year in range(startyear,endyear):
        year_url = ("https://www.oyez.org/cases/" + str(year))
        year_urls.append(year_url)
    return year_urls
	
startyear = 1970
endyear = 2019
year_urls = get_year_urls()

def get_docket_list(year, source_year): 
    #Grabs the docket numbers list for a given year. Takes in the page source from a /year/ url on oyez.
    indexlist = []
    for match in re.finditer(f'cases/{year}/', source_year):
        indexlist.append(match.span(0)[1])

    cleaned_list = []
    for i in indexlist:
        item = (source_year[i:i+7])
        if "ori" not in item: #Removes all orig cases as they have incompatible formatting
            docket = []
            for letter in item:
				#Grabs only numbers and hyphens for consistency in docket formatting
                if letter.isnumeric():
                    docket.append(letter)
                if letter == "-":
                    docket.append(letter) 
            docket = "".join(docket)
            cleaned_list.append(docket)

    cleaned_list=list(set(cleaned_list)) #keeps only unique dockets
    return cleaned_list

big_urls = []
#Runs get_docket_list and get_source to create a list of landing URLS on Oyez; saves list to file
for year_url in year_urls:
    source_year = get_source(year_url)
    year = year_url[-4:]
    docket_list = get_docket_list(year, source_year)
    for docket in docket_list:
        big_urls.append(f"{year_url}/{docket}")
    
with open("big_urls.txt", "w") as f:
    for url in big_urls:
        f.write(f"{url}\n")

### Part 2: scrapes transcript URLs, and advocate names from case landing page list ###

#Gets the URLs of the transcripts from the landing page for each docket on Oyez. Note: this takes many hours to finish!
def get_transcript_urls(source):
    #Scrapes from the landing page the URL of the transcript
    text = "https://apps.oyez.org/player"

    #Scrapes transcript URLs
    indexlist = []
    transcript_urls = []
    for match in re.finditer(text, source):
        indexlist.append(match.span(0)[1])
    for index in indexlist:        
        urlslice = source[index:index+55]
        url = urlslice.split('" class')[0]
        url = text+url
        if "opinion" not in url:
            transcript_urls.append(url)

    return transcript_urls

def get_advocate_names(source):
	#regular expressions to locate petitioner/respondent names on landing page 
    petitioner = ["for the petition","for petition","for the appella","for appella","supporting petition",\
                 "supporting appella","on behalf of petition","on behalf of appella","on behalf of the petition",\
                  "on behalf of the appella"] 
    respondent = ["for the responden","for respond","for the appelle","for appelle","supporting respond",\
                 "supporting appelle","on behalf of respond","on behalf of appelle","on behalf of the respond",\
                  "on behalf of the appelle"]
            
    def advscrape(party):
        advindex = []
        advlist = []
        for adv in party:
            for match in re.finditer(adv, source.lower()):
                advindex.append(match.span(0)[1])

        for adv in advindex:
            advslice = source[adv-150:adv]
            advocate = re.search('">(.+?)</a>',advslice)
            if advocate:
                advocate = advocate.group(1)
                advlist.append(advocate)
    
        return advlist
    
    petitionerlist = advscrape(petitioner)
    respondentlist = advscrape(respondent)
    
    #If names aren't labeled but there are two advocates given, assumes first one is petitioner, second is respondent.
    if len(petitionerlist+respondentlist) == 0:
        missing_advocates = 'class="ng-binding" href="advocates/' 
        missing_adv_index = []
        for match in re.finditer(missing_advocates, source):
            missing_adv_index.append(match.span(0)[1])
        if len(missing_adv_index) == 2:
            advslice = source[missing_adv_index[0]:missing_adv_index[0]+55]
            petitioner = re.search('">(.+?)</a>',advslice)
            petitioner = petitioner.group(1)
            petitionerlist.append(petitioner)

            advslice = source[missing_adv_index[1]:missing_adv_index[1]+55]
            respondent = re.search('">(.+?)</a>',advslice)
            respondent = respondent.group(1)
            respondentlist.append(respondent)
        
    return petitionerlist,respondentlist

#Main loop to gather transcript URLS and advocates; puts them in dict case_data
for raw_url in big_urls:
    docket = raw_url[-9:].split("/")[1]
    transcript_url_source = get_source(raw_url)
    try:
        transcript_urls = get_transcript_urls(transcript_url_source)
        petitionerlist,respondentlist = get_advocate_names(transcript_url_source)
    except:
        print(f"{raw_url} error!")
    
    case_data[docket] = {}
    case_data[docket]["transcript_url"] = transcript_urls
    case_data[docket]["petitioners"] = petitionerlist
    case_data[docket]["respondents"] = respondentlist
    case_data[docket]["landing_source"] = transcript_url_source

### Part 3: Scrapes transcripts from the transcripts URLs in the dict. ####

def get_transcript(transcript_url):
    transcript_source = get_source(transcript_url)
    souped = BeautifulSoup(transcript_source, 'html.parser')
    raw_oyez = souped.get_text()
    return raw_oyez
	
for bigurl in big_urls:
    key = bigurl[-8:]
    transcripts = []
    for url in case_data[key]["transcript_url"]:
        transcripts.append(get_transcript(url))
        case_data[key]["transcripts"] = transcripts
		
### Saves finished dict to file ###

w = csv.writer(open('case_data.csv', "w", encoding="utf-8"))
for key, val in case_data.items():
    w.writerow([key, val])
    