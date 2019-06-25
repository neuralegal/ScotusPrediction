#This file takes in the dict from case_data.csv and outputs the dataframe to train the model
import re
import pandas as pd

justices = ["William O. Douglas", "Harry A. Blackmun","Thurgood Marshall","Warren E. Burger","William H. Rehnquist",
"Byron R. White","Potter Stewart","William J. Brennan, Jr.","Thurgood Marshall","Lewis F. Powell, Jr.","John Paul Stevens",
"Sandra Day O'Connor","Antonin Scalia","Anthony M. Kennedy","David H. Souter","Clarence Thomas","Ruth Bader Ginsburg",
"Stephen G. Breyer","John G. Roberts, Jr.","Samuel A. Alito, Jr.","Sonia Sotomayor","Elena Kagan","Neil Gorsuch"]

#imports csv and converts to dict
df = pd.read_csv('case_data.csv',encoding="utf-8")
case_data = {}

for index, row in df.iterrows():
	value = eval(row[1])
	key = row[0]
	case_data[key] = value
	

### Main Functions ###

def clean_oyez(transcript_list):
	#Takes in list of transcripts, returns one combined transcript string
	cleaned_transcript = ""
	for transcript in transcript_list:
		try: 
			first_pass = (transcript.split("</iframe>",1)[1])
		except:
			first_pass = (transcript.split("analytics.js",1)[1])
		second_pass = (first_pass.split("The case is submitted.",1)[0])
		cleaned_transcript += second_pass
	return cleaned_transcript

def find_missing_advocates(cleaned_oyez,landing_source,advocatelist,opposinglist):
#We need to figure out which advocates weren't accounted for and remove questions directed towards them
#This function is called by get_advocate_strings and returns unaccounted for advocates
	#Grabs advocates from transcripts
	matchlist = [match.group(1) for match in re.finditer('	 ([A-Z].+?)	 ',cleaned_oyez)]
	advocatelist = [item for item in matchlist if item not in justices]
	advocates = list(set([item for item in advocatelist if advocatelist.count(item) > 5]))
	#Grabs advocates from landing page
	landinglist = [match.group(3) for match in re.finditer(' href="advocates/([a-z].+?)(">)(.+?)</a>',landing_source)]
	#combines them
	combolist = list(set(advocates + landinglist))
	found_advocates = advocatelist+opposinglist
	missing_advocates = [advocate for advocate in combolist if advocate not in found_advocates]
	return missing_advocates

def get_advocate_indexes(advocatelist,opposinglist, missing_advocates):
#Takes in petitioner and respondent's names and locates when they start and stop in the transcript; this function is called by
#get_advocate_strings to provide the indexes where each party starts and stops speaking.
	opposinglist = opposinglist + missing_advocates
	adv_index_list = [match.span(0)[0] for a in advocatelist for match in re.finditer(a, cleaned_oyez)]
	opp_index_list = [match.span(0)[0] for o in opposinglist for match in re.finditer(o, cleaned_oyez)]
	adv_index_list.sort()
	opp_index_list.sort()

	adv_indx = []
	opp_indx = []
	for adv in adv_index_list:
		for opp in opp_index_list:
			if opp > adv: #Finds where respondent starts speaking again after petitioner finishes
				if opp not in opp_indx:
					adv_indx.append(adv)
					opp_indx.append(opp)
				break

	#Grabs 'til the end if this party is last one speaking
	if len(adv_index_list) > 0 and len(opp_index_list) > 0:
		if max(adv_index_list) > max(opp_index_list):
			adv_indx.append(max(opp_index_list))
			opp_indx.append(len(cleaned_oyez))
	
	return adv_indx, opp_indx

def get_advocate_strings(cleaned_oyez, landing_source, advocatelist, opposinglist):
#Slices up doc so we have only questions directed to one party or the other; calls the above two functions.

	missing_advocates = find_missing_advocates(cleaned_oyez, landing_source, advocatelist, opposinglist)
	adv_indx, opp_indx = get_advocate_indexes(advocatelist,opposinglist,missing_advocates)

	advocate_string = ""
	for i,advocate in enumerate(adv_indx): #Grabs all strings from after advocate talks until other party starts
		advocate_speaking_string = cleaned_oyez[adv_indx[i]:opp_indx[i]] 
		advocate_string += advocate_speaking_string
	
	return advocate_string

def get_questions(advocate_string,advocate_list):
	#Finds where justices and advocates speak, returns just the justices speaking
	justice_index = [match.span(0)[0] for justice in justices for match in re.finditer(justice, advocate_string)]
	advocate_index = [match.span(0)[0] for advocate in advocate_list for match in re.finditer(advocate, advocate_string)]
	justice_index.sort()
	advocate_index.sort()

	justice_indx = []
	advocate_indx = []
	for justice in justice_index:
		for advocate in advocate_index:
			if advocate > justice: #Finds where advocate starts speaking again after a justice talks
				if advocate not in advocate_indx:
					justice_indx.append(justice)
					advocate_indx.append(advocate)
				break #Stops after we have the first instance of the justice speaking after the party.
	
	justice_string = ""
	for i,justice in enumerate(justice_indx): #Grabs strings from between justice talk until advocate starts responding.
		justice_speaking_string = advocate_string[justice_indx[i]:advocate_indx[i]] 
		if "--" in advocate_string[justice_indx[i]-8:justice_indx[i]]:
			justice_speaking_string = "INTERRUPTING " + justice_speaking_string #Adds note if text indicates interruption.
		justice_string += justice_speaking_string
		
	return justice_string

