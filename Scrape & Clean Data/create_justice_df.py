## Creates CSVs for each justice with the questions each justice asked at each case
import pandas as pd
import re
import numpy as np
import statistics

justices = ["William H. Rehnquist","John Paul Stevens",
"Sandra Day O'Connor","Antonin Scalia","Anthony M. Kennedy","David H. Souter","Clarence Thomas","Ruth Bader Ginsburg",
"Stephen G. Breyer","John G. Roberts, Jr.","Samuel A. Alito, Jr.","Sonia Sotomayor","Elena Kagan","Neil Gorsuch"]


#Creates a series of lists of all the justices with one justice withheld from each list so we can remove the other justice questions
remaining = []
for justice in justices:
    holdouts = [j for j in justices if j != justice]
    remaining.append(holdouts)   


def get_one_justice(advocate_string,advocate_list,justices):
	#This function treats the remainining justices as 'advocates' and removes their questions
    justice_index = [match.span(0)[0] for justice in justices for match in re.finditer(justice, str(advocate_string))]
    advocate_index = [match.span(0)[0] for advocate in advocate_list for match in re.finditer(advocate, str(advocate_string))]
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
                break

    justice_string = ""
    for i,justice in enumerate(justice_indx): #Grabs strings from between justice talk until advocate starts responding.
        justice_speaking_string = advocate_string[justice_indx[i]:advocate_indx[i]] 
        justice_string += justice_speaking_string
    return justice_string


#imports justice DF, runs get_one_justice to split each justice off into their own questions, saves DF of the split questions.
df = pd.read_csv('justice_combo.csv',header=0, encoding="utf-8") #This file is created by create_main_df.py
data = []
for indx,row in df.iterrows():
    pstring = df.iloc[indx][2]
    rstring = df.iloc[indx][3]
    docket = df.iloc[indx][0]

    for i,justice in enumerate(justices):
        justiceP = get_one_justice(pstring,remaining[i],[justices[i]])
        justiceR = get_one_justice(rstring,remaining[i],[justices[i]])

        if len(justiceP) or len(justiceR) > 0:
            data.append([docket,justice,justiceP,justiceR])
        
df_questions = pd.DataFrame(data)
colnames = ["docket","justiceName","petitioner_questions","respondent_questions"]
df_questions.columns = colnames
df_questions.to_csv("indvJQuestions.csv", index=False)
df_votes = pd.read_csv("justiceVotes.csv", encoding="utf-8") #Reads in justice vote information from SCDB

#Merges the two DF to match votes to justice questions
df_votes_nodupes = df_votes.drop_duplicates()
df_questions_nodupes = df_questions.drop_duplicates()
df3 = pd.merge(df_questions_nodupes, df_votes_nodupes, on=['docket','justiceName'], how ="left")
df3 = df3.sort_values(by="docket")
df3 = df3.fillna(value="NO QUESTIONS")
df3 = df3.loc[df3["petVote"] != "NO QUESTIONS"]
df3=df3.drop_duplicates()


#Main loop to split off justices to separate DF and report summary statistics

for justice in justices:
    data = []
    lengthspet = []
    lengthsresp = []
    totint = []
    justiceDF = df3.loc[df3['justiceName'] == justice]

    for indx,row in justiceDF.iterrows():
        petQ = row["petitioner_questions"]
        respQ = row["respondent_questions"]
        petVote = int(row["petVote"])
        docket = row["docket"]
        if petVote == 1:
            respVote = 0
        elif petVote == 0:
            respVote = 1
        data.append([petVote,petQ,docket])
        data.append([respVote,respQ,docket])
        
        #Gets wordcounts
        wordspet = petQ.split()
        wordsresp = respQ.split()
        lengthspet.append(len(wordspet))
        lengthsresp.append(len(wordsresp))
        wordstot = wordspet+wordsresp
		#gets interruptions
        totint.append(wordstot.count("INTERRUPTING"))
		#gets means
        meantot = (statistics.mean(lengthspet+lengthsresp)*2)
        meanint = statistics.mean(totint)

        
    justiceDF1 = pd.DataFrame(data)
    justiceDF1.to_csv(f"{justice}_questions.csv", sep=',',header=False, index=False, encoding = "utf-8")
    print(f"{justice} # of cases: {len(justiceDF1)}; avg words: {meantot}, total interruptions: {meanint}")