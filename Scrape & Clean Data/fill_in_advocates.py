#This script runs a series of functions to add advocates to the case_data dictionary who were missed in the first pass

import pandas as pd
from bs4 import BeautifulSoup
import re
from selenium import webdriver
import time 

justices = ["William O. Douglas", "Harry A. Blackmun","Thurgood Marshall","Warren E. Burger","William H. Rehnquist",
"Byron R. White","Potter Stewart","William J. Brennan, Jr.","Thurgood Marshall","Lewis F. Powell, Jr.","John Paul Stevens",
"Sandra Day O'Connor","Antonin Scalia","Anthony M. Kennedy","David H. Souter","Clarence Thomas","Ruth Bader Ginsburg",
"Stephen G. Breyer","John G. Roberts, Jr.","Samuel A. Alito, Jr.","Sonia Sotomayor","Elena Kagan","Neil Gorsuch"]

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

def clean_oyez(transcript_list):
    #Takes in list of transcripts, returns one combined transcript string
    cleaned_transcript = ""
    for transcript in transcript_list:
        #first_pass = (transcript.split("</iframe>",1)[1]) Oyez may have changed their code .. use auto now
        first_pass = (transcript.split("\'auto\')",1)[1])
        second_pass = (first_pass.split("The case is submitted.",1)[0])
        cleaned_transcript += second_pass
    return cleaned_transcript

#imports csv created by scrape_oyez.py and converts to dict
df = pd.read_csv('case_data.csv',encoding="utf-8")
case_data = {}
for index, row in df.iterrows():
    key = row[0]
    value = eval(row[1])
    case_data[key] = value
	

### Initial Cleaning ###


#Delete any keys with cleaned_oyez less than 2000 characters; tend to be bugged cases or just a few lines
no_transcript = []
for key, value in case_data.items():
    cleaned_oyez = clean_oyez(case_data[key]["transcripts"])
    if len(cleaned_oyez) < 2000:
        no_transcript.append(key)
for key in no_transcript: 
    del case_data[key]
print(f"Missing Transcripts Deleted: {len(no_transcript)}")

#Delete any keys where we found pet/respondent in both parties; to re-add later
missing_advocates = []
for key, value in case_data.items():
    missing_advocates.append(key)
to_remove = []
for key in missing_advocates:
    petitionerlist = case_data[key]["petitioners"]
    respondentlist = case_data[key]["respondents"]
    for pet in petitionerlist:
        for resp in respondentlist:
            if pet == resp:
                to_remove.append(key)
for key in set(to_remove):
    del case_data[key]
    missing_advocates = []
for key, value in case_data.items():
    missing_advocates.append(key)


### Main Functions to Fill-in Advocates ###


def fix_broken_names(key):
	#Fix broken petitioner/respondent names that have residual html characters hanging around
    for key, value in case_data.items():
        for indx,string in enumerate(case_data[key]["petitioners"]):
            if ">" in string:
                string1 = string.split(">")[1]
                case_data[key]["petitioners"][indx] = string1

        for indx,string in enumerate(case_data[key]["respondents"]):
            if ">" in string:
                string1 = string.split(">")[1]
                case_data[key]["respondents"][indx] = string1

def get_advocate_area(landing_page):
	# Locates advocate area of the landing page
    souped = BeautifulSoup(landing_source, 'html.parser')
    text = souped.get_text()
    advslice = None
    match = re.search("Facts of",text)
    if match:
        match = re.search('Advocates(.+)Facts of',text)
        if match:
            advslice = match.group(1)
    else:
        match = re.search('Advocates(.+)Sort:',text)
        if match:
            advslice = match.group(1)
    return advslice

def add_advocates(key,landing_source,advslice):
	#tries to deduce who is who based on words associated with petitioner and respondent
    petitioner = ["petition","appella"] 
    respondent = ["respond","appelle"]
    advocates = [match.group(3) for match in re.finditer(' href="advocates/([a-z].+?)(">)(.+?)</a>',landing_source)]
    for advocate in advocates:
        match = re.search(fr'  {advocate}(.+?)  ',advslice)
        if match:
            for pet in petitioner:
                if pet in match[1].lower():
                    if advocate not in case_data[key]["petitioners"] and advocate not in case_data[key]["respondents"]:
                        case_data[key]["petitioners"].append(advocate)
            for resp in respondent:
                if resp in match[1].lower():
                    if advocate not in case_data[key]["respondents"] and advocate not in case_data[key]["petitioners"]:
                        case_data[key]["respondents"].append(advocate)

def fix2advocates(key):
	#finds cases with two advocates on landing page and one is labeled; assumes advocate is the unlabeled one.
    landing_source = case_data[key]["landing_source"]
    petitioners = case_data[key]["petitioners"]
    respondents = case_data[key]["respondents"]
    matchlist = [match.group(3) for match in re.finditer(' href="advocates/([a-z].+?)(">)(.+?)</a>',landing_source)]
    if len(matchlist) == 2:
        if len(case_data[key]["respondents"]) + len(case_data[key]["petitioners"]) == 1:
            
            if len(petitioners) > 0:
                if petitioners[0] == matchlist[0]:
                    case_data[key]["respondents"].append(matchlist[1])
                if petitioners[0] == matchlist[1]:
                    case_data[key]["respondents"].append(matchlist[0])
                    
            if len(respondents) > 0:
                if respondents[0] == matchlist[0]:
                    case_data[key]["petitioners"].append(matchlist[1])
                if respondents[0] == matchlist[1]:
                    case_data[key]["petitioners"].append(matchlist[0])
                    