def createDF(data, questions_petitioner,questions_respondent,key):
	#Matches each case text with whether petitioner won or lost as class label
	
	if len(questions_petitioner) == 0:
		questions_petitioner = "NO QUESTIONS"
	if len(questions_respondent) == 0:
		questions_respondent = "NO QUESTIONS"
		
	if len(key) < 5: #Adds X so trailing spaces don't get confused with other cases
		key = ''.join((key,'XXX'))
	elif len(key) < 6:
		key = ''.join((key,'XX'))
	elif len(key) < 7:
		key = ''.join((key,'X'))
		
	outcomes = pd.read_csv("outcomes.csv", encoding = "utf-8")
	no_match = key
	
	for index, docket in enumerate(outcomes["docket"]): 
		docket = str(docket)
		if key == docket:
			no_match = 0
			win = outcomes.iloc[index:,2] #grabs the winning variable from index of this docket
			outcome = int(win.values[0])
			data.append([outcome,questions_petitioner, docket])
			
			#Switches wins to losses for respondent
			if outcome == 1:
				outcome = 0 
			elif outcome == 0:
				outcome = 1
			data.append([outcome,questions_respondent, docket])	 
			
	return data, no_match

def createDFCOLUMN(data, questions_petitioner,questions_respondent,key):
    #Same as createDF except keeps petitioner and respondent questions on the same line for easier splitting to create justice dataframes
    
    if len(key) < 5: #Adds X so trailing spaces don't get confused with other cases
        key = ''.join((key,'XXX'))
    elif len(key) < 6:
        key = ''.join((key,'XX'))
    elif len(key) < 7:
        key = ''.join((key,'X'))
        
    outcomes = pd.read_csv("outcomes.csv", encoding = "utf-8")
    for index, docket in enumerate(outcomes["docket"]): 
        docket = str(docket)
        if key == docket:
            win = outcomes.iloc[index:,2] #grabs the winning variable from index of this docket
            outcome = int(win.values[0])
            data.append([docket,outcome,questions_petitioner,questions_respondent])
    return data
	
### Main Loop ###

data = []
data2 = []
noadvocates = []
noQ = []
no_match_list = []
for key, value in case_data.items():

	transcript_list = case_data[key]["transcripts"]
	petitionerlist = case_data[key]["petitioners"]
	respondentlist = case_data[key]["respondents"]
	landing_source = case_data[key]['landing_source']
	cleaned_oyez = clean_oyez(transcript_list)

	if len(petitionerlist) > 0 and len(respondentlist) > 0: #only gets files with petitioners and respondents identifeid
		petitionerstring = get_advocate_strings(cleaned_oyez, landing_source, petitionerlist, respondentlist)
		respondentstring = get_advocate_strings(cleaned_oyez, landing_source, respondentlist, petitionerlist)
		petitionerQ = get_questions(petitionerstring,petitionerlist)
		respondentQ = get_questions(respondentstring,respondentlist)
		if len(petitionerQ) > 100 or len(respondentQ) > 100: #only gets files if questions to at least one party are identified
			data,no_match = createDF(data,petitionerQ,respondentQ,key) #Adds files to DF to match to win/loss
			data2 = createDFCOLUMN(data2,petitionerQ,respondentQ,key) #Adds files to DF on shared column for pet/resp

			no_match_list.append(no_match)
		else:
			noQ.append(key)
	else: 
		noadvocates.append(key) #If advocates weren't in transcript, adds to list

df = pd.DataFrame(data)
df = df.sort_values(by = 2)
df2 = pd.DataFrame(data2)
df.to_csv("train_language_model.csv",index = False)
no_match = [i for i in no_match_list if i != 0]
print(f"Total Cases: {len(case_data)}, Missing Questions: {len(noQ)}, Missing Advocates: {len(noadvocates)}, No Match: {len(no_match)}")
 
## Slices DF to match KKS Dataset

start = "04-1067"
end = "14-86XX"

for i, row in df.iterrows():
	#finds rows to begin and end
	if df.iloc[i,2] == start:
		slice1 = i
	if df.iloc[i,2] == end:
		slice2 = i

KKS = df.iloc[slice1-1:slice2+1]
KKS.to_csv("KKS.csv",index = False, header = None)


## Slices DF to create Justice Dataset


start = "02-1580"
end = "17-333X"

for i, row in df2.iterrows():
	#finds rows to begin and end
	if df2.iloc[i,0] == start:
		slice1 = i
	if df2.iloc[i,0] == end:
		slice2 = i

justice_df = df2.iloc[slice1-2:slice2+2]
justice_df.to_csv("justice_combo.csv",index = False, header = None)