def find_advocates_transcript(key, cleaned_oyez,transcripts):
	#Tries to add missing advocates by looking in the in transcript based on spacing and number of times names appear
    matchlist = [match.group(1) for match in re.finditer('   ([A-Z].+?)  ',cleaned_oyez)]
    advocatelist = [item for item in matchlist if item not in justices]
    advocates = []
       
    for item in advocatelist:
        if advocatelist.count(item) > 5:
            if item not in advocates:
                advocates.append(item)

    if len(advocates) == 2:
        if len(case_data[key]["respondents"]) + len(case_data[key]["petitioners"]) < 2:
            if len(transcripts) == 1:
                petitionerslist = []
                respondentslist = []
                petitionerslist.append(advocates[0])
                respondentslist.append(advocates[1])
                case_data[key]["petitioners"] = petitionerslist
                case_data[key]["respondents"] = respondentslist
    return advocates

def add_first_speaker(advocates, landing_source,transcripts):
	#Takes the first advocate who argues in the transcript and makes them a petitioner if they aren't already
    pageadvocates = [match.group(3) for match in re.finditer(' href="advocates/([a-z].+?)(">)(.+?)</a>',landing_source)]
    if len(pageadvocates) != len(case_data[key]["respondents"]) + len(case_data[key]["petitioners"]):
        if len(transcripts) == 1:
            if advocates:
                if advocates[0] not in case_data[key]["petitioners"] and advocates[0] not in case_data[key]["respondents"]:
                    case_data[key]["petitioners"].append(advocates[0])
        

### Main Loop To Fix Advocates ###   


for key in missing_advocates:
    landing_source = case_data[key]["landing_source"]
    cleaned_oyez=clean_oyez(case_data[key]["transcripts"])
    transcripts = case_data[key]["transcripts"]
    fix_broken_names(key) #Start by fixing broken names
    
    advslice = get_advocate_area(landing_source) #Grabs area where advocate info is on landing page
    if advslice:
        add_advocates(key,landing_source,advslice) #If we found advocate area, adds that info
        
    fix2advocates(key) #If there's two advocates and we found another one, assumes other is the remaining one.
    advocates = find_advocates_transcript(key, cleaned_oyez,transcripts) #Runs catchall to grab from transcript if can't find elsewhere
    add_first_speaker(advocates,landing_source,transcripts) #Finally, makes first advocate a petitioner if not already
    
    ## Removes any duplicate advocates from the process
    petitionerlist = case_data[key]["petitioners"]
    respondentlist = case_data[key]["respondents"]
    case_data[key]["petitioners"] = list(set(petitionerlist))
    case_data[key]["respondents"] = list(set(respondentlist))


#Prints final count of missing stuff

def find_complete_dockets(case_data):
    complete_docket_list=[]
    missing_pet = []
    missing_resp = []
    missing_adv = []
    
    for key, value in case_data.items():
        if len(case_data[key]["petitioners"]) == 0:
            missing_pet.append(key)
        elif len(case_data[key]["respondents"]) == 0:
            missing_resp.append(key)
        else:
            complete_docket_list.append(key)
        if len(case_data[key]["petitioners"]) == 0 or len(case_data[key]["respondents"]) == 0:
            missing_adv.append(key)

    return complete_docket_list, missing_pet, missing_resp, missing_adv
	
complete_docket_list, missing_pet, missing_resp, missing_adv = find_complete_dockets(case_data)
print(f"Full dockets: {len(complete_docket_list)}")
print(f"Missing Petitioners: {len(missing_pet)}")
print(f"Missing Respondents: {len(missing_resp)}")
print(f"Missing Advocates: {len(missing_adv)}")


### Additional Cleaning ###


#Removes empty advocate strings
for key, value in case_data.items():
    newpet = []
    newresp = []
    petitionerlist = case_data[key]["petitioners"]
    respondentlist = case_data[key]["respondents"]
    
    for petitioner in petitionerlist:
        if len(petitioner) > 5:
            newpet.append(petitioner)
    for respondent in respondentlist:
        if len(respondent) > 5:
            newresp.append(respondent)
            
    case_data[key]["petitioners"] = newpet
    case_data[key]["respondents"] = newresp
	
#Removes cases where 1 or fewer justices is talking (tend to be bugged from Oyez)
badjusticelist = []
for key, value in case_data.items():

    justicespresent = []
    transcript_list = case_data[key]["transcripts"]
    cleaned_oyez = clean_oyez(transcript_list)

    for justice in justices:
        if justice in cleaned_oyez:
            justicespresent.append(justice)
            
    if len(justicespresent) < 2:
        badjusticelist.append(key)

for key in badjusticelist:
    del case_data[key]
	
#Saves updated dictionary with fixes advocates
import csv
w = csv.writer(open("case_data.csv", "w", encoding="utf-8"))
for key, val in case_data.items():
    w.writerow([key, val])
len(case_data)